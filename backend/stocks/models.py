from django.db import models
from django.utils import timezone


class Ticker(models.Model):
    symbol = models.CharField(max_length=20, unique=True)
    company_name = models.CharField(max_length=255, blank=True, default="")
    exchange = models.CharField(max_length=100, blank=True, default="")
    currency = models.CharField(max_length=10, blank=True, default="")
    sector = models.CharField(max_length=150, blank=True, default="")
    industry = models.CharField(max_length=200, blank=True, default="")
    website = models.URLField(max_length=500, null=True, blank=True)
    business_summary = models.TextField(blank=True, default="")
    full_time_employees = models.IntegerField(null=True, blank=True)
    last_scraped_at = models.DateTimeField(null=True, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["symbol"]

    def __str__(self):
        return self.symbol


class Quote(models.Model):
    ticker = models.ForeignKey(Ticker, on_delete=models.CASCADE, related_name="quotes")
    current_price = models.DecimalField(max_digits=20, decimal_places=4, null=True, blank=True)
    change = models.DecimalField(max_digits=20, decimal_places=4, null=True, blank=True)
    change_percent = models.DecimalField(max_digits=10, decimal_places=4, null=True, blank=True)
    previous_close = models.DecimalField(max_digits=20, decimal_places=4, null=True, blank=True)
    open_price = models.DecimalField(max_digits=20, decimal_places=4, null=True, blank=True)
    days_low = models.DecimalField(max_digits=20, decimal_places=4, null=True, blank=True)
    days_high = models.DecimalField(max_digits=20, decimal_places=4, null=True, blank=True)
    week52_low = models.DecimalField(max_digits=20, decimal_places=4, null=True, blank=True)
    week52_high = models.DecimalField(max_digits=20, decimal_places=4, null=True, blank=True)
    volume = models.BigIntegerField(null=True, blank=True)
    market_cap = models.BigIntegerField(null=True, blank=True)
    pe_ratio = models.DecimalField(max_digits=15, decimal_places=4, null=True, blank=True)
    eps = models.DecimalField(max_digits=15, decimal_places=4, null=True, blank=True)
    scraped_at = models.DateTimeField(default=timezone.now)

    class Meta:
        ordering = ["-scraped_at"]

    def __str__(self):
        return f"{self.ticker.symbol} @ {self.current_price}"


class HistoricalPrice(models.Model):
    ticker = models.ForeignKey(Ticker, on_delete=models.CASCADE, related_name="historical_prices")
    date = models.DateField()
    open_price = models.DecimalField(max_digits=20, decimal_places=4, null=True, blank=True)
    high_price = models.DecimalField(max_digits=20, decimal_places=4, null=True, blank=True)
    low_price = models.DecimalField(max_digits=20, decimal_places=4, null=True, blank=True)
    close_price = models.DecimalField(max_digits=20, decimal_places=4, null=True, blank=True)
    volume = models.BigIntegerField(null=True, blank=True)

    class Meta:
        ordering = ["-date"]
        constraints = [
            models.UniqueConstraint(fields=["ticker", "date"], name="unique_ticker_date")
        ]

    def __str__(self):
        return f"{self.ticker.symbol} {self.date}"


class NewsArticle(models.Model):
    ticker = models.ForeignKey(Ticker, on_delete=models.CASCADE, related_name="news")
    title = models.CharField(max_length=500)
    url = models.URLField(max_length=1000, unique=True)
    source = models.CharField(max_length=200, blank=True, default="")
    published_at = models.DateTimeField(null=True, blank=True)
    published_raw = models.CharField(max_length=200, blank=True, default="")

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-published_at", "-created_at"]

    def __str__(self):
        return self.title[:60]


class ScrapeLog(models.Model):
    class Status(models.TextChoices):
        SUCCESS = "success", "Success"
        PARTIAL = "partial", "Partial"
        FAILED = "failed", "Failed"

    ticker = models.ForeignKey(
        Ticker, on_delete=models.SET_NULL, null=True, blank=True, related_name="scrape_logs"
    )
    status = models.CharField(max_length=10, choices=Status.choices)
    started_at = models.DateTimeField()
    finished_at = models.DateTimeField(null=True, blank=True)
    records_affected = models.IntegerField(default=0)
    error_message = models.TextField(null=True, blank=True)

    class Meta:
        ordering = ["-started_at"]

    def __str__(self):
        return f"{self.ticker or 'N/A'} - {self.status}"
