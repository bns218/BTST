import sqlite3
from datetime import date
from pathlib import Path

SCHEMA = """
CREATE TABLE IF NOT EXISTS trades (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    mode TEXT NOT NULL,
    trade_date TEXT NOT NULL,
    symbol TEXT NOT NULL,
    security_id TEXT NOT NULL,
    qty INTEGER NOT NULL,
    entry_price REAL NOT NULL,
    stop_loss REAL NOT NULL,
    target REAL NOT NULL,
    buy_order_id TEXT,
    reason TEXT,
    status TEXT NOT NULL DEFAULT 'OPEN',
    exit_date TEXT,
    exit_price REAL,
    exit_reason TEXT,
    sell_order_id TEXT,
    pnl REAL
)
"""


class Journal:
    def __init__(self, path: Path):
        path.parent.mkdir(parents=True, exist_ok=True)
        self.db = sqlite3.connect(path)
        self.db.row_factory = sqlite3.Row
        self.db.execute(SCHEMA)

    def record_buy(self, mode: str, plan: dict, buy_order_id: str | None) -> None:
        self.db.execute(
            "INSERT INTO trades (mode, trade_date, symbol, security_id, qty, entry_price, stop_loss, target,"
            " buy_order_id, reason) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
            (mode, date.today().isoformat(), plan["symbol"], plan["security_id"], plan["qty"],
             plan["entry_limit"], plan["stop_loss"], plan["target"], buy_order_id, plan["reason"]),
        )
        self.db.commit()

    def open_trades(self, mode: str, bought_before: date) -> list[sqlite3.Row]:
        return self.db.execute(
            "SELECT * FROM trades WHERE status = 'OPEN' AND mode = ? AND trade_date < ?",
            (mode, bought_before.isoformat()),
        ).fetchall()

    def update_fill(self, trade_id: int, qty: int, price: float) -> None:
        self.db.execute("UPDATE trades SET qty = ?, entry_price = ? WHERE id = ?", (qty, price, trade_id))
        self.db.commit()

    def mark_unfilled(self, trade_id: int) -> None:
        self.db.execute("UPDATE trades SET status = 'UNFILLED', pnl = 0 WHERE id = ?", (trade_id,))
        self.db.commit()

    def record_exit(self, trade_id: int, price: float, reason: str, sell_order_id: str | None) -> None:
        row = self.db.execute("SELECT qty, entry_price FROM trades WHERE id = ?", (trade_id,)).fetchone()
        pnl = (price - row["entry_price"]) * row["qty"]
        self.db.execute(
            "UPDATE trades SET status = 'CLOSED', exit_date = ?, exit_price = ?, exit_reason = ?,"
            " sell_order_id = ?, pnl = ? WHERE id = ?",
            (date.today().isoformat(), price, reason, sell_order_id, round(pnl, 2), trade_id),
        )
        self.db.commit()

    def realized_pnl(self, on: date) -> float:
        row = self.db.execute("SELECT COALESCE(SUM(pnl), 0) FROM trades WHERE exit_date = ?",
                              (on.isoformat(),)).fetchone()
        return float(row[0])

    def summary(self) -> list[sqlite3.Row]:
        return self.db.execute(
            "SELECT mode, COUNT(*) AS trades, SUM(pnl > 0) AS wins, ROUND(SUM(pnl), 2) AS pnl"
            " FROM trades WHERE status = 'CLOSED' GROUP BY mode").fetchall()
