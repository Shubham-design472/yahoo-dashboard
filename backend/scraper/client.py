import time
import requests
from django.conf import settings


class YahooFinanceError(Exception):
    """Raised when Yahoo returns an error for a symbol or request fails continuously."""


class YahooClient:
    CHART_URL = "https://query1.finance.yahoo.com/v8/finance/chart/{symbol}"
    SUMMARY_URL = "https://query2.finance.yahoo.com/v10/finance/quoteSummary/{symbol}"
    SEARCH_URL = "https://query1.finance.yahoo.com/v1/finance/search"
    COOKIE_URL = "https://finance.yahoo.com"
    COOKIE_ALT_URL = "https://fc.yahoo.com"
    CRUMB_URL = "https://query1.finance.yahoo.com/v1/test/getcrumb"

    def __init__(self):
        self.delay = getattr(settings, "SCRAPER_REQUEST_DELAY", 2)
        self.retries = getattr(settings, "SCRAPER_RETRY_COUNT", 3)
        self.timeout = getattr(settings, "SCRAPER_REQUEST_TIMEOUT", 15)

        self.session = requests.Session()
        self.session.headers.update({
            "User-Agent": getattr(
                settings,
                "SCRAPER_USER_AGENT",
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            ),
            "Accept": "application/json,text/plain,*/*",
            "Accept-Language": "en-US,en;q=0.9",
        })
        self._crumb = None

    def _sleep(self):
        """Polite pause between requests."""
        if self.delay:
            time.sleep(self.delay)

    def _request(self, url, params=None):
        """GET a URL with timeout and retry logic."""
        last_error = None
        for attempt in range(1, self.retries + 1):
            try:
                resp = self.session.get(url, params=params, timeout=self.timeout)
                if resp.status_code == 200:
                    return resp
                last_error = f"HTTP {resp.status_code}"
            except requests.RequestException as exc:
                last_error = str(exc)
            
            time.sleep((self.delay or 1) * attempt)
            
        raise YahooFinanceError(f"request failed after {self.retries} attempts ({last_error})")

    def ensure_crumb(self):
        """Fetch cookie + crumb needed by summary/search endpoints."""
        if self._crumb:
            return self._crumb

        try:
            # First attempt main cookie URL
            resp = self.session.get(self.COOKIE_URL, timeout=self.timeout)
            if not self.session.cookies:
                # Fallback to FC endpoint if main page sets no cookies
                self.session.get(self.COOKIE_ALT_URL, timeout=self.timeout)

            # Fetch Crumb
            resp = self.session.get(self.CRUMB_URL, timeout=self.timeout)
            crumb = resp.text.strip()
            
            if crumb and "<html" not in crumb.lower() and "too many" not in crumb.lower():
                self._crumb = crumb
        except requests.RequestException:
            self._crumb = None

        return self._crumb

    def fetch_chart(self, symbol, range_="3mo", interval="1d"):
        """Fetch current price + historical OHLCV."""
        url = self.CHART_URL.format(symbol=symbol)
        resp = self._request(url, params={"range": range_, "interval": interval})
        chart = resp.json().get("chart", {})
        
        if chart.get("error"):
            desc = (chart["error"] or {}).get("description", "unknown symbol")
            raise YahooFinanceError(f"{symbol}: {desc}")
            
        results = chart.get("result")
        if not results:
            raise YahooFinanceError(f"{symbol}: no data (symbol may be invalid or delisted)")
            
        self._sleep()
        return results[0]

    def fetch_summary(self, symbol):
        """Fetch company profile + detailed quote fields."""
        crumb = self.ensure_crumb()
        params = {"modules": "assetProfile,summaryDetail,defaultKeyStatistics,price"}
        if crumb:
            params["crumb"] = crumb

        url = self.SUMMARY_URL.format(symbol=symbol)
        resp = self._request(url, params=params)
        qs = resp.json().get("quoteSummary", {})
        
        if qs.get("error"):
            desc = (qs["error"] or {}).get("description", "summary error")
            raise YahooFinanceError(f"{symbol}: {desc}")
            
        results = qs.get("result")
        self._sleep()
        return results[0] if results else {}

    def fetch_news(self, symbol, count=10):
        """Fetch recent news articles for the given symbol."""
        params = {"q": symbol, "newsCount": count, "quotesCount": 0}
        if self._crumb:
            params["crumb"] = self._crumb

        resp = self._request(self.SEARCH_URL, params=params)
        self._sleep()
        return resp.json().get("news", [])
