from django.urls import path
from . import views

urlpatterns = [
    path("tickers/", views.TickerListCreateView.as_view(), name="ticker-list"),
    path("tickers/<str:symbol>/", views.TickerDetailView.as_view(), name="ticker-detail"),
    path("tickers/<str:symbol>/history/", views.HistoricalPriceListView.as_view(), name="ticker-history"),
    path("tickers/<str:symbol>/news/", views.NewsListView.as_view(), name="ticker-news"),
    path("logs/", views.ScrapeLogListView.as_view(), name="scrape-logs"),
]
