from django.urls import include, re_path

from django_reusable import views
from django_reusable.constants import URLNames
from django_reusable.error_tracker import views as error_tracker_views
app_name = "django_reusable"

urlpatterns = [
    re_path(r'^ajax-callback-handler/(?P<pk>\d+)/(?P<name>[\w-]+)/$',
        views.ajax_callback_handler, name=URLNames.AJAX_CALLBACK_HANDLER),
    re_path(r'^is-user-authenticated/$', views.is_user_authenticated, name=URLNames.IS_USER_AUTHENTICATED),
    re_path(r'^admin-utils-callback/$', views.admin_utils_callback, name=URLNames.ADMIN_UTILS_JS_CALLBACK),
    re_path(r'^log/$', views.log, name=URLNames.LOG),
    re_path(r'^errors/', include([
        re_path(r'^$', error_tracker_views.view_list, name="errors"),
        re_path(r'^(?P<rhash>[\w-]+)/delete$', error_tracker_views.delete_exception, name='delete_error'),
        re_path(r'^(?P<rhash>[\w-]+)$', error_tracker_views.detail, name='view_error'),
    ])),
]
