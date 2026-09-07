import time
import requests
from django.conf import settings


class YahooFinanceError(Exception):
    """Custom exception raised for failed requests or invalid symbols."""
    pass


class YahooClient:
    CHART_URL = "https://query1.finance.yahoo.com/v8/finance/chart/{symbol}"
    SUMMARY_URL = "https://query2.finance.yahoo.com/v10/finance/quoteSummary/{symbol}"
    SEARCH_URL = "https://query1.finance.yahoo.com/v1/finance/search"
    COOKIE_URL = "https://finance.yahoo.com"
    CRUMB_URL = "https://query1.finance.yahoo.com/v1/test/getcrumb"

    def __init__(self):
        self.delay = getattr(settings, "SCRAPER_REQUEST_DELAY", 2)
        self.retries = getattr(settings, "SCRAPER_RETRY_COUNT", 3)
        self.timeout = getattr(settings, "SCRAPER_REQUEST_TIMEOUT", 15)
        
        user_agent = getattr(
            settings, 
            "SCRAPER_USER_AGENT", 
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
        )

        self.session = requests.Session()
        self.session.headers.update({
            "User-Agent": user_agent,
            "Accept": "application/json,text/plain,*/*",
        })
        self.crumb = None

    def _sleep(self):
        if self.delay:
            time.sleep(self.delay)

    def _request(self, url, params=None):
        last_error = None
        for attempt in range(1, self.retries + 1):
            try:
                response = self.session.get(url, params=params, timeout=self.timeout)
                if response.status_code == 200:
                    return response
                last_error = f"HTTP status {response.status_code}"
            except requests.RequestException as err:
                last_error = str(err)

            time.sleep(self.delay * attempt)

        raise YahooFinanceError(f"Request failed after {self.retries} attempts ({last_error})")

    def ensure_crumb(self):
        if self.crumb:
            return self.crumb
        
        try:
            # Set session cookie first
            self.session.get(self.COOKIE_URL, timeout=self.timeout)
            res = self.session.get(self.CRUMB_URL, timeout=self.timeout)
            text = res.text.strip()
            
            if text and "<html" not in text.lower() and "Too Many" not in text:
                self.crumb = text
        except requests.RequestException:
            self.crumb = None

        return self.crumb

    def fetch_chart(self, symbol, timeframe="3mo", interval="1d"):
        url = self.CHART_URL.format(symbol=symbol)
        res = self._request(url, params={"range": timeframe, "interval": interval})
        
        data = res.json().get("chart", {})
        if data.get("error"):
            msg = (data["error"] or {}).get("description", "Unknown symbol error")
            raise YahooFinanceError(f"[{symbol}] {msg}")

        results = data.get("result")
        if not results:
            raise YahooFinanceError(f"[{symbol}] No chart data available")

        self._sleep()
        return results[0]

    def fetch_summary(self, symbol):
        crumb = self.ensure_crumb()
        params = {"modules": "assetProfile,summaryDetail,defaultKeyStatistics,price"}
        if crumb:
            params["crumb"] = crumb

        url = self.SUMMARY_URL.format(symbol=symbol)
        res = self._request(url, params=params)
        
        qs = res.json().get("quoteSummary", {})
        if qs.get("error"):
            msg = (qs["error"] or {}).get("description", "Failed to fetch summary")
            raise YahooFinanceError(f"[{symbol}] {msg}")

        results = qs.get("result")
        self._sleep()
        return results[0] if results else {}

    def fetch_news(self, symbol, limit=10):
        params = {"q": symbol, "newsCount": limit, "quotesCount": 0}
        if self.crumb:
            params["crumb"] = self.crumb

        res = self._request(self.SEARCH_URL, params=params)
        self._sleep()
        return res.json().get("news", [])
