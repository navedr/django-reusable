from django_tables2 import Column

from django_reusable.django_tables2.columns import EnhancedColumn
from django_reusable.django_tables2.table_mixins import EnhancedTable
from .models import Person


class PersonTable(EnhancedTable):
    first_name = Column()
    last_name = EnhancedColumn(new_row_index=1, colspan=2)

    class Meta:
        model = Person
        orderable = False
        attrs = {'class': 'pdf-table mtop table table-bordered'}
