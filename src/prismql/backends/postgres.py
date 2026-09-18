"""PostgreSQL backend implementation for PrismQL."""

from collections.abc import Sequence
from typing import Any

from ..types import Document, MessageId
from .base import SearchBackend


class PostgresBackend(SearchBackend):
    """
    PostgreSQL backend for PrismQL.

    Connects to an existing PostgreSQL database and translates PrismQL
    queries to SQL queries. Perfect for annotation platforms and production
    applications already using Postgres.

    Features:
    - Connects to existing Postgres database (no data duplication)
    - Field mapping to match your existing schema
    - Full-text search using Postgres tsvector/tsquery
    - JSONB support for annotations
    - Efficient queries with proper indexes

    Example configuration:
        config = {
            "table_name": "messages",
            "field_mappings": {
                "text": "content",        # PrismQL 'text' -> your 'content' column
                "user": "author_name",    # PrismQL 'user' -> your 'author_name' column
                "id": "message_id"        # PrismQL 'id' -> your 'message_id' column
            },
            "text_search_config": "english",  # Postgres text search config
            "use_fts": True  # Use full-text search (requires tsvector index)
        }

        # Option 1: Pass connection
        import psycopg2
        conn = psycopg2.connect("postgresql://user:pass@localhost/dbname")
        backend = PostgresBackend(conn, config)

        # Option 2: Pass connection string
        backend = PostgresBackend(
            "postgresql://user:pass@localhost/dbname",
            config
        )

    Recommended indexes for performance:
        CREATE INDEX idx_messages_user ON messages(author_name);
        CREATE INDEX idx_messages_ts_vector ON messages
            USING gin(to_tsvector('english', content));
    """

    def __init__(
        self,
        connection: Any | str,
        config: dict[str, Any],
        autocommit: bool = True,
    ) -> None:
        """
        Initialize Postgres backend.

        Args:
            connection: Either a psycopg2/psycopg connection object or connection string
            config: Configuration dictionary with table and field mappings
            autocommit: Whether to use autocommit mode (recommended for read-only)
        """
        # Handle connection string vs connection object
        if isinstance(connection, str):
            try:
                import psycopg2
            except ImportError as e:
                msg = (
                    "psycopg2 is required for PostgresBackend. "
                    "Install it with: pip install psycopg2-binary"
                )
                raise ImportError(msg) from e

            self.conn = psycopg2.connect(connection)
            self._owns_connection = True
        else:
            self.conn = connection
            self._owns_connection = False

        if autocommit:
            self.conn.autocommit = True

        self.config = config

        # Extract configuration
        self.table_name = config["table_name"]
        self.field_mappings = config.get("field_mappings", {})

        # Default field mappings
        self.text_field = self.field_mappings.get("text", "text")
        self.user_field = self.field_mappings.get("user", "user")
        self.id_field = self.field_mappings.get("id", "id")

        # Text search configuration
        self.text_search_config = config.get("text_search_config", "english")
        self.use_fts = config.get("use_fts", True)  # Use full-text search

    def _map_field(self, field: str) -> str:
        """Map PrismQL field name to actual database column name."""
        return str(self.field_mappings.get(field, field))

    def search_text(
        self, terms: Sequence[str], field: str = "text", operator: str = "OR"
    ) -> set[MessageId]:
        """
        Search for messages containing terms.

        Uses Postgres full-text search (to_tsvector/to_tsquery) if use_fts=True,
        otherwise falls back to ILIKE pattern matching.

        Args:
            terms: List of terms to search for
            field: Field to search in (default: "text")
            operator: Boolean operator - "OR" or "AND"

        Returns:
            Set of message IDs matching the search
        """
        if not terms:
            return set()

        column = self._map_field(field)

        if self.use_fts and field == "text":
            # Use Postgres full-text search (much faster with proper index)
            if operator == "OR":
                # Join with | for OR
                query = " | ".join(terms)
            else:  # AND
                # Join with & for AND
                query = " & ".join(terms)

            sql = f"""
                SELECT {self.id_field}
                FROM {self.table_name}
                WHERE to_tsvector(%s, {column}) @@ to_tsquery(%s, %s)
            """
            params: tuple[Any, ...] = (
                self.text_search_config,
                self.text_search_config,
                query,
            )
        else:
            # Fallback to ILIKE pattern matching
            if operator == "OR":
                # Any term matches
                conditions = [f"{column} ILIKE %s" for _ in terms]
                where_clause = " OR ".join(conditions)
                params = tuple(f"%{term}%" for term in terms)
            else:  # AND
                # All terms must match
                conditions = [f"{column} ILIKE %s" for _ in terms]
                where_clause = " AND ".join(conditions)
                params = tuple(f"%{term}%" for term in terms)

            sql = f"""
                SELECT {self.id_field}
                FROM {self.table_name}
                WHERE {where_clause}
            """

        with self.conn.cursor() as cur:
            cur.execute(sql, params)
            return {row[0] for row in cur.fetchall()}

    def search_by_field(
        self, field: str, value: str, exact: bool = True
    ) -> set[MessageId]:
        """
        Search for messages with specific field value.

        Args:
            field: Field name to search in
            value: Value to search for
            exact: Whether to do exact match (=) or partial match (ILIKE)

        Returns:
            Set of message IDs matching the search
        """
        column = self._map_field(field)

        if exact:
            sql = f"""
                SELECT {self.id_field}
                FROM {self.table_name}
                WHERE {column} = %s
            """
            params = (value,)
        else:
            sql = f"""
                SELECT {self.id_field}
                FROM {self.table_name}
                WHERE {column} ILIKE %s
            """
            params = (f"%{value}%",)

        with self.conn.cursor() as cur:
            cur.execute(sql, params)
            return {row[0] for row in cur.fetchall()}

    def get_total_documents(self) -> int:
        """Get total number of documents in the table."""
        sql = f"SELECT COUNT(*) FROM {self.table_name}"
        with self.conn.cursor() as cur:
            cur.execute(sql)
            result = cur.fetchone()
            return int(result[0]) if result else 0

    def get_all_document_ids(self, limit: int | None = None) -> set[MessageId]:
        """
        Get all document IDs (up to limit).

        Args:
            limit: Maximum number of IDs to return

        Returns:
            Set of all document IDs, ordered by ID
        """
        if limit is not None:
            sql = f"""
                SELECT {self.id_field}
                FROM {self.table_name}
                ORDER BY {self.id_field}
                LIMIT %s
            """
            params: tuple[Any, ...] = (limit,)
        else:
            sql = f"""
                SELECT {self.id_field}
                FROM {self.table_name}
                ORDER BY {self.id_field}
            """
            params = ()

        with self.conn.cursor() as cur:
            cur.execute(sql, params)
            return {row[0] for row in cur.fetchall()}

    def get_documents(self, ids: Sequence[MessageId]) -> list[Document]:
        """
        Retrieve full documents by IDs.

        Args:
            ids: List of document IDs to retrieve

        Returns:
            List of documents as dictionaries
        """
        if not ids:
            return []

        # Use ANY for efficient IN clause with parameters
        sql = f"""
            SELECT *
            FROM {self.table_name}
            WHERE {self.id_field} = ANY(%s)
            ORDER BY {self.id_field}
        """

        with self.conn.cursor() as cur:
            cur.execute(sql, (list(ids),))

            # Get column names
            columns = [desc[0] for desc in cur.description]

            # Convert rows to dictionaries
            documents = []
            for row in cur.fetchall():
                doc = dict(zip(columns, row, strict=False))
                documents.append(doc)

            return documents

    def close(self) -> None:
        """Close database connection if we own it."""
        if self._owns_connection and self.conn:
            self.conn.close()

    def __enter__(self) -> "PostgresBackend":
        """Context manager entry."""
        return self

    def __exit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        """Context manager exit - close connection."""
        self.close()

    def execute_custom_query(
        self, sql: str, params: tuple[Any, ...] = ()
    ) -> list[dict[str, Any]]:
        """
        Execute a custom SQL query and return results as dictionaries.

        Useful for advanced queries not covered by the standard interface.

        Args:
            sql: SQL query to execute
            params: Query parameters (use %s placeholders)

        Returns:
            List of result rows as dictionaries

        Example:
            results = backend.execute_custom_query(
                "SELECT user, COUNT(*) FROM messages GROUP BY user",
            )
        """
        with self.conn.cursor() as cur:
            cur.execute(sql, params)
            columns = [desc[0] for desc in cur.description]
            return [dict(zip(columns, row, strict=False)) for row in cur.fetchall()]

    def search_jsonb_field(
        self, field: str, json_path: str, value: Any
    ) -> set[MessageId]:
        """
        Search in JSONB fields using JSON path.

        Perfect for annotation platforms storing annotations in JSONB columns.

        Args:
            field: JSONB column name
            json_path: JSON path (e.g., 'sentiment' or 'labels[0]')
            value: Value to match

        Returns:
            Set of matching message IDs

        Example:
            # Find messages with positive sentiment annotation
            ids = backend.search_jsonb_field(
                'annotations',
                'sentiment',
                'positive'
            )
        """
        column = self._map_field(field)

        sql = f"""
            SELECT {self.id_field}
            FROM {self.table_name}
            WHERE {column} ->> %s = %s
        """

        with self.conn.cursor() as cur:
            cur.execute(sql, (json_path, value))
            return {row[0] for row in cur.fetchall()}
