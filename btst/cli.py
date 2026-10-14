import argparse
import json
import logging
import time
from datetime import date, datetime, timedelta
from zoneinfo import ZoneInfo

from .config import Config
from .dhan_client import Dhan, DhanError
from .events import TYPES, Event, EventCalendar, filter_candidates, load_holidays
from .kite_quotes import normalize_kite_quotes
from .nse import NSE, sync_calendar
from . import review as rv
from .risk import build_plan, build_sell_ideas
from .screener import evaluate, mover_row, quote_screen, rank_movers, with_today

IST = ZoneInfo("Asia/Kolkata")
log = logging.getLogger("btst")


def _plan_path(cfg: Config, day: date):
    return cfg.data_dir / f"plan-{day}.json"


def _calendar(cfg: Config) -> EventCalendar:
    return EventCalendar(cfg.calendar_file, load_holidays(cfg.calendar_file.with_name("holidays.txt")))


def _universe(cfg: Config) -> list[str]:
    return [s.strip().upper() for s in cfg.universe_file.read_text().splitlines()
            if s.strip() and not s.startswith("#")]


def _sync(cfg: Config, calendar: EventCalendar, today: date, days: int = 45) -> int:
    added = sync_calendar(calendar, NSE(), set(_universe(cfg)), today, days)
    log.info("Calendar synced from NSE: %d events for %d stocks", added, len(_universe(cfg)))
    return added


def _synced_calendar(cfg: Config, today: date, no_sync: bool) -> EventCalendar:
    calendar = _calendar(cfg)
    if not no_sync:
        try:
            _sync(cfg, calendar, today)
        except Exception as e:
            log.warning("NSE calendar sync failed (%s); using the saved calendar", e)
    return calendar


def _shortlist_path(cfg: Config, day: date):
    return cfg.data_dir / f"shortlist-{day}.json"


def _write_shortlist(cfg: Config, day: date, mode: str, shortlist: list, losers: list, notes: list,
                     index_snapshot: dict, source: str = "dhan") -> None:
    """Hand-off file for the Claude Code subagents: screened stocks only, no LLM calls made."""
    doc = {"date": str(day), "mode": mode, "source": source, "shortlist": shortlist, "losers": losers,
           "notes": notes, "index_snapshot": index_snapshot}
    path = _shortlist_path(cfg, day)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(doc, indent=2, default=str))
    print(f"Screened {len(shortlist)} stocks" + (f" and {len(losers)} losers" if losers else "") + f" -> {path}")
    for n in notes:
        print(f"  - {n}")


def normalize_reviews(doc) -> dict[str, dict]:
    """Accept {"reviews": [..]}, a bare list, or a {symbol: review} map; return {symbol: review}."""
    rows = doc.get("reviews", doc) if isinstance(doc, dict) else doc
    if isinstance(rows, dict):
        rows = [dict(v, symbol=v.get("symbol", k)) for k, v in rows.items()]
    return {r["symbol"]: r for r in rows}


def cmd_kite_screen(cfg: Config, args) -> None:
    """Screen from a saved Kite MCP `get_quotes` response. Needs no Dhan or AI keys."""
    today = datetime.now(IST).date()
    universe = _universe(cfg)
    quotes, indices = normalize_kite_quotes(json.load(open(args.quotes)), set(universe))
    missing = [s for s in universe if s not in quotes]
    notes = []
    if missing:
        notes.append(f"{len(missing)} of {len(universe)} stocks missing from the Kite quotes: {', '.join(missing[:15])}"
                     + (" ..." if len(missing) > 15 else ""))
    if len(quotes) < len(universe) * 0.8:
        raise SystemExit(f"Only {len(quotes)} of {len(universe)} stocks in the quotes file; refusing to rank a partial list.\n"
                         + notes[0])
    rows = [r for sym, q in quotes.items() if (r := mover_row(sym, sym, q, cfg.min_turnover_cr))]
    calendar = _synced_calendar(cfg, today, args.no_sync)
    losers: list = []
    if args.mode == "movers":
        gainers, losers = rank_movers(rows, args.top)
        shortlist, cal_notes = filter_candidates(gainers, calendar, today, len(gainers))
        losers, loser_notes = filter_candidates(losers, calendar, today, len(losers))
        cal_notes += loser_notes
    else:
        shortlist, cal_notes = filter_candidates(quote_screen(rows), calendar, today, args.top)
    if not shortlist and not losers:
        print("No stocks passed the screen today.")
        for n in notes + cal_notes:
            print(f"  - {n}")
        return
    _write_shortlist(cfg, today, args.mode, shortlist, losers, notes + cal_notes, indices, source="kite")


