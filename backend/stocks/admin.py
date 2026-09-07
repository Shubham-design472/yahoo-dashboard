from django.contrib import admin
from .models import Ticker, Quote, HistoricalPrice, NewsArticle, ScrapeLog


@admin.register(Ticker)
class TickerAdmin(admin.ModelAdmin):
    list_display = ("symbol", "company_name", "exchange", "sector", "last_scraped_at")
    search_fields = ("symbol", "company_name")


@admin.register(Quote)
class QuoteAdmin(admin.ModelAdmin):
    list_display = ("ticker", "current_price", "change", "change_percent", "scraped_at")


@admin.register(HistoricalPrice)
class HistoricalPriceAdmin(admin.ModelAdmin):
    list_display = ("ticker", "date", "open_price", "high_price", "low_price", "close_price", "volume")
    list_filter = ("ticker",)


@admin.register(NewsArticle)
class NewsArticleAdmin(admin.ModelAdmin):
    list_display = ("title", "ticker", "source", "published_at")


@admin.register(ScrapeLog)
class ScrapeLogAdmin(admin.ModelAdmin):
    list_display = ("ticker", "status", "started_at", "finished_at", "records_affected")
    list_filter = ("status",)
