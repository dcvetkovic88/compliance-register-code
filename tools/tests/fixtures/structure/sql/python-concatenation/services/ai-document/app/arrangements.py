"""Reads the register's arrangements through a concatenated query, which the AI document service must not do."""

import psycopg


def arrangement_count(connection: psycopg.Connection) -> int:
    row = connection.execute("SELECT count(*) FROM " + "register.arrangements").fetchone()
    return row[0] if row else 0
