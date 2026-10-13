def normalize_kite_quotes(doc, universe: set[str]) -> tuple[dict[str, dict], dict[str, dict]]:
    """Split a Kite `quote` response ({"NSE:INFY": {...}}, possibly wrapped in "data") into
    (stock quotes keyed by symbol, index snapshot keyed by index name)."""
    data = doc
    for key in ("data", "result"):
        if isinstance(data, dict) and isinstance(data.get(key), dict):
            data = data[key]
    quotes: dict[str, dict] = {}
    indices: dict[str, dict] = {}
    for key, q in (data.items() if isinstance(data, dict) else []):
        if not isinstance(q, dict) or "last_price" not in q:
            continue
        exchange, _, name = key.partition(":")
        if not name:
            exchange, name = "NSE", key
        if exchange.upper() != "NSE":
            continue
        if name.upper() in universe:
            quotes[name.upper()] = q
        else:
            prev = float((q.get("ohlc") or {}).get("close") or 0)
            last = float(q["last_price"])
            indices[name] = {"last_price": last, "prev_close": prev,
                             "change_pct": round((last / prev - 1) * 100, 2) if prev else None}
    return quotes, indices
