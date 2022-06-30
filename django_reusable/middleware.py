import threading
from re import compile
from urllib.parse import quote_plus

from django.conf import settings
from django.http import HttpResponseRedirect

from django_reusable.error_tracker import ErrorTracker

try:
    from django.utils.deprecation import MiddlewareMixin
except ImportError:
    MiddlewareMixin = object


class LoginRequiredMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response
        self.login_url = settings.LOGIN_URL
        self.open_urls = [self.login_url] + [u.replace('^', '^/') for u in getattr(settings, 'OPEN_URLS', {}).values()]
        self.open_urls = list(map(compile, self.open_urls))

    def __call__(self, request):
        path = request.path_info
        if not request.user.is_authenticated and not any(m.match(path) for m in self.open_urls):
            next_page = '%s?%s' % (path, request.META['QUERY_STRING'])
            return HttpResponseRedirect('%s?next=%s' % (self.login_url, quote_plus(next_page)))

        return self.get_response(request)


class CRequestMiddleware(MiddlewareMixin):
    """
    Provides storage for the "current" request object, so that code anywhere
    in your project can access it, without it having to be passed to that code
    from the view.
    """
    _requests = {}

    def process_request(self, request):
        """
        Store the current request.
        """
        self.__class__.set_request(request)

    def process_response(self, request, response):
        """
        Delete the current request to avoid leaking memory.
        """
        self.__class__.del_request()
        return response

    @classmethod
    def get_request(cls, default=None):
        """
        Retrieve the request object for the current thread, or the optionally
        provided default if there is no current request.
        """
        return cls._requests.get(threading.current_thread(), default)

    @classmethod
    def set_request(cls, request):
        """
        Save the given request into storage for the current thread.
        """
        cls._requests[threading.current_thread()] = request

    @classmethod
    def del_request(cls):
        """
        Delete the request that was stored for the current thread.
        """
        cls._requests.pop(threading.current_thread(), None)


class ExceptionTrackerMiddleware(ErrorTracker):
    """
    Error tracker middleware that's invoked in the case of exception occurs,
    this should be placed at the end of Middleware lists
    """

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        return self.get_response(request)

    def process_exception(self, request, exception):
        if exception is None:
            return
        self.capture_exception(request, exception)


# use this object to track errors in the case of custom failures, where try/except is used
error_tracker = ErrorTracker()
