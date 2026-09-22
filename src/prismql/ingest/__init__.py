"""Ingest: anything → an ordered Parquet stream the engine loads as-is.

Layer 1 of the ordinal-axis design: whoever produces the table owns joins
and stream order; the engine never joins. The core normalizes one table
(``position``, ``id``, ``time``); ``sources`` turn well-known harness log
folders into that table. (graph ``@aleph/prismql``, node #54)
"""

from .core import embed, normalize, read_source, write

__all__ = ["embed", "normalize", "read_source", "write"]
