from django.shortcuts import render

"""
API Endpoint Views:
  - GET  /api/tickers/              List all tickers + latest quote
  - POST /api/tickers/              Add a ticker and trigger scrape
  - GET  /api/tickers/<symbol>/     Get single ticker metadata
  - GET  /api/tickers/<symbol>/history/  Get OHLCV history with date filtering
  - GET  /api/tickers/<symbol>/news/     Get news for a ticker
  - GET  /api/logs/                 Get scraper activity logs
"""

from django.shortcuts import get_object_or_404
from django.utils.dateparse import parse_date
from rest_framework import generics, status
from rest_framework.response import Response

from scraper.client import YahooFinanceError
from scraper.service import scrape_ticker

from .models import Ticker, ScrapeLog
from .serializers import (
    TickerListSerializer,
    TickerDetailSerializer,
    HistoricalPriceSerializer,
    NewsArticleSerializer,
    ScrapeLogSerializer,
    AddTickerSerializer,
)


class TickerListCreateView(generics.ListCreateAPIView):
    queryset = Ticker.objects.prefetch_related("quotes").all()

    def get_serializer_class(self):
        if self.request.method == "POST":
            return AddTickerSerializer
        return TickerListSerializer

    def create(self, request, *args, **kwargs):
        serializer = AddTickerSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        symbol = serializer.validated_data["symbol"]

        existed = Ticker.objects.filter(symbol=symbol).exists()
        try:
            result = scrape_ticker(symbol)
        except YahooFinanceError as exc:
            # Cleanup orphan row if this symbol failed on initial creation
            if not existed:
                Ticker.objects.filter(symbol=symbol).delete()
            return Response(
                {"detail": f"Could not add '{symbol}': {exc}"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        ticker = Ticker.objects.get(symbol=symbol)
        data = TickerDetailSerializer(ticker).data
        data["scrape_status"] = result["status"]
        return Response(data, status=status.HTTP_201_CREATED)


class TickerDetailView(generics.RetrieveAPIView):
    serializer_class = TickerDetailSerializer

    def get_object(self):
        symbol = self.kwargs["symbol"].upper()
        return get_object_or_404(Ticker, symbol=symbol)


class HistoricalPriceListView(generics.ListAPIView):
    serializer_class = HistoricalPriceSerializer

    def get_queryset(self):
        ticker = get_object_or_404(Ticker, symbol=self.kwargs["symbol"].upper())
        qs = ticker.historical_prices.order_by("date")

        start = parse_date(self.request.query_params.get("start", "") or "")
        end = parse_date(self.request.query_params.get("end", "") or "")

        if start:
            qs = qs.filter(date__gte=start)
        if end:
            qs = qs.filter(date__lte=end)
        return qs


class NewsListView(generics.ListAPIView):
    serializer_class = NewsArticleSerializer

    def get_queryset(self):
        ticker = get_object_or_404(Ticker, symbol=self.kwargs["symbol"].upper())
        return ticker.news.all()


class ScrapeLogListView(generics.ListAPIView):
    queryset = ScrapeLog.objects.select_related("ticker").all().order_by("-started_at")
    serializer_class = ScrapeLogSerializer
