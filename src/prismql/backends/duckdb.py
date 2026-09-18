"""DuckDB backend implementation for PrismQL."""

from collections.abc import Sequence
from pathlib import Path
from typing import Any

from ..types import Document, MessageId
from .base import SearchBackend


class DuckDBBackend(SearchBackend):
    """
    DuckDB backend for PrismQL.

    DuckDB is a fast in-process analytical database perfect for:
    - LLM research interfaces with large conversation datasets
    - Fast analytics on conversation data (100x faster than Pandas)
    - Direct querying of Parquet/CSV files without loading into database
    - In-memory or persistent databases
    - Columnar storage for efficient aggregations

    Features:
    - Blazing fast queries (OLAP-optimized)
    - Direct Parquet/CSV file queries
    - Full-text search support
    - Zero configuration for in-memory mode
    - Can create database from Pandas DataFrame
    - SQL-based with great Python integration

    Example usage:
        # Option 1: In-memory from DataFrame
        backend = DuckDBBackend.from_dataframe(df, id_field="msg_id")

        # Option 2: Query Parquet file directly
        backend = DuckDBBackend.from_parquet("conversations.parquet")

        # Option 3: Persistent database
        backend = DuckDBBackend("research.duckdb", table_name="messages")

        # Option 4: Query CSV
        backend = DuckDBBackend.from_csv("data.csv")

    All methods:
        engine = PrismQLEngine(backend)
        result = engine.execute("SELECT from(alice) AND contains(question)")
    """

    def __init__(
        self,
        database: str | Any = ":memory:",
        table_name: str = "messages",
        field_mappings: dict[str, str] | None = None,
        create_fts_index: bool = True,
    ) -> None:
        """
        Initialize DuckDB backend.

        Args:
            database: Database path or ":memory:" for in-memory, or duckdb connection
            table_name: Name of the table containing messages
            field_mappings: Map PrismQL fields to your column names
            create_fts_index: Whether to create full-text search index

        Example:
            backend = DuckDBBackend(
                "research.duckdb",
                table_name="conversations",
                field_mappings={
                    "text": "message_text",
                    "user": "author",
                    "id": "message_id"
                }
            )
        """
        try:
            import duckdb
        except ImportError as e:
            msg = (
                "duckdb is required for DuckDBBackend. "
                "Install it with: pip install duckdb"
            )
            raise ImportError(msg) from e

        # Handle connection vs path
        if isinstance(database, str):
            self.conn = duckdb.connect(database)
            self._owns_connection = True
        else:
            self.conn = database
            self._owns_connection = False

        self.table_name = table_name
        self.field_mappings = field_mappings or {}

        # Default field mappings
        self.text_field = self.field_mappings.get("text", "text")
        self.user_field = self.field_mappings.get("user", "user")
        self.id_field = self.field_mappings.get("id", "id")

        self.create_fts_index = create_fts_index

        # Check if table exists and optionally create FTS index
        if self._table_exists():
            if create_fts_index:
                self._setup_fts_index()

    @classmethod
    def from_dataframe(
        cls,
        df: Any,
        table_name: str = "messages",
        id_field: str = "id",
        text_field: str = "text",
        user_field: str = "user",
    ) -> "DuckDBBackend":
        """
        Create DuckDB backend from Pandas DataFrame.

        Perfect for LLM research interfaces using DataFrames!

        Args:
            df: Pandas DataFrame with conversation data
            table_name: Name for the table
            id_field: Column name for message ID
            text_field: Column name for message text
            user_field: Column name for user/author

        Returns:
            DuckDBBackend instance

        Example:
            import pandas as pd
            df = pd.read_csv("conversations.csv")
            backend = DuckDBBackend.from_dataframe(df)
            engine = PrismQLEngine(backend)
        """
        try:
            import duckdb
        except ImportError as e:
            msg = "duckdb is required. Install it with: pip install duckdb"
            raise ImportError(msg) from e

        # Create in-memory database
        conn = duckdb.connect(":memory:")

        # Register DataFrame as a table
        conn.register(table_name, df)

        # Create field mappings
        field_mappings = {
            "id": id_field,
            "text": text_field,
            "user": user_field,
        }

        backend = cls(conn, table_name, field_mappings, create_fts_index=False)

        # Create FTS index if text column exists
        if text_field in df.columns:
            backend._setup_fts_index()

        return backend

    @classmethod
    def from_parquet(
        cls,
        parquet_path: str | Path,
        table_name: str = "messages",
        id_field: str = "id",
        text_field: str = "text",
        user_field: str = "user",
    ) -> "DuckDBBackend":
        """
        Create DuckDB backend that queries Parquet file directly.

        DuckDB can query Parquet files without loading them into memory!
        Perfect for large conversation datasets stored in Parquet format.

        Args:
            parquet_path: Path to Parquet file
            table_name: Name for the view
            id_field: Column name for message ID
            text_field: Column name for message text
            user_field: Column name for user/author

        Returns:
            DuckDBBackend instance

        Example:
            backend = DuckDBBackend.from_parquet("conversations.parquet")
            engine = PrismQLEngine(backend)
            # Queries run directly on Parquet file!
        """
        try:
            import duckdb
        except ImportError as e:
            msg = "duckdb is required. Install it with: pip install duckdb"
            raise ImportError(msg) from e

        conn = duckdb.connect(":memory:")

        # Create view that reads from Parquet
        conn.execute(
            f"CREATE VIEW {table_name} AS SELECT * FROM read_parquet('{parquet_path}')"
        )

        field_mappings = {
            "id": id_field,
            "text": text_field,
            "user": user_field,
        }

        return cls(conn, table_name, field_mappings, create_fts_index=True)

    @classmethod
    def from_csv(
        cls,
        csv_path: str | Path,
        table_name: str = "messages",
        id_field: str = "id",
        text_field: str = "text",
        user_field: str = "user",
        **csv_kwargs: Any,
    ) -> "DuckDBBackend":
        """
        Create DuckDB backend that queries CSV file directly.

        Args:
            csv_path: Path to CSV file
            table_name: Name for the view
            id_field: Column name for message ID
            text_field: Column name for message text
            user_field: Column name for user/author
            **csv_kwargs: Additional CSV reading options (header, delimiter, etc.)

        Returns:
            DuckDBBackend instance

        Example:
            backend = DuckDBBackend.from_csv("conversations.csv")
            engine = PrismQLEngine(backend)
        """
        try:
            import duckdb
        except ImportError as e:
            msg = "duckdb is required. Install it with: pip install duckdb"
            raise ImportError(msg) from e

        conn = duckdb.connect(":memory:")

        # Build CSV reading options
        csv_options = ", ".join(f"{k}={v}" for k, v in csv_kwargs.items())
        if csv_options:
            csv_options = f", {csv_options}"

        # Create view that reads from CSV
        conn.execute(
            f"CREATE VIEW {table_name} AS SELECT * FROM read_csv_auto('{csv_path}'{csv_options})"
        )

        field_mappings = {
            "id": id_field,
            "text": text_field,
            "user": user_field,
        }

        return cls(conn, table_name, field_mappings, create_fts_index=True)

    def _map_field(self, field: str) -> str:
        """Map PrismQL field name to actual column name."""
        return str(self.field_mappings.get(field, field))

    def _table_exists(self) -> bool:
        """Check if table/view exists."""
        try:
            result = self.conn.execute(
                f"SELECT 1 FROM {self.table_name} LIMIT 1"
            ).fetchone()
            return result is not None
        except Exception:
            return False

    def _setup_fts_index(self) -> None:
        """Set up full-text search index using DuckDB FTS extension."""
        try:
            # Install and load FTS extension
            self.conn.execute("INSTALL fts")
            self.conn.execute("LOAD fts")

            # Create FTS index on text field
            text_col = self._map_field("text")
            self.conn.execute(
                f"PRAGMA create_fts_index('{self.table_name}', '{self.id_field}', '{text_col}')"
            )
        except Exception:
            # FTS not available or already exists - that's okay
            pass

    def search_text(
        self, terms: Sequence[str], field: str = "text", operator: str = "OR"
    ) -> set[MessageId]:
        """
        Search for messages containing terms.

        Uses DuckDB's LIKE operator for text search.

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

        # Build LIKE conditions
        if operator == "OR":
            # Any term matches
            conditions = [f"LOWER({column}) LIKE LOWER('%' || ? || '%')" for _ in terms]
            where_clause = " OR ".join(conditions)
        else:  # AND
            # All terms must match
            conditions = [f"LOWER({column}) LIKE LOWER('%' || ? || '%')" for _ in terms]
            where_clause = " AND ".join(conditions)

        sql = f"SELECT {self.id_field} FROM {self.table_name} WHERE {where_clause}"

        result = self.conn.execute(sql, list(terms)).fetchall()
        return {row[0] for row in result}

    def search_by_field(
        self, field: str, value: str, exact: bool = True
    ) -> set[MessageId]:
        """
        Search for messages with specific field value.

        Args:
            field: Field name to search in
            value: Value to search for
            exact: Whether to do exact match (=) or partial match (LIKE)

        Returns:
            Set of message IDs matching the search
        """
        column = self._map_field(field)

        if exact:
            sql = f"SELECT {self.id_field} FROM {self.table_name} WHERE {column} = ?"
            params = [value]
        else:
            sql = f"SELECT {self.id_field} FROM {self.table_name} WHERE LOWER({column}) LIKE LOWER('%' || ? || '%')"
            params = [value]

        result = self.conn.execute(sql, params).fetchall()
        return {row[0] for row in result}

    def get_total_documents(self) -> int:
        """Get total number of documents in the table."""
        sql = f"SELECT COUNT(*) FROM {self.table_name}"
        result = self.conn.execute(sql).fetchone()
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
            sql = f"SELECT {self.id_field} FROM {self.table_name} ORDER BY {self.id_field} LIMIT ?"
            result = self.conn.execute(sql, [limit]).fetchall()
        else:
            sql = f"SELECT {self.id_field} FROM {self.table_name} ORDER BY {self.id_field}"
            result = self.conn.execute(sql).fetchall()

        return {row[0] for row in result}

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

        # Build parameterized query
        placeholders = ",".join("?" * len(ids))
        sql = f"SELECT * FROM {self.table_name} WHERE {self.id_field} IN ({placeholders}) ORDER BY {self.id_field}"

        result = self.conn.execute(sql, list(ids))

        # Get column names
        columns = [desc[0] for desc in result.description]

        # Convert rows to dictionaries
        documents = []
        for row in result.fetchall():
            doc = dict(zip(columns, row, strict=False))
            documents.append(doc)

        return documents

    def execute_query(self, sql: str, params: Sequence[Any] | None = None) -> Any:
        """
        Execute a custom DuckDB SQL query.

        Perfect for advanced analytics on conversation data!

        Args:
            sql: SQL query to execute
            params: Query parameters (use ? placeholders)

        Returns:
            DuckDB query result

        Example:
            # Get message counts by user
            result = backend.execute_query(
                "SELECT user, COUNT(*) as count FROM messages GROUP BY user"
            )
            df = result.df()  # Convert to DataFrame
        """
        if params:
            return self.conn.execute(sql, list(params))
        return self.conn.execute(sql)

    def to_dataframe(self) -> Any:
        """
        Export entire table to Pandas DataFrame.

        Returns:
            Pandas DataFrame with all messages
        """
        sql = f"SELECT * FROM {self.table_name}"
        return self.conn.execute(sql).df()

    def close(self) -> None:
        """Close database connection if we own it."""
        if self._owns_connection and self.conn:
            self.conn.close()

    def __enter__(self) -> "DuckDBBackend":
        """Context manager entry."""
        return self

    def __exit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        """Context manager exit - close connection."""
        self.close()