def cmd_plan(cfg: Config, args) -> None:
    """Risk gate on subagent output: shortlist + market + reviews JSON -> plan file."""
    today = datetime.now(IST).date()
    doc = json.loads(_shortlist_path(cfg, today).read_text())
    market = json.loads(open(args.market).read())
    reviews = normalize_reviews(json.loads(open(args.reviews).read()))
    funds = cfg.capital_per_trade * cfg.max_positions
    plans, notes = build_plan(
        doc["shortlist"], reviews, market,
        capital_per_trade=cfg.capital_per_trade, max_positions=cfg.max_positions, available_funds=funds,
        stop_loss_pct=cfg.stop_loss_pct, target_pct=cfg.target_pct,
    )
    sells, sell_notes = build_sell_ideas(doc.get("losers", []), reviews, max_ideas=cfg.max_sell_ideas,
                                         stop_loss_pct=cfg.stop_loss_pct, target_pct=cfg.target_pct)
    notes = doc.get("notes", []) + notes + sell_notes
    output = {"date": str(today), "mode": doc["mode"], "source": doc.get("source", "dhan"), "market": market,
              "shortlist": doc["shortlist"],
              "reviews": reviews, "losers": doc.get("losers", []), "sell_ideas": [i.to_dict() for i in sells],
              "notes": notes, "plans": [p.to_dict() for p in plans]}
    _plan_path(cfg, today).write_text(json.dumps(output, indent=2, default=str))
    print(f"Market: {market.get('bias')}  new positions allowed: {market.get('allow_new_positions')}")
    for n in notes:
        print(f"  - {n}")
    print("\nBTST plan:")
    for pl in plans:
        print(f"  {pl.symbol:<12} qty {pl.qty:<5} buy<= {pl.entry_limit:<9} SL {pl.stop_loss:<9} "
              f"TGT {pl.target:<9} score {pl.final_score}\n      {pl.reason}")
    if not plans:
        print("  (no trades passed the risk gate)")
    if doc.get("losers"):
        _print_sell_ideas(sells, len(doc["losers"]))
    if plans:
        print("\nPlace these yourself as CNC limit orders. Not financial advice.")


def cmd_scan(cfg: Config, args) -> None:
    dhan = Dhan(cfg.dhan_client_id, cfg.dhan_access_token, cfg.data_dir)
    ids = dhan.security_ids(_universe(cfg))
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
    calendar = _synced_calendar(cfg, today, args.no_sync)
    shortlist, calendar_notes = filter_candidates(candidates, calendar, today, args.top)
    for c in shortlist:
        if not any(e.type == "results" and e.date >= today for e in calendar.between(today, today + timedelta(days=90), c["symbol"])):
            calendar_notes.append(f"{c['symbol']}: no results date on file - confirm it is not reporting tomorrow")
    log.info("Screener passed %d stocks; writing %d to the shortlist", len(candidates), len(shortlist))

    if not shortlist:
        print("No stocks passed the screener today.")
        for n in calendar_notes:
            print(f"  - {n}")
        return

    _write_shortlist(cfg, today, "scan", shortlist, [], calendar_notes, dhan.index_snapshot())


def _print_sell_ideas(sells: list, n_losers: int) -> None:
    print(f"\nSELL ideas from the top {n_losers} F&O losers (up to 10). Intraday or stock-futures only; "
          "this tool never places them and cash BTST cannot short overnight:")
    for i in sells:
        print(f"  {i.symbol:<12} sell<= {i.entry_limit:<9} stop {i.stop_loss:<9} target {i.target:<9} score {i.final_score}\n      {i.reason}")
    if not sells:
        print("  (none passed the review)")


