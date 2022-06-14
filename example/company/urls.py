from django.conf.urls import url

from .views import ManagerPersonView

urlpatterns = [
    url(r'^person/', ManagerPersonView.as_view(), name='person_manager'),
]
