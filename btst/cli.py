import argparse
import json
import logging
import time
from datetime import date, datetime
from zoneinfo import ZoneInfo

from .agents import Agents
from .config import Config
from .dhan_client import Dhan, DhanError
from .journal import Journal
from .risk import build_plan
from .screener import evaluate, with_today

IST = ZoneInfo("Asia/Kolkata")
log = logging.getLogger("btst")


def _mode(cfg: Config) -> str:
    return "live" if cfg.live_trading else "paper"


def _plan_path(cfg: Config, day: date):
    return cfg.data_dir / f"plan-{day}.json"


def cmd_scan(cfg: Config, args) -> None:
    dhan = Dhan(cfg.dhan_client_id, cfg.dhan_access_token, cfg.data_dir)
    journal = Journal(cfg.data_dir / "journal.db")
    symbols = [s.strip().upper() for s in cfg.universe_file.read_text().splitlines()
               if s.strip() and not s.startswith("#")]
    ids = dhan.security_ids(symbols)
    log.info("Fetching live quotes for %d stocks", len(ids))
    quotes = dhan.quotes(list(ids.values()))

    today = datetime.now(IST).date()
    candidates = []
    for symbol, sid in ids.items():
        quote = quotes.get(sid)
        if not quote:
            continue
        try:
            df = with_today(dhan.daily_history(sid), quote, today)
        except DhanError as e:
            log.warning("%s: history failed (%s)", symbol, e)
            continue
        finally:
            time.sleep(0.25)
        c = evaluate(symbol, sid, df, quote, cfg.min_turnover_cr)
        if c:
            candidates.append(c.to_dict())
    candidates.sort(key=lambda c: c["score"], reverse=True)
    shortlist = candidates[:args.top]
    log.info("Screener passed %d stocks; sending top %d to agents", len(candidates), len(shortlist))

    if not shortlist:
        print("No stocks passed the screener today.")
        return

    agents = Agents(cfg.claude_model)
    market = agents.market_context(dhan.index_snapshot())
    log.info("Market context: %s", market)
    reviews = agents.catalysts(shortlist)

    plans, notes = build_plan(
        shortlist, reviews, market,
        capital_per_trade=cfg.capital_per_trade, max_positions=cfg.max_positions,
        available_funds=dhan.available_funds() if cfg.live_trading else cfg.capital_per_trade * cfg.max_positions,
        stop_loss_pct=cfg.stop_loss_pct, target_pct=cfg.target_pct,
        realized_pnl_today=journal.realized_pnl(today), max_daily_loss=cfg.max_daily_loss,
    )
    output = {"date": str(today), "market": market, "shortlist": shortlist, "reviews": reviews,
              "notes": notes, "plans": [p.to_dict() for p in plans]}
    _plan_path(cfg, today).write_text(json.dumps(output, indent=2, default=str))

    print(f"\nMarket: {market['bias']}  new positions allowed: {market['allow_new_positions']}")
    for n in notes:
        print(f"  - {n}")
    print(f"\nBTST plan ({_mode(cfg)} mode):")
    for p in plans:
        print(f"  {p.symbol:<12} qty {p.qty:<5} buy<= {p.entry_limit:<9} SL {p.stop_loss:<9} "
              f"TGT {p.target:<9} score {p.final_score}\n      {p.reason}")
    if plans:
        print(f"\nReview, then run:  python -m btst buy")


def cmd_buy(cfg: Config, args) -> None:
    today = datetime.now(IST).date()
    path = _plan_path(cfg, today)
    if not path.exists():
        raise SystemExit("No plan for today. Run `python -m btst scan` first.")
    plans = json.loads(path.read_text())["plans"]
    if not plans:
        raise SystemExit("Today's plan has no trades.")

    mode = _mode(cfg)
    for p in plans:
        print(f"{p['symbol']:<12} BUY {p['qty']} @ {p['entry_limit']}  (SL {p['stop_loss']}, TGT {p['target']})")
    if not args.yes and input(f"\nPlace these {len(plans)} {mode.upper()} CNC orders? [y/N] ").strip().lower() != "y":
        print("Aborted.")
        return

    dhan = Dhan(cfg.dhan_client_id, cfg.dhan_access_token, cfg.data_dir) if cfg.live_trading else None
    journal = Journal(cfg.data_dir / "journal.db")
    for p in plans:
        order_id = None
        if dhan:
            order_id = dhan.place_order(p["security_id"], "BUY", p["qty"], p["entry_limit"], tag=f"btst-{today}")
        journal.record_buy(mode, p, order_id)
        print(f"{p['symbol']}: {'order ' + order_id if order_id else 'paper trade recorded'}")


