from datetime import datetime, timezone as dt_tz
from decimal import Decimal, InvalidOperation

from django.db import transaction
from django.utils import timezone

from stocks.models import Ticker, Quote, HistoricalPrice, NewsArticle, ScrapeLog
from . import parsers
from .client import YahooClient, YahooFinanceError


def _dec(value, places="0.0001"):
    """Safely convert strings or floats to Decimal, handling formatting characters."""
    if value is None:
        return None
    try:
        # Strip common formatting characters like '%', '$', ','
        clean_str = str(value).replace("%", "").replace("$", "").replace(",", "").strip()
        return Decimal(clean_str).quantize(Decimal(places))
    except (InvalidOperation, ValueError, TypeError):
        return None


def _int(value):
    """Safely convert value to integer."""
    try:
        return int(value) if value is not None else None
    except (ValueError, TypeError):
        return None


def _set_if(obj, field, value):
    """Only overwrite object attributes when value is non-empty."""
    if value not in (None, ""):
        setattr(obj, field, value)


def _log(ticker, status, started, records, error):
    """Safely log scrape output to ScrapeLog model."""
    log_kwargs = {
        "ticker": ticker,
        "status": status,
        "started_at": started,
        "finished_at": timezone.now(),
    }
    
    # Introspect model fields to prevent keyword argument errors if model fields vary
    field_names = [f.name for f in ScrapeLog._meta.get_fields()]
    
    if "records_affected" in field_names:
        log_kwargs["records_affected"] = records
    elif "records" in field_names:
        log_kwargs["records"] = records

    if "error_message" in field_names:
        log_kwargs["error_message"] = error
    elif "message" in field_names:
        log_kwargs["message"] = error

    ScrapeLog.objects.create(**log_kwargs)


def scrape_ticker(symbol, company_name_hint=""):
    """Scrape a single ticker symbol and record results."""
    symbol = symbol.strip().upper()
    started = timezone.now()
    errors = []
    records = 0

    ticker, _ = Ticker.objects.get_or_create(symbol=symbol)
    client = YahooClient()

    # 1) CHART — Mandatory
    try:
        chart_data = parsers.parse_chart(client.fetch_chart(symbol))
    except YahooFinanceError as exc:
        status_failed = getattr(ScrapeLog.Status, "FAILED", "failed")
        _log(ticker, status_failed, started, 0, str(exc))
        raise

    # 2) SUMMARY — Optional
    summary_data = None
    try:
        summary_data = parsers.parse_summary(client.fetch_summary(symbol))
    except YahooFinanceError as exc:
        errors.append(f"company info unavailable ({exc})")

    # 3) NEWS — Optional
    news_items = []
    try:
        news_items = client.fetch_news(symbol)
    except YahooFinanceError as exc:
        errors.append(f"news unavailable ({exc})")

    meta = chart_data["meta"]
    company = (summary_data or {}).get("company", {})
    q = (summary_data or {}).get("quote", {})

    with transaction.atomic():
        # ---- Ticker ----
        _set_if(ticker, "company_name", company.get("company_name") or company_name_hint)
        _set_if(ticker, "exchange", company.get("exchange") or meta.get("exchange"))
        _set_if(ticker, "currency", company.get("currency") or meta.get("currency"))
        _set_if(ticker, "sector", company.get("sector"))
        _set_if(ticker, "industry", company.get("industry"))
        if company.get("website"):
            ticker.website = company["website"]
        _set_if(ticker, "business_summary", company.get("business_summary"))
        if company.get("full_time_employees") is not None:
            ticker.full_time_employees = _int(company["full_time_employees"])
        ticker.last_scraped_at = timezone.now()
        ticker.save()

        # ---- Quote ----
        current_price = q.get("current_price") or meta.get("current_price")
        previous_close = q.get("previous_close") or meta.get("previous_close")
        change = q.get("change")
        change_percent = q.get("change_percent")

        if current_price is not None and previous_close:
            try:
                c_price = float(current_price)
                p_close = float(previous_close)
                change = c_price - p_close
                change_percent = (change / p_close) * 100
            except (ValueError, TypeError, ZeroDivisionError):
                pass

        Quote.objects.create(
            ticker=ticker,
            current_price=_dec(current_price),
            change=_dec(change),
            change_percent=_dec(change_percent),
            previous_close=_dec(previous_close),
            open_price=_dec(q.get("open_price")),
            days_low=_dec(q.get("days_low") or meta.get("days_low")),
            days_high=_dec(q.get("days_high") or meta.get("days_high")),
            week52_low=_dec(q.get("week52_low") or meta.get("week52_low")),
            week52_high=_dec(q.get("week52_high") or meta.get("week52_high")),
            volume=_int(q.get("volume") or meta.get("volume")),
            market_cap=_int(q.get("market_cap")),
            pe_ratio=_dec(q.get("pe_ratio")),
            eps=_dec(q.get("eps")),
            scraped_at=timezone.now(),
        )
        records += 1

        # ---- Historical Prices ----
        for row in chart_data["historical"]:
            HistoricalPrice.objects.update_or_create(
                ticker=ticker,
                date=row["date"],
                defaults={
                    "open_price": _dec(row["open_price"]),
                    "high_price": _dec(row["high_price"]),
                    "low_price": _dec(row["low_price"]),
                    "close_price": _dec(row["close_price"]),
                    "volume": _int(row["volume"]),
                },
            )
            records += 1

        # ---- News ----
        for item in news_items:
            link = item.get("link")
            if not link:
                continue
            published_dt, raw = None, ""
            ts = item.get("providerPublishTime")
            if ts:
                try:
                    published_dt = datetime.fromtimestamp(int(ts), tz=dt_tz.utc)
                except (ValueError, TypeError, OSError):
                    raw = str(ts)

            NewsArticle.objects.update_or_create(
                url=link,
                defaults={
                    "ticker": ticker,
                    "title": (item.get("title") or "")[:500],
                    "source": item.get("publisher") or item.get("provider") or "",
                    "published_at": published_dt,
                    "published_raw": raw,
                },
            )
            records += 1

    status_success = getattr(ScrapeLog.Status, "SUCCESS", "success")
    status_partial = getattr(ScrapeLog.Status, "PARTIAL", "partial")
    status = status_success if not errors else status_partial
    
    _log(ticker, status, started, records, "; ".join(errors) if errors else None)
    return {"symbol": symbol, "status": str(status), "records": records, "errors": errors}
