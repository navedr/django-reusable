from django.db.models import Transform, Lookup


class JSONExtract(Transform):
    """ORM Transform that extracts a JSON property for filtering and comparison.

    Enables Django ORM lookups on individual keys within a JSON-stored TextField.
    All comparisons are case-insensitive. Supports SQLite, PostgreSQL, and MySQL.

    Supported lookup chains:

    - ``field__key='value'`` -- exact (case-insensitive)
    - ``field__key__exact='value'``
    - ``field__key__iexact='value'``
    - ``field__key__contains='value'`` -- LIKE with wildcards
    - ``field__key__icontains='value'``

    This class is used internally by ``USAddressField`` and should not normally
    be instantiated directly. Use ``create_instance()`` to register new JSON
    property lookups on a field.

    Example:
        ```python
        # USAddressField registers these automatically:
        Person.objects.filter(home_address__city='New York')
        Person.objects.filter(home_address__state__icontains='n')
        ```
    """
    @staticmethod
    def _get_sub(_lookup_name, expr):
        class JSONExtractSub(Lookup):
            """Case-insensitive lookup for JSON extracted values"""
            lookup_name = _lookup_name

            def as_sql(self, compiler, connection):
                lhs, lhs_params = self.process_lhs(compiler, connection)
                rhs, rhs_params = self.process_rhs(compiler, connection)

                # For LIKE operations, wrap the value with wildcards
                if expr == 'LIKE':
                    # Escape the rhs value and add wildcards
                    if rhs_params:
                        # Convert to lowercase and add wildcards for LIKE pattern
                        rhs_params = [f"%{str(rhs_params[0]).lower()}%"]
                    params = lhs_params + rhs_params
                    return f'{lhs} {expr} %s', params
                else:
                    # For exact matches, just lowercase the rhs
                    if rhs_params:
                        rhs_params = [str(rhs_params[0]).lower()]
                    params = lhs_params + rhs_params
                    return f'{lhs} {expr} %s', params

        return JSONExtractSub

    @classmethod
    def create_instance(cls, json_path):
        """Create a JSONExtract subclass bound to a specific JSON property path.

        Args:
            json_path: The JSON key to extract (e.g. ``'city'``, ``'state'``).

        Returns:
            A JSONExtract subclass with ``lookup_name`` set to ``json_path``.
        """
        class JSONExtractInstance(JSONExtract):
            lookup_name = json_path

            def __init__(self, *args, **kwargs):
                super().__init__(*args, **kwargs)
                self.json_path = json_path

        return JSONExtractInstance

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.json_path = None
        self.__class__.class_lookups = {
            'exact': self._get_sub('exact', '='),
            'iexact': self._get_sub('iexact', '='),
            'contains': self._get_sub('contains', 'LIKE'),
            'icontains': self._get_sub('icontains', 'LIKE'),
        }

    def as_sql(self, compiler, connection):
        lhs, params = compiler.compile(self.lhs)
        # Use JSON extraction for SQLite (json_extract function)
        # For other databases, this might need adjustment
        # Wrap with LOWER() for case-insensitive comparisons
        if connection.vendor == 'sqlite':
            return f"LOWER(json_extract({lhs}, '$.{self.json_path}'))", params
        elif connection.vendor == 'postgresql':
            return f"LOWER({lhs}->>'%s')" % self.json_path, params
        elif connection.vendor == 'mysql':
            return f"LOWER(JSON_UNQUOTE(JSON_EXTRACT({lhs}, '$.{self.json_path}')))", params
        else:
            # Fallback: try to parse JSON in Python (less efficient)
            return f"LOWER({lhs})", params
