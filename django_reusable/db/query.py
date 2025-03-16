from django.db import connection


def execute(query):
    """
    Executes a raw SQL query using Django's database connection.

    Args:
        query (str): The raw SQL query to be executed.

    Returns:
        None
    """
    with connection.cursor() as cursor:
        cursor.execute(query)
