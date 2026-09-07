from datetime import datetime, timezone as dt_tz


def num(value):
    """Return a plain numeric value from either a primitive or {'raw': val, ...}."""
    if isinstance(value, dict):
        value = value.get("raw")
    return value


def parse_chart(result):
    """Parse output from the chart endpoint."""
    meta = result.get("meta", {}) or {}
    out = {
        "meta": {
            "currency": meta.get("currency"),
            "exchange": meta.get("fullExchangeName") or meta.get("exchangeName"),
            "current_price": meta.get("regularMarketPrice"),
            "previous_close": meta.get("chartPreviousClose") or meta.get("previousClose"),
            "days_low": meta.get("regularMarketDayLow"),
            "days_high": meta.get("regularMarketDayHigh"),
            "week52_low": meta.get("fiftyTwoWeekLow"),
            "week52_high": meta.get("fiftyTwoWeekHigh"),
            "volume": meta.get("regularMarketVolume"),
        },
        "historical": [],
    }

    timestamps = result.get("timestamp") or []
    quote_list = (result.get("indicators", {}) or {}).get("quote") or [{}]
    quote_block = quote_list[0] if quote_list else {}

    opens = quote_block.get("open") or []
    highs = quote_block.get("high") or []
    lows = quote_block.get("low") or []
    closes = quote_block.get("close") or []
    volumes = quote_block.get("volume") or []

    def at(seq, i):
        return seq[i] if i < len(seq) else None

    for i, ts in enumerate(timestamps):
        try:
            day = datetime.fromtimestamp(ts, tz=dt_tz.utc).date()
        except (OSError, ValueError, TypeError):
            continue

        # Skip incomplete holiday rows
        if at(closes, i) is None and at(opens, i) is None:
            continue

        out["historical"].append({
            "date": day,
            "open_price": at(opens, i),
            "high_price": at(highs, i),
            "low_price": at(lows, i),
            "close_price": at(closes, i),
            "volume": at(volumes, i),
        })
    return out


def parse_summary(result):
    """Parse output from the quoteSummary endpoint."""
    profile = result.get("assetProfile", {}) or {}
    detail = result.get("summaryDetail", {}) or {}
    stats = result.get("defaultKeyStatistics", {}) or {}
    price = result.get("price", {}) or {}

    company = {
        "company_name": price.get("longName") or price.get("shortName"),
        "exchange": price.get("exchangeName") or price.get("fullExchangeName"),
        "currency": price.get("currency"),
        "sector": profile.get("sector"),
        "industry": profile.get("industry"),
        "website": profile.get("website"),
        "business_summary": profile.get("longBusinessSummary"),
        "full_time_employees": profile.get("fullTimeEmployees"),
    }

    quote = {
        "current_price": num(price.get("regularMarketPrice")),
        "change": num(price.get("regularMarketChange")),
        "change_percent": num(price.get("regularMarketChangePercent")),
        "previous_close": num(detail.get("previousClose")),
        "open_price": num(detail.get("open")),
        "days_low": num(detail.get("dayLow")),
        "days_high": num(detail.get("dayHigh")),
        "week52_low": num(detail.get("fiftyTwoWeekLow")),
        "week52_high": num(detail.get("fiftyTwoWeekHigh")),
        "volume": num(detail.get("volume")),
        "market_cap": num(detail.get("marketCap")) or num(price.get("marketCap")),
        "pe_ratio": num(detail.get("trailingPE")),
        "eps": num(stats.get("trailingEps")),
    }
    return {"company": company, "quote": quote}
