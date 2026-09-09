from rest_framework import serializers
from .models import Ticker, Quote, HistoricalPrice, NewsArticle, ScrapeLog


class QuoteSerializer(serializers.ModelSerializer):
    class Meta:
        model = Quote
        fields = [
            "current_price",
            "change",
            "change_percent",
            "previous_close",
            "open_price",
            "days_low",
            "days_high",
            "week52_low",
            "week52_high",
            "volume",
            "market_cap",
            "pe_ratio",
            "eps",
            "scraped_at",
        ]


class TickerListSerializer(serializers.ModelSerializer):
    """Used for list endpoints: basic ticker details and latest quote."""
    latest_quote = serializers.SerializerMethodField()

    class Meta:
        model = Ticker
        fields = [
            "id",
            "symbol",
            "company_name",
            "exchange",
            "currency",
            "sector",
            "industry",
            "last_scraped_at",
            "latest_quote",
        ]

    def get_latest_quote(self, obj):
        # Uses pre-fetched quotes list to prevent N+1 queries
        quotes = list(obj.quotes.all())
        return QuoteSerializer(quotes[0]).data if quotes else None


class TickerDetailSerializer(serializers.ModelSerializer):
    """Used for detail endpoints: comprehensive profile and latest quote."""
    latest_quote = serializers.SerializerMethodField()

    class Meta:
        model = Ticker
        fields = [
            "id",
            "symbol",
            "company_name",
            "exchange",
            "currency",
            "sector",
            "industry",
            "website",
            "business_summary",
            "full_time_employees",
            "last_scraped_at",
            "latest_quote",
        ]

    def get_latest_quote(self, obj):
        quote = obj.quotes.first()
        return QuoteSerializer(quote).data if quote else None


class HistoricalPriceSerializer(serializers.ModelSerializer):
    class Meta:
        model = HistoricalPrice
        fields = [
            "date",
            "open_price",
            "high_price",
            "low_price",
            "close_price",
            "volume",
        ]


class NewsArticleSerializer(serializers.ModelSerializer):
    class Meta:
        model = NewsArticle
        fields = ["title", "url", "source", "published_at", "published_raw"]


class ScrapeLogSerializer(serializers.ModelSerializer):
    ticker_symbol = serializers.SerializerMethodField()

    class Meta:
        model = ScrapeLog
        fields = [
            "id",
            "ticker_symbol",
            "status",
            "started_at",
            "finished_at",
            "records_affected",
            "error_message",
        ]

    def get_ticker_symbol(self, obj):
        return obj.ticker.symbol if obj.ticker else None


class AddTickerSerializer(serializers.Serializer):
    """Validates symbol POST input when triggering a scraper run."""
    symbol = serializers.CharField(max_length=20)

    def validate_symbol(self, value):
        cleaned = value.strip().upper()
        if not cleaned:
            raise serializers.ValidationError("Symbol cannot be empty.")
        return cleaned
