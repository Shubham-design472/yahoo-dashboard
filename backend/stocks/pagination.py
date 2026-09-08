"""
Standard Pagination configuration.

Allows client page size overrides via `?page_size=...` up to a maximum limit of 500.
"""

from rest_framework.pagination import PageNumberPagination


class StandardPagination(PageNumberPagination):
    page_size = 10
    page_size_query_param = "page_size"
    max_page_size = 500