def _resolve_fills(dhan: Dhan, journal: Journal, trades) -> list:
    live = []
    for t in trades:
        order = dhan.order_status(t["buy_order_id"])
        order = order[0] if isinstance(order, list) else order
        filled = int(order.get("filledQty") or 0)
        if filled == 0:
            journal.mark_unfilled(t["id"])
            print(f"{t['symbol']}: buy order was not filled, skipping")
            continue
        journal.update_fill(t["id"], filled, float(order.get("averageTradedPrice") or t["entry_price"]))
        live.append(t["id"])
    return live


def cmd_exit(cfg: Config, args) -> None:
    mode = _mode(cfg)
    journal = Journal(cfg.data_dir / "journal.db")
    dhan = Dhan(cfg.dhan_client_id, cfg.dhan_access_token, cfg.data_dir)
    today = datetime.now(IST).date()
    trades = journal.open_trades(mode, bought_before=today)
    if cfg.live_trading:
        keep = set(_resolve_fills(dhan, journal, trades))
        trades = [t for t in journal.open_trades(mode, bought_before=today) if t["id"] in keep]
    if not trades:
        print("No open BTST positions to exit.")
        return

    exit_h, exit_m = map(int, cfg.exit_by.split(":"))
    open_trades = {t["id"]: t for t in trades}
    print(f"Managing {len(open_trades)} {mode} positions until {cfg.exit_by} IST")

    while open_trades:
        now = datetime.now(IST)
        time_up = (now.hour, now.minute) >= (exit_h, exit_m)
        prices = dhan.ltp([t["security_id"] for t in open_trades.values()])
        for tid, t in list(open_trades.items()):
            ltp = prices.get(t["security_id"])
            if ltp is None:
                continue
            reason = ("STOP_LOSS" if ltp <= t["stop_loss"] else "TARGET" if ltp >= t["target"]
                      else "TIME_EXIT" if time_up else None)
            if not reason:
                continue
            order_id = None
            if cfg.live_trading:
                order_id = dhan.place_order(t["security_id"], "SELL", t["qty"], None, tag=f"btst-exit-{today}")
            journal.record_exit(tid, ltp, reason, order_id)
            print(f"{t['symbol']}: {reason} at ~{ltp} ({(ltp - t['entry_price']) * t['qty']:+.0f})")
            del open_trades[tid]
        if open_trades:
            time.sleep(args.poll)


def cmd_report(cfg: Config, args) -> None:
    journal = Journal(cfg.data_dir / "journal.db")
    rows = journal.summary()
    if not rows:
        print("No closed trades yet.")
    for r in rows:
        wins = r["wins"] or 0
        print(f"{r['mode']:<6} trades {r['trades']:<4} win-rate {100 * wins / r['trades']:.0f}%  P&L {r['pnl']}")


def main() -> None:
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
    parser = argparse.ArgumentParser(prog="btst", description="AI-assisted BTST trading on Dhan")
    sub = parser.add_subparsers(dest="command", required=True)
    scan = sub.add_parser("scan", help="Screen stocks, run AI agents, write today's plan (run ~3:00-3:15 PM)")
    scan.add_argument("--top", type=int, default=10, help="Candidates to send to the agents")
    buy = sub.add_parser("buy", help="Place today's planned CNC buys after confirmation (before 3:30 PM)")
    buy.add_argument("--yes", action="store_true", help="Skip the confirmation prompt")
    ext = sub.add_parser("exit", help="Next morning: manage SL/target/time exits (start at 9:15 AM)")
    ext.add_argument("--poll", type=int, default=15, help="Seconds between price checks")
    sub.add_parser("report", help="Journal P&L summary")

    args = parser.parse_args()
    cfg = Config.from_env()
    {"scan": cmd_scan, "buy": cmd_buy, "exit": cmd_exit, "report": cmd_report}[args.command](cfg, args)