def cmd_movers(cfg: Config, args) -> None:
    dhan = Dhan(cfg.dhan_client_id, cfg.dhan_access_token, cfg.data_dir)
    ids = dhan.security_ids(_universe(cfg))
    quotes = dhan.quotes(list(ids.values()))
    today = datetime.now(IST).date()

    rows = [r for sym, sid in ids.items() if sid in quotes
            and (r := mover_row(sym, sid, quotes[sid], cfg.min_turnover_cr))]
    gainers, losers = rank_movers(rows, args.top)
    calendar = _synced_calendar(cfg, today, args.no_sync)
    gainers, notes = filter_candidates(gainers, calendar, today, len(gainers))
    losers, loser_notes = filter_candidates(losers, calendar, today, len(losers))
    notes += loser_notes
    log.info("%d F&O stocks ranked; %d gainers and %d losers after the calendar check", len(rows), len(gainers), len(losers))
    if not gainers and not losers:
        print("No liquid F&O movers found.")
        return

    _write_shortlist(cfg, today, "movers", gainers, losers, notes, dhan.index_snapshot())


def cmd_calendar(cfg: Config, args) -> None:
    calendar = _calendar(cfg)
    today = datetime.now(IST).date()
    if args.action == "add":
        calendar.add(Event(args.symbol, args.type, date.fromisoformat(args.date), args.note, args.source))
        calendar.save()
        print(f"Saved {args.symbol.upper()} {args.type} on {args.date}")
    elif args.action == "import":
        import csv
        with open(args.file, newline="") as f:
            for row in csv.DictReader(f):
                calendar.add(Event(row["symbol"], row["type"], date.fromisoformat(row["date"]),
                                   row.get("note", ""), row.get("source", "")))
        calendar.save()
        print(f"Imported; calendar now has {len(calendar.events)} events")
    elif args.action == "sync":
        added = _sync(cfg, calendar, today, args.days)
        print(f"Synced {added} events; calendar now has {len(calendar.events)} events")
    elif args.action == "check":
        reasons = calendar.blocking_reasons(args.symbol, today)
        print(f"{args.symbol.upper()}: " + ("BLOCKED for BTST - " + "; ".join(reasons) if reasons else "no results due today or next trading day"))
        for e in calendar.between(today - timedelta(days=30), today + timedelta(days=60), args.symbol):
            print(f"  {e.date}  {e.type:<13} {e.note}")
    else:
        for e in calendar.between(today - timedelta(days=args.past), today + timedelta(days=args.days)):
            print(f"{e.date}  {e.symbol:<12} {e.type:<13} {e.note}  [{e.source}]")


def cmd_review(cfg: Config, args) -> None:
    picks, results = cfg.review_dir / "picks.csv", cfg.review_dir / "results.csv"
    holidays = load_holidays(cfg.calendar_file.with_name("holidays.txt"))
    today = datetime.now(IST).date()
    if args.action == "add":
        day = date.fromisoformat(args.date) if args.date else today
        rows = json.loads(open(args.file).read())
        new = rv.add_picks(picks, [rv.Pick(day, args.session, r["side"], r["symbol"].upper(), float(r["ref_price"]),
                                           r.get("stop"), r.get("target"), r.get("tags", ""), r.get("reason", ""))
                                   for r in rows])
        print(f"Logged {len(rows)} {args.session} picks for {day} ({new} new)")
    elif args.action == "pending":
        todo = rv.pending(picks, results, today, holidays)
        print(json.dumps([{"pick_date": p.day.isoformat(), "session": p.session, "side": p.side, "symbol": p.symbol,
                           "eval_date": d.isoformat()} for p, d in todo], indent=1))
    elif args.action == "score":
        scored, missing = rv.score_pending(picks, results, rv.load_bars(args.prices), today, holidays)
        print(f"Scored {scored} picks")
        if missing:
            print("No price bar for: " + ", ".join(missing))
    else:
        since = today - timedelta(days=args.days) if args.days else None
        print(rv.format_summary(rv.summarize(results, since)))


