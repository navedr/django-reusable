import builtins
import itertools
import re
import sys
import traceback
import types
from hashlib import sha256
from io import StringIO

import six
from django.http import QueryDict, RawPostDataException

from .logging import PrintLogger


def format_frame(x, max_elements, max_string, max_recursion, masking=None):
    """
    Return a formatted frame for storing in the database.
    :param x: frame key/value pair
    :param max_elements: Maximum number of elements to be formatted
    :param max_string: Maximum length for string data types in output
    :param max_recursion: Maximum recursion depth used in structure like dict
    :param masking: Used to mask a key/value
    :return: string of formatted value
    """

    def _per_element(i):
        return format_frame(i, max_elements, max_string, max_recursion - 1, masking=masking)

    def _per_dict_element(i):
        masked = False
        val = None
        if masking:
            masked, val = masking(i[0])
        return "%r : %s" % (i[0], val if masked else _per_element(i[1]))

    def _it_to_string(fmt, it, per_element=_per_element):
        if max_recursion <= 0:
            return fmt % "..."

        it = iter(it)

        s = ', '.join(per_element(i) for i in itertools.islice(it, max_elements))
        try:
            it.__next__()
        except AttributeError:
            try:
                next(it)
            except StopIteration:
                return fmt % s
        except StopIteration:
            return fmt % s

        # Add ellipsis indicating truncation.
        # Correctly handle the corner case of max_elements == 0.
        return fmt % (s + ", ..." if s else "...")

    if x is builtins.__dict__:
        return "<builtins>"
    elif type(x) == dict:
        return _it_to_string("{%s}", sorted(x.items()), per_element=_per_dict_element)
    elif type(x) == list:
        return _it_to_string("[%s]", x)
    elif type(x) == tuple:
        return _it_to_string("(%s)" if len(x) != 1
                                       or max_recursion <= 0
                                       or max_elements <= 0
                             else "(%s,)", x)
    elif type(x) == set:
        return _it_to_string("set([%s])", sorted(x))
    elif type(x) == frozenset:
        return _it_to_string("frozenset([%s])", sorted(x))
    elif isinstance(x, six.string_types) and max_string < len(x):
        return repr(x[:max_string] + "...")
    elif type(x) == QueryDict:
        x = x.dict()
        return _it_to_string("QueryDict({%s})", sorted(x.items()),
                             per_element=_per_dict_element)
    else:
        try:
            if issubclass(x, dict):
                x = dict(x)
                return _it_to_string("Dict({%s})", sorted(x.items()),
                                     per_element=_per_dict_element)
        except TypeError:
            pass
        return repr(x)


def can_be_skipped(key, value):
    # Identifiers that are all uppercase are almost always constants.
    if re.match('[A-Z0-9_]+$', key):
        return True
    # dunder functions.
    if re.match('__.*__$', key):
        return True
    if callable(value):
        return True
    if isinstance(value, types.ModuleType):
        return True
    return False


def format_exception(tb, max_elements=1000,
                     max_string=10000, max_recursion=100,
                     masking=None):
    """
    :param tb: traceback
    :param max_elements:  Maximum number of elements to be printed
    :param max_string: Max string length in print
    :param max_recursion: Recursive printing in case of dict or other items
    :param masking: Masking rule for key/value pair
    :return: a formatted string

    Walk over all the frames and get the local variables from the frame and format them using format function and
    write to the stringIO based file.
    """
    stack = []
    t = tb
    while t:
        stack.append(t.tb_frame)
        t = t.tb_next
    buf = StringIO()
    w = buf.write
    # Go through each frame and format them to get final string
    for frame in stack:
        w('\n  File "%s", line %s, in %s\n' % (frame.f_code.co_filename,
                                               frame.f_lineno,
                                               frame.f_code.co_name))
        local_vars = frame.f_locals.items()
        local_vars = sorted(local_vars)
        for key, value in local_vars:
            if can_be_skipped(key, value):
                continue

            w("    %20s = " % key)
            masked = False
            if masking:
                masked, val = masking(key)
                if masked:
                    w(val)
            if not masked:
                try:
                    w(format_frame(value, max_elements, max_string, max_recursion,
                                   masking=masking))
                except Exception:
                    exc_class = sys.exc_info()[0]
                    w("<%s raised while printing value>" % exc_class)
            w("\n")
    w("\n")
    w(''.join(traceback.format_tb(tb)))
    op = buf.getvalue()
    buf.close()
    return op


def get_context_detail(request, masking, context_builder,
                       additional_context):
    ty, val, tb = sys.exc_info()
    frames = traceback.format_exception(ty, val, tb)
    traceback_str = format_exception(tb, masking=masking)
    frame_str = ''.join(frames)
    rhash = sha256(str.encode(frame_str, "UTF-8")).hexdigest()
    request_data = context_builder.get_context(request, masking=masking,
                                               additional_context=additional_context)
    return ty, frames, frame_str, traceback_str, rhash, request_data


