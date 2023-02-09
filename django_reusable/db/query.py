from django.db import connection


def execute(query):
    with connection.cursor() as cursor:
        cursor.execute(query)
