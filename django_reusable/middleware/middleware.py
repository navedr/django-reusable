import threading
from re import compile
from urllib.parse import quote_plus

from django.conf import settings
from django.http import HttpResponseRedirect

from django_reusable.constants import URLNames
from django_reusable.error_tracker.error_tracker import ErrorTracker
from django_reusable.urls.utils import get_app_and_url_name

try:
    from django.utils.deprecation import MiddlewareMixin
except ImportError:
    MiddlewareMixin = object


class LoginRequiredMiddleware:
    """
    Middleware that ensures the user is authenticated before accessing certain views.

    Attributes:
        get_response (callable): The next middleware or view in the chain.
        login_url (str): The URL to redirect to for login.
        open_urls (list): A list of URLs that are accessible without authentication.
    """

    def __init__(self, get_response):
        """
        Initializes the middleware with the given response handler.

        Args:
            get_response (callable): The next middleware or view in the chain.
        """
        self.get_response = get_response
        self.login_url = settings.LOGIN_URL
        self.open_urls = [self.login_url] + [u.replace('^', '^/') for u in getattr(settings, 'OPEN_URLS', {}).values()]
        self.open_urls = list(map(compile, self.open_urls))

    def __call__(self, request):
        """
        Processes the request and redirects to the login page if the user is not authenticated.

        Args:
            request (HttpRequest): The current request object.

        Returns:
            HttpResponse: The response object.
        """
        path = request.path_info
        app_name, url_name = get_app_and_url_name(request)
        should_redirect_to_login = (not request.user.is_authenticated and
                                    not any(m.match(path) for m in self.open_urls) and
                                    not (app_name == 'django_reusable' and url_name == URLNames.IS_USER_AUTHENTICATED))
        if should_redirect_to_login:
            next_page = '%s?%s' % (path, request.META['QUERY_STRING'])
            return HttpResponseRedirect('%s?next=%s' % (self.login_url, quote_plus(next_page)))

        return self.get_response(request)


class CRequestMiddleware(MiddlewareMixin):
    """
    Middleware that provides storage for the "current" request object, allowing
    access to it from anywhere in the project.
    """
    _requests = {}

    def process_request(self, request):
        """
        Stores the current request.

        Args:
            request (HttpRequest): The current request object.
        """
        self.__class__.set_request(request)

    def process_response(self, request, response):
        """
        Deletes the current request to avoid memory leaks.

        Args:
            request (HttpRequest): The current request object.
            response (HttpResponse): The response object.

        Returns:
            HttpResponse: The response object.
        """
        self.__class__.del_request()
        return response

    @classmethod
    def get_request(cls, default=None):
        """
        Retrieves the request object for the current thread.

        Args:
            default (optional): The default value to return if no request is found.

        Returns:
            HttpRequest: The current request object or the default value.
        """
        return cls._requests.get(threading.current_thread(), default)

    @classmethod
    def set_request(cls, request):
        """
        Saves the given request into storage for the current thread.

        Args:
            request (HttpRequest): The current request object.
        """
        cls._requests[threading.current_thread()] = request

    @classmethod
    def del_request(cls):
        """
        Deletes the request that was stored for the current thread.
        """
        cls._requests.pop(threading.current_thread(), None)


class ExceptionTrackerMiddleware(ErrorTracker):
    """
    Middleware that tracks exceptions and captures them using an error tracker.

    Attributes:
        get_response (callable): The next middleware or view in the chain.
    """

    def __init__(self, get_response):
        """
        Initializes the middleware with the given response handler.

        Args:
            get_response (callable): The next middleware or view in the chain.
        """
        self.get_response = get_response

    def __call__(self, request):
        """
        Processes the request and returns the response.

        Args:
            request (HttpRequest): The current request object.

        Returns:
            HttpResponse: The response object.
        """
        return self.get_response(request)

    def process_exception(self, request, exception):
        """
        Processes exceptions and captures them using the error tracker.

        Args:
            request (HttpRequest): The current request object.
            exception (Exception): The exception that occurred.
        """
        if exception is None:
            return
        self.capture_exception(request, exception)


# Use this object to track errors in the case of custom failures, where try/except is used
error_tracker = ErrorTracker()