def get_exception_name(e):
    return str(e).replace("'>", "").replace("<class '", "").replace("<type 'exceptions.", "")


def get_context_dict(headers=None, context=None, form=None, args=None, masking=None):
    request_data = dict()
    form = form or {}
    headers = headers or {}
    args = args or {}
    context = context or {}
    if len(context) != 0:
        request_data['context'] = context
    if masking:
        for key in form:
            masked, value = masking(key)
            if masked:
                form[key] = value
        for key in headers:
            masked, value = masking(key)
            if masked:
                headers[key] = value
    if len(headers) != 0:
        request_data['headers'] = headers
    if len(args) != 0:
        request_data['args'] = args
    if len(form) != 0:
        request_data['form'] = form
    return request_data


class DefaultDjangoContextBuilder(object):
    """
    Default request builder, this records, form data, header and URL parameters and mask them if necessary
    """

    @staticmethod
    def _get_form_data(request):
        form = {}
        if request is None:
            return form
        post = request.POST
        if post is None or len(post) == 0:
            body = None
            try:
                body = request.data
            except AttributeError:
                try:
                    body = request.body
                except RawPostDataException:
                    pass
            if body is not None:
                if len(body) > 0:
                    import json
                    try:
                        form = json.loads(body, encoding="UTF-8")
                    except Exception:
                        form = {'data': body}
        else:
            form = post.dict()
        return form

    @staticmethod
    def _get_headers(request):
        if request is not None:
            try:
                headers = request.headers.dict()
            except AttributeError:
                regex = re.compile('^HTTP_')
                headers = dict((regex.sub('', header), value) for (header, value)
                               in request.META.items() if header.startswith('HTTP_'))
            return headers

    @staticmethod
    def _get_args(request):
        if request is not None:
            return request.GET.dict()

    def get_context(self, request, masking=None, additional_context=None):
        return str(get_context_dict(headers=self._get_headers(request),
                                    form=self._get_form_data(request),
                                    args=self._get_args(request),
                                    context=additional_context,
                                    masking=masking))


# noinspection PyMethodMayBeStatic
class ErrorTracker(object):
    """
     ErrorTracker class, this is responsible for capturing exceptions and
     sending notifications and taking other actions,
    """

    # @staticmethod
    # def _send_notification(request, message, exception, error):
    #     """
    #     Send notification to the list of entities or call the specific methods
    #     :param request: request object
    #     :param message: message having frame details
    #     :param exception: exception that's triggered
    #     :param error:  error model object
    #     :return: None
    #     """
    #     if notifier is None:
    #         return
    #     if request is not None:
    #         method = request.method
    #         url = request.get_full_path()
    #     else:
    #         method = ""
    #         url = ""
    #     subject = get_notification_subject(APP_ERROR_SUBJECT_PREFIX,
    #                                        method, url, exception)
    #     notifier.notify(request,
    #                     error,
    #                     email_subject=subject,
    #                     email_body=message,
    #                     from_email=APP_ERROR_EMAIL_SENDER,
    #                     recipient_list=APP_ERROR_RECIPIENT_EMAIL)
    #
    # @staticmethod
    # def _raise_ticket(request, error):
    #     if ticketing is None:
    #         return
    #     ticketing.raise_ticket(request, error)
    #
    # @staticmethod
    # def _post_process(request, frame_str, frames, error):
    #     if request is not None:
    #         message = ('URL: %s' % request.path) + '\n\n'
    #     else:
    #         message = ""
    #     message += frame_str
    #     ErrorTracker._send_notification(request, message, frames[-1][:-1], error)
    #     ErrorTracker._raise_ticket(request, error)

    def capture_exception(self, request=None, exception=None, additional_context=None):
        """
        Record the exception details and do post processing actions. this method can be used to track any exceptions,
        even those are being excepted using try/except block.
        :param request:  request object
        :param exception: what type of exception has occurred
        :param additional_context: any additional context
        :return:  None
        """
        logger = PrintLogger("ErrorTracker")
        try:
            path, host, method = ((request.path, request.META.get('HTTP_HOST', ''), request.method)
                                  if request else ('', '', ''))
            print(path, host, method)

            ty, frames, frame_str, traceback_str, rhash, request_data = \
                get_context_detail(request, None, DefaultDjangoContextBuilder(),
                                   additional_context=additional_context)
            from .models import Error
            error = Error.create_or_update_entity(rhash,
                                                  host,
                                                  path,
                                                  method,
                                                  str(request_data),
                                                  f'{get_exception_name(ty)}("{exception}")',
                                                  traceback_str)
            # ErrorTracker._post_process(request, frame_str, frames, error)
        except:
            logger.error("error while capturing error", traceback.format_exc())
