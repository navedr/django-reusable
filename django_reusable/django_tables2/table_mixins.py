from django_tables2 import Table


class EnhancedTable(Table):

    def __init__(self, *args, extra_data={}, fields=None, **kwargs):
        kwargs['template_name'] = 'django_reusable/tables/enhanced-table.html'
        self.extra_data = extra_data
        super().__init__(*args, **kwargs)
        if fields is not None:
            all_fields = self.base_columns.keys()
            self.exclude = self.exclude or []
            self.exclude.extend(set(all_fields).difference(fields))
        self.extra_footers = self.get_extra_footers()

    def get_extra_footers(self):
        """
        :return: List of dict with column as key for each footer row
        """
        return []
