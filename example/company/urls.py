from django.urls import re_path

from .views import ManagerPersonView, PersonTableView, MusicianCRUDView

urlpatterns = [
    re_path(r'^person/', ManagerPersonView.as_view(), name='person_manager'),
    re_path(r'^musician/', MusicianCRUDView.as_view(), name='musician_manager'),
    re_path(r'^person-table/', PersonTableView.as_view(), name='person_table'),
]
