from django_reusable import views

try:
    from django.conf.urls import url
except ImportError:
    from django.conf.urls.defaults import url


urlpatterns = [
    url(r'^ajax-callback-handler/(?P<pk>\d+)/(?P<name>[\w-]+)/$',
        views.ajax_callback_handler, name='ajax_callback_handler'),
]
