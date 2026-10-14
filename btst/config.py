import os
from dataclasses import dataclass
from pathlib import Path


def _load_dotenv(path: Path = Path(".env")) -> None:
    if not path.exists():
        return
    for line in path.read_text().splitlines():
        line = line.strip()
        if line and not line.startswith("#") and "=" in line:
            key, _, value = line.partition("=")
            os.environ.setdefault(key.strip(), value.strip())


@dataclass(frozen=True)
class Config:
    dhan_client_id: str
    dhan_access_token: str
    live_trading: bool
    capital_per_trade: float
    max_positions: int
    max_sell_ideas: int
    max_daily_loss: float
    stop_loss_pct: float
    target_pct: float
    exit_by: str
    min_turnover_cr: float
    universe_file: Path
    calendar_file: Path
    review_dir: Path
    data_dir: Path

    @classmethod
    def from_env(cls) -> "Config":
        _load_dotenv()
        env = os.environ.get
        return cls(
            dhan_client_id=env("DHAN_CLIENT_ID", ""),
            dhan_access_token=env("DHAN_ACCESS_TOKEN", ""),
            live_trading=env("LIVE_TRADING", "false").lower() == "true",
            capital_per_trade=float(env("CAPITAL_PER_TRADE", "20000")),
            max_positions=int(env("MAX_POSITIONS", "10")),
            max_sell_ideas=int(env("MAX_SELL_IDEAS", "10")),
            max_daily_loss=float(env("MAX_DAILY_LOSS", "2000")),
            stop_loss_pct=float(env("STOP_LOSS_PCT", "1.0")),
            target_pct=float(env("TARGET_PCT", "2.0")),
            exit_by=env("EXIT_BY", "09:45"),
            min_turnover_cr=float(env("MIN_TURNOVER_CR", "50")),
            universe_file=Path(env("UNIVERSE_FILE", "universe.txt")),
            calendar_file=Path(env("CALENDAR_FILE", "calendar.csv")),
            review_dir=Path(env("REVIEW_DIR", "review")),
            data_dir=Path(env("DATA_DIR", "data")),
        )
