# Create your views here.
from django_reusable.mixin_views import CRUDViews
from .models import Person


class ManagerPersonView(CRUDViews):
    base_template = 'admin/base_site.html'
    name = 'person_manager'
    model = Person
