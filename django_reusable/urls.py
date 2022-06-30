from django.urls import include

from django_reusable import views, error_tracker_views
from django.conf.urls import url
app_name = "django_reusable"


urlpatterns = [
    url(r'^ajax-callback-handler/(?P<pk>\d+)/(?P<name>[\w-]+)/$',
        views.ajax_callback_handler, name='ajax_callback_handler'),
    url(r'^errors/', include([
        url(r'^$', error_tracker_views.view_list, name="errors"),
        url(r'^(?P<rhash>[\w-]+)/delete$', error_tracker_views.delete_exception, name='delete_error'),
        url(r'^(?P<rhash>[\w-]+)$', error_tracker_views.detail, name='view_error'),
    ])),
]
