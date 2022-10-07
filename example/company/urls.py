from django.conf.urls import url

from .views import ManagerPersonView, PersonTableView, MusicianCRUDView

urlpatterns = [
    url(r'^person/', ManagerPersonView.as_view(), name='person_manager'),
    url(r'^musician/', MusicianCRUDView.as_view(), name='musician_manager'),
    url(r'^person-table/', PersonTableView.as_view(), name='person_table'),
]
