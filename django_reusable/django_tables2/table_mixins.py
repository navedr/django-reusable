from django_tables2 import Table
from django_tables2.rows import BoundRow, BoundRows


class EnhancedBoundRow(BoundRow):
    """Extended BoundRow that supports rendering extra rows below the main row."""

    def new_rows(self):
        new_row_columns = self.table.new_row_columns
        rows = sorted(set(new_row_index for column, new_row_index in new_row_columns))
        for row in rows:
            yield self.get_new_row_items(row, new_row_columns)

    def get_new_row_items(self, row, new_row_columns):
        for column, new_row_index in new_row_columns:
            if row == new_row_index:
                column.current_value = self.get_cell(column.name)
                column.current_record = self.record
                if not column.current_value and getattr(column.column, 'no_empty_cell', False):
                    continue
                yield column, column.current_value


class EnhancedBoundRows(BoundRows):
    """Extended BoundRows that yields EnhancedBoundRow instances with new-row support."""

    def __iter__(self):
        # Top pinned rows
        for pinned_record in self.generator_pinned_row(self.pinned_data.get('top')):
            yield pinned_record

        for record in self.data:
            yield EnhancedBoundRow(record, table=self.table)

        # Bottom pinned rows
        for pinned_record in self.generator_pinned_row(self.pinned_data.get('bottom')):
            yield pinned_record

    def __getitem__(self, key):
        """
        Slicing returns a new `~.BoundRows` instance, indexing returns a single
        `~.BoundRow` instance.
        """
        if isinstance(key, slice):
            return self.__class__(
                data=self.data[key],
                table=self.table,
                pinned_data=self.pinned_data
            )
        else:
            return EnhancedBoundRow(record=self.data[key], table=self.table)


class EnhancedTable(Table):
    """Extended django-tables2 Table with support for extra rows, dynamic field selection, and extra footers.

    Uses the ``django_reusable/tables/enhanced-table.html`` template. Columns with
    a ``new_row_index`` attribute are rendered as additional rows beneath the main row.

    Args:
        extra_data: Optional dict of extra context data available to columns/templates.
        fields: Optional list of field names to display. All other columns are excluded.
    """

    def __init__(self, *args, extra_data={}, fields=None, **kwargs):
        kwargs['template_name'] = 'django_reusable/tables/enhanced-table.html'
        self.extra_data = extra_data
        super().__init__(*args, **kwargs)
        if self.new_row_columns:
            self.rows = EnhancedBoundRows(data=self.data, table=self, pinned_data=self.pinned_data)
        if fields is not None:
            all_fields = self.base_columns.keys()
            self.exclude = self.exclude or []
            self.exclude.extend(set(all_fields).difference(fields))
        self.extra_footers = self.get_extra_footers()

    @property
    def new_row_columns(self):
        return [(column, column.column.new_row_index) for column in self.columns.all()
                if getattr(column.column, 'has_new_row_index', False)]

    def get_extra_footers(self):
        """Return extra footer rows for the table. Override in subclasses.

        Returns:
            list[dict]: List of dicts with column names as keys for each footer row.
        """
        return []
