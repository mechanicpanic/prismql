"""Source adapters: a well-known log folder → the canonical stream.

An adapter belongs here when the format is shared by many users (a
harness's session log); an adapter for one dataset stays next to the
dataset and hands one table to ``prismql ingest table``.
"""