def main() -> None:
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
    parser = argparse.ArgumentParser(prog="btst", description="BTST trading helper: code screens and risk gate, Claude Code subagents review")
    sub = parser.add_subparsers(dest="command", required=True)
    scan = sub.add_parser("scan", help="Screen stocks and write the shortlist for the Claude Code subagents (run ~3:00-3:15 PM)")
    scan.add_argument("--top", type=int, default=10, help="Shortlist size")
    scan.add_argument("--no-sync", action="store_true", help="Skip the NSE calendar refresh")
    mov = sub.add_parser("movers", help="Top N F&O gainers (BTST plan) and losers (watchlist) for the Claude Code subagents")
    mov.add_argument("--top", type=int, default=20, help="How many gainers and losers to take")
    mov.add_argument("--no-sync", action="store_true", help="Skip the NSE calendar refresh")
    ks = sub.add_parser("kite-screen", help="Screen from a saved Kite MCP get_quotes response (no Dhan/AI keys)")
    ks.add_argument("--quotes", required=True, help="JSON saved from the Kite get_quotes tool")
    ks.add_argument("--mode", choices=["btst", "movers"], default="btst")
    ks.add_argument("--top", type=int, default=10, help="Shortlist size (btst) or gainers/losers each (movers)")
    ks.add_argument("--no-sync", action="store_true", help="Skip the NSE calendar refresh")
    pl = sub.add_parser("plan", help="Risk-gate subagent output (market + reviews JSON) into today's plan")
    pl.add_argument("--market", required=True, help="JSON: bias, allow_new_positions, reasons")
    pl.add_argument("--reviews", required=True, help='JSON: {"reviews":[{symbol,catalyst_score,veto,red_flags,summary}]}')
    rev = sub.add_parser("review", help="Log picks and score them against what the market really did")
    rev_sub = rev.add_subparsers(dest="action", required=True)
    ra = rev_sub.add_parser("add", help="Log picks from a JSON list [{side,symbol,ref_price,stop,target,tags,reason}]")
    ra.add_argument("file")
    ra.add_argument("--session", choices=["am", "pm"], required=True)
    ra.add_argument("--date", help="YYYY-MM-DD, default today")
    rev_sub.add_parser("pending", help="Picks whose result day has arrived and still need a price bar")
    rs = rev_sub.add_parser("score", help='Score pending picks from {"YYYY-MM-DD": {"SYM": {open,high,low,close}}}')
    rs.add_argument("prices")
    rr = rev_sub.add_parser("report", help="How many picks moved the right way")
    rr.add_argument("--days", type=int, default=0, help="Only the last N calendar days (0 = all)")
    cal = sub.add_parser("calendar", help="Results / bulk-deal calendar used to veto BTST picks")
    cal_sub = cal.add_subparsers(dest="action", required=True)
    lst = cal_sub.add_parser("list", help="Upcoming events")
    lst.add_argument("--days", type=int, default=30)
    lst.add_argument("--past", type=int, default=3)
    chk = cal_sub.add_parser("check", help="Is this stock safe to hold overnight?")
    chk.add_argument("symbol")
    add = cal_sub.add_parser("add", help="Add or update one event")
    add.add_argument("symbol")
    add.add_argument("type", choices=sorted(TYPES))
    add.add_argument("date", help="YYYY-MM-DD")
    add.add_argument("--note", default="")
    add.add_argument("--source", default="manual")
    syn = cal_sub.add_parser("sync", help="Pull board meetings and bulk/block deals for the whole universe from NSE")
    syn.add_argument("--days", type=int, default=45)
    imp = cal_sub.add_parser("import", help="Import events from a CSV (symbol,type,date,note,source)")
    imp.add_argument("file")

    args = parser.parse_args()
    cfg = Config.from_env()
    {"scan": cmd_scan, "movers": cmd_movers, "plan": cmd_plan, "kite-screen": cmd_kite_screen, "calendar": cmd_calendar, "review": cmd_review}[args.command](cfg, args)
