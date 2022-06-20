from django_reusable.mixin_views import CRUDViews
from .models import Person


class ManagerPersonView(CRUDViews):
    base_template = 'admin/base_site.html'
    name = 'person_manager'
    model = Person
    table_fields = ['first_name', 'last_name']
    edit_fields = ['first_name', 'last_name']
    object_title = 'Person'
    allow_edit = False
