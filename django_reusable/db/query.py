from django.db import connection


def execute(query):
    """Execute a raw SQL statement (e.g. DDL or DML) with no return value.

    Args:
        query: Raw SQL string to execute.
    """
    with connection.cursor() as cursor:
        cursor.execute(query)
