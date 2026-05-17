"""Стандартизированная пагинация для REST API.

Возвращает единый формат ответа с метаданными:
``{"count", "next", "previous", "total_pages", "page", "page_size", "results"}``.
"""
from __future__ import annotations

from collections import OrderedDict

from rest_framework import pagination
from rest_framework.response import Response


class StandardPagination(pagination.PageNumberPagination):
    """Стандартная пагинация со страницами фиксированного размера."""

    page_size = 25
    page_size_query_param = "page_size"
    max_page_size = 200

    def get_paginated_response(self, data: list) -> Response:
        return Response(
            OrderedDict(
                [
                    ("count", self.page.paginator.count),
                    ("total_pages", self.page.paginator.num_pages),
                    ("page", self.page.number),
                    ("page_size", self.get_page_size(self.request)),
                    ("next", self.get_next_link()),
                    ("previous", self.get_previous_link()),
                    ("results", data),
                ]
            )
        )


class CursorPagination(pagination.CursorPagination):
    """Курсорная пагинация для бесконечных лент (сообщения, события)."""

    page_size = 50
    ordering = "-created_at"
    cursor_query_param = "cursor"
