from django.conf.urls import url

from .views import ManagerPersonView, PersonTableView

urlpatterns = [
    url(r'^person/', ManagerPersonView.as_view(), name='person_manager'),
    url(r'^person-table/', PersonTableView.as_view(), name='person_table'),
]
