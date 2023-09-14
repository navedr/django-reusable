from django_tables2 import SingleTableView

from django_reusable.views.mixins import CRUDViews
from .models import Person, Musician
from .tables import PersonTable
from .wizards import MusicianWizardView


def filter_gender(qs, value):
    return qs.filter(first_name='Naved') if value == 'Male' else qs.exclude(first_name='Naved')


class ManagerPersonView(CRUDViews):
    base_template = 'admin/base_site.html'
    name = 'person_manager'
    model = Person
    table_fields = ['first_name', 'last_name', 'position']
    edit_fields = ['first_name', 'last_name']
    object_title = 'Person'
    allow_edit = False

    filters = ['position', ('gender', dict(label='Gender', get_choices=lambda: [('Male', 'Male'), ('Female', 'Female')],
                                           filter=filter_gender))]
    search_fields = ['first_name', 'last_name']


class MusicianCRUDView(CRUDViews):
    model = Musician
    add_wizard_view_class = MusicianWizardView
    base_template = 'admin/base_site.html'
    name = 'musician_manager'
    table_fields = ['first_name', 'last_name']
    edit_fields = ['first_name', 'last_name']
    object_title = 'Person'


class PersonTableView(SingleTableView):
    template_name = 'admin/table.pug'
    table_class = PersonTable
    queryset = Person.objects.all()
