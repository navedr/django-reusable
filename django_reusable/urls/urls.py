from django.urls import include

from django_reusable import views
from django_reusable.constants import URLNames
from django_reusable.error_tracker import views as error_tracker_views
from django.conf.urls import url
app_name = "django_reusable"

urlpatterns = [
    url(r'^ajax-callback-handler/(?P<pk>\d+)/(?P<name>[\w-]+)/$',
        views.ajax_callback_handler, name=URLNames.AJAX_CALLBACK_HANDLER),
    url(r'^is-user-authenticated/$', views.is_user_authenticated, name=URLNames.IS_USER_AUTHENTICATED),
    url(r'^errors/', include([
        url(r'^$', error_tracker_views.view_list, name="errors"),
        url(r'^(?P<rhash>[\w-]+)/delete$', error_tracker_views.delete_exception, name='delete_error'),
        url(r'^(?P<rhash>[\w-]+)$', error_tracker_views.detail, name='view_error'),
    ])),
]
