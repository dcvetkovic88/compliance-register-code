"""The AI document service's own documents; a docstring may say SELECT * FROM register.arrangements."""

import psycopg

CONSUMED_EVENT = "register.arrangement.created"


def document_count(connection: psycopg.Connection) -> int:
    """Counts the documents with SELECT count(*) FROM aidoc.documents."""
    # SELECT * FROM register.arrangements in a comment is not read.
    row = connection.execute(
        "SELECT count(*) FROM aidoc.documents WHERE tenant_id = platform.current_tenant_id()"
    ).fetchone()
    return row[0] if row else 0
