"""
Supabase HTTP client - lightweight alternative to supabase package
Uses raw HTTP calls to Supabase REST API instead of the heavy Python client
"""
import httpx
import os
import json
from typing import List, Dict, Any, Optional


# Cache for Supabase connection info
_SUPABASE_URL = None
_SUPABASE_KEY = None


def _get_supabase_config() -> tuple:
    """Get Supabase URL and key from environment"""
    global _SUPABASE_URL, _SUPABASE_KEY
    if not _SUPABASE_URL:
        _SUPABASE_URL = os.environ.get('SUPABASE_URL')
        _SUPABASE_KEY = os.environ.get('SUPABASE_ANON_KEY')
    return _SUPABASE_URL, _SUPABASE_KEY


def _get_headers() -> Dict[str, str]:
    """Get headers for Supabase REST API requests"""
    _, key = _get_supabase_config()
    return {
        'apikey': key,
        'Authorization': f'Bearer {key}',
        'Content-Type': 'application/json'
    }


def _build_url(table: str) -> str:
    """Build Supabase REST API URL for a table"""
    url, _ = _get_supabase_config()
    return f'{url}/rest/v1/{table}'


class Table:
    """Lightweight Supabase table client using HTTP"""

    def __init__(self, table_name: str):
        self.table_name = table_name

    def select(self, columns: str = '*') -> 'SelectBuilder':
        """Start a SELECT query"""
        return SelectBuilder(self.table_name, columns)

    def insert(self, data) -> 'Result':
        """Insert row(s) - accepts dict for single row or list for multiple"""
        url = _build_url(self.table_name)
        headers = _get_headers()
        response = httpx.post(url, headers=headers, json=data)
        return Result(response)

    def update(self, data: Dict[str, Any]) -> 'UpdateBuilder':
        """Start an UPDATE query"""
        return UpdateBuilder(self.table_name, data)

    def delete(self) -> 'DeleteBuilder':
        """Start a DELETE query"""
        return DeleteBuilder(self.table_name)


class SelectBuilder:
    """Builder for SELECT queries"""

    def __init__(self, table_name: str, columns: str = '*'):
        self.table_name = table_name
        self.columns = columns
        self.filters = []
        self.order_by = None
        self.limit_val = None
        self.single_result = False

    def eq(self, column: str, value: Any) -> 'SelectBuilder':
        """Filter by equality"""
        self.filters.append((column, 'eq', value))
        return self

    def neq(self, column: str, value: Any) -> 'SelectBuilder':
        """Filter by inequality"""
        self.filters.append((column, 'neq', value))
        return self

    def order(self, column: str, desc: bool = False, nulls: str = None) -> 'SelectBuilder':
        """Order results. nulls can be 'last' or 'first'"""
        order = f"{column}.desc" if desc else column
        if nulls:
            order = f"{order}.nulls{nulls}"
        self.order_by = order
        return self

    def limit(self, n: int) -> 'SelectBuilder':
        """Limit results"""
        self.limit_val = n
        return self

    def single(self) -> 'SelectBuilder':
        """Expect single result"""
        self.single_result = True
        return self

    def or_(self, filter_str: str) -> 'SelectBuilder':
        """Add OR filter - accepts Supabase filter string like 'column1.eq.value1,column2.eq.value2'"""
        self.filters.append(('or', 'or', filter_str))
        return self

    def execute(self) -> 'Result':
        """Execute the query"""
        url = _build_url(self.table_name)
        headers = _get_headers()

        params = {'select': self.columns}

        # Add filters
        for column, operator, value in self.filters:
            if operator == 'or':
                params['or'] = value
            elif operator == 'eq':
                params[f'{column}'] = f'eq.{value}'
            elif operator == 'neq':
                params[f'{column}'] = f'neq.{value}'

        # Add ordering
        if self.order_by:
            params['order'] = self.order_by

        # Add limit
        if self.limit_val:
            params['limit'] = self.limit_val

        # For single result
        if self.single_result:
            params['limit'] = 1

        response = httpx.get(url, headers=headers, params=params)
        return Result(response)


class UpdateBuilder:
    """Builder for UPDATE queries"""

    def __init__(self, table_name: str, data: Dict[str, Any]):
        self.table_name = table_name
        self.data = data
        self.filters = []

    def eq(self, column: str, value: Any) -> 'UpdateBuilder':
        """Filter by equality"""
        self.filters.append((column, value))
        return self

    def execute(self) -> 'Result':
        """Execute the update"""
        url = _build_url(self.table_name)
        headers = _get_headers()

        # Build query string for filters
        params = {}
        for i, (column, value) in enumerate(self.filters):
            params[f'{column}'] = f'eq.{value}'

        response = httpx.patch(url, headers=headers, params=params, json=self.data)
        return Result(response)


class DeleteBuilder:
    """Builder for DELETE queries"""

    def __init__(self, table_name: str):
        self.table_name = table_name
        self.filters = []

    def eq(self, column: str, value: Any) -> 'DeleteBuilder':
        """Filter by equality"""
        self.filters.append((column, value))
        return self

    def execute(self) -> 'Result':
        """Execute the delete"""
        url = _build_url(self.table_name)
        headers = _get_headers()

        # Build query string for filters
        params = {}
        for i, (column, value) in enumerate(self.filters):
            params[f'{column}'] = f'eq.{value}'

        response = httpx.delete(url, headers=headers, params=params)
        return Result(response)


class Result:
    """Query result with data attribute"""

    def __init__(self, response: httpx.Response):
        self.response = response
        self.status_code = response.status_code
        self.error = None
        try:
            parsed = response.json()
            # Check if this is an error response
            if isinstance(parsed, dict) and ('error' in parsed or 'message' in parsed or 'code' in parsed):
                # This is an error response, not data
                self.error = parsed.get('error') or parsed.get('message') or str(parsed)
                self.data = []
            elif isinstance(parsed, list):
                # Normal list of rows
                self.data = parsed
            elif isinstance(parsed, dict):
                # Single row returned as dict - wrap in list
                self.data = [parsed]
            elif not parsed:
                self.data = []
            else:
                self.data = []
        except:
            self.data = []

    def execute(self) -> 'Result':
        """Chain method - returns self"""
        return self


def table(table_name: str) -> Table:
    """Get a table client"""
    return Table(table_name)
