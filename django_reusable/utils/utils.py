import csv
import json
import locale
import math
import os
import random
import uuid
from collections import namedtuple, OrderedDict
from datetime import datetime, date
from tempfile import NamedTemporaryFile

from django import forms
from django.conf import settings
from django.core.exceptions import ValidationError
from django.core.serializers.json import DjangoJSONEncoder
from django.core.validators import validate_email
from django.db import connection
from django.db.models.fields.files import FieldFile
from django.db.models.fields.files import FileField
from django.http import HttpResponse, JsonResponse
from django.template import Context, Template
from django.template import engines
from django.urls import resolve
from django.utils import encoding
from django.utils.encoding import Promise, force_str
from django.utils.safestring import mark_safe
from django.views.generic import TemplateView
from pytz import timezone, utc

from .conversion import is_number, is_int

try:
    locale.setlocale(locale.LC_ALL, '')
except locale.Error:
    pass


def global_request():
    """Return the current Django HTTP request from thread-local middleware.

    Returns:
        HttpRequest: The current request object, or None if unavailable.
    """
    from django_reusable.middleware import CRequestMiddleware
    return CRequestMiddleware.get_request()


def current_user():
    """Return the currently authenticated user from the active request.

    Returns:
        User: The current Django auth user.
    """
    return global_request().user


def truncate(value, digits):
    """Truncate a numeric value to a given number of decimal places (no rounding).

    Args:
        value: Numeric value to truncate.
        digits: Number of decimal places to keep.

    Returns:
        float: The truncated value.
    """
    return int(value * math.pow(10, digits)) / math.pow(10, digits)


def fix_decimal_product_no(value):
    """Strip trailing ``.0`` from a numeric string representation.

    Args:
        value: Value to clean.

    Returns:
        str: Cleaned string.
    """
    if str(value)[-2:] == '.0':
        return str(value)[:-2]
    else:
        return str(value)


def strip_non_alpha_numeric(string):
    """Remove all non-alphanumeric characters from a string.

    Args:
        string: Input string to cleanse.

    Returns:
        str: String with only alphanumeric characters.
    """
    import re
    cleansed_string = re.sub("[^0-9A-Za-z]", "", string)
    return cleansed_string


def to_json(obj):
    """Serialize an object to a JSON string using its ``__dict__``.

    Args:
        obj: Any object with a ``__dict__`` attribute.

    Returns:
        str: Pretty-printed JSON string.
    """
    return json.dumps(obj, default=lambda o: o.__dict__, sort_keys=True, indent=4)


def _json_object_hook(d): return namedtuple('X', d.keys())(*d.values())


def from_json(data):
    """Deserialize a JSON string into nested namedtuples for attribute access.

    Args:
        data: JSON string.

    Returns:
        namedtuple: Parsed object with attribute-style access.
    """
    return json.loads(data, object_hook=_json_object_hook)


def save_and_return_bytes(wb):
    """Save an openpyxl Workbook to a temp file and return its bytes.

    Args:
        wb: An openpyxl Workbook instance.

    Returns:
        bytes: The workbook file contents.
    """
    file_path = get_temp_file_path()
    wb.save(file_path)
    return get_bytes_and_delete(file_path)


def get_bytes_and_delete(file_path):
    """Read a file as bytes and then delete it.

    Args:
        file_path: Absolute path to the file.

    Returns:
        bytes: The file contents.
    """
    data = get_bytes(file_path)
    delete_file(file_path)
    return data


def delete_file(file_path):
    """Delete a file, returning True on success and False on failure.

    Args:
        file_path: Absolute path to the file.

    Returns:
        bool: True if deleted, False if an error occurred.
    """
    try:
        os.remove(file_path)
        return True
    except:
        return False


def rename_file(old_name, new_name):
    """Rename a file.

    Args:
        old_name: Current file path.
        new_name: New file path.
    """
    os.rename(old_name, new_name)


def move_file(source, destination):
    """Move a file from source to destination.

    Args:
        source: Current file path.
        destination: Target file path.
    """
    os.rename(source, destination)


def get_bytes(file_path):
    """Read and return a file's contents as bytes.

    Args:
        file_path: Absolute path to the file.

    Returns:
        bytes: The raw file contents.
    """
    in_file = open(file_path, "rb")  # opening for [r]eading as [b]inary
    data = in_file.read()  # if you only wanted to read 512 bytes, do .read(512)
    in_file.close()
    return data


def get_temp_file_path(extn=None):
    """Generate a unique temp file path under ``MEDIA_ROOT/tmp/``.

    Args:
        extn: Optional file extension (without dot).

    Returns:
        str: Absolute path to the temp file.
    """
    import uuid
    file_name = str(uuid.uuid4()) + (f'.{extn}' if extn else '')
    file_path = os.path.join(settings.MEDIA_ROOT, "tmp", file_name)
    return file_path


def xstr(s, default=''):
    """Convert a value to string, returning a default if None.

    Args:
        s: Value to convert.
        default: Value to return when s is None. Defaults to ``''``.

    Returns:
        str: String representation of s, or default.
    """
    return default if s is None else str(s)


def prepend_project_directory(directory_name):
    return os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), directory_name)


def unicode_to_string(x):
    """Convert a unicode value to an ASCII string, ignoring unencodable characters.

    Args:
        x: Value to convert.

    Returns:
        str: ASCII string.
    """
    return encoding.smart_str(x, encoding='ascii', errors='ignore')


class CustomEncoder(DjangoJSONEncoder):
    """Extended JSON encoder that handles Django FieldFile and lazy translation strings.

    Falls back to ``force_str`` for any object the parent encoder cannot handle.
    """

    def default(self, o):
        if isinstance(o, FieldFile):
            return o.url if o.name else ''
        elif isinstance(o, Promise):
            return force_str(o)
        else:
            try:
                return super().default(o)
            except:
                return force_str(o)


def coalesce(value, replace):
    """Return ``value`` if not None, otherwise return ``replace``.

    Args:
        value: Primary value.
        replace: Fallback value.

    Returns:
        The non-None value.
    """
    if value is None:
        return replace
    return value


def query_to_dicts(query_string, params=None):
    """Execute a raw SQL query and yield each row as a dict.

    Args:
        query_string: Raw SQL query string.
        params: Optional query parameters for parameterized queries.

    Yields:
        dict: Row data keyed by column name.
    """
    cursor = connection.cursor()
    cursor.execute(query_string, params)
    col_names = [desc[0] for desc in cursor.description]
    while True:
        row = cursor.fetchone()
        if row is None:
            break
        row_dict = dict(zip(col_names, row))
        yield row_dict
    cursor.close()
    return


def query_to_lists(query_string, col_index=None, params=None):
    """Execute a raw SQL query and yield rows as tuples, or a single column value.

    Args:
        query_string: Raw SQL query string.
        col_index: If provided, yield only the value at this column index.
        params: Optional query parameters for parameterized queries.

    Yields:
        tuple or value: Full row tuple, or the single column value if col_index is set.
    """
    cursor = connection.cursor()
    cursor.execute(query_string, params)
    while True:
        row = cursor.fetchone()
        if row is None:
            break
        yield row[col_index] if col_index is not None else row
    cursor.close()
    return


def field_html(field, name):
    """Render a Django form field to its HTML representation.

    Args:
        field: A Django form field instance.
        name: The field name to use in the rendered HTML.

    Returns:
        str: The rendered HTML for the field.
    """
    class TempForm(forms.Form):
        def __init__(self, *args, **kwargs):
            super(TempForm, self).__init__(*args, **kwargs)
            self.fields[name] = field

    form = TempForm()
    t = Template("{{form.%s}}" % name)
    c = Context({'form': form})
    return t.render(c)


def get_model_fields(model):
    """Return a sorted list of ``(field_name, verbose_name)`` tuples for a model.

    Includes both model fields and properties, excluding common defaults like
    ``id``, ``modified``, ``pk``, and ``file``.

    Args:
        model: Django model class.

    Returns:
        list[tuple[str, str]]: Sorted (name, label) pairs.
    """
    field_excludes = ['id', 'modified']
    property_excludes = ['pk', 'file', 'country'] + [field.name for field in model._meta.fields]
    fields = [(field.name, field.verbose_name.title() if field.verbose_name.islower() else field.verbose_name)
              for field in model._meta.fields if field.name not in field_excludes and not isinstance(field, FileField)]
    property_names = [(name, name.replace('_', ' ').title()) for name in dir(model)
                      if name not in property_excludes
                      and isinstance(getattr(model, name), property)]
    fields.extend(property_names)
    return sorted(fields, key=lambda k: k[1].lower())


class TempFiles(object):
    """Context manager for a group of temporary files that are closed on exit."""

    def __init__(self, *files):
        self.files = files

    def __exit__(self, exc_type, exc_val, exc_tb):
        for f in self.files:
            f.close()

    def __enter__(self):
        return self.files


class TempFilesFromBytes(TempFiles):
    """Context manager that writes byte sequences to temp files for the duration of the block."""

    def __init__(self, *file_bytes):
        files = []
        for file_byte in file_bytes:
            f = NamedTemporaryFile()
            f.write(file_byte)
            f.close()
        super().__init__(*files)


class TempFile(object):
    """Context manager for a single temporary file that is closed on exit."""

    def __init__(self, file):
        self.file = file

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.file.close()

    def __enter__(self):
        return self.file


def get_wb_response_from_bytes(data_bytes, file_name):
    """Create an HttpResponse for downloading an Excel (.xlsx) file.

    Args:
        data_bytes: The workbook file contents as bytes.
        file_name: The download file name.

    Returns:
        HttpResponse: Configured for xlsx download.
    """
    response = HttpResponse(data_bytes,
                            content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
    response["X-Accel-Buffering"] = "no"
    response['Content-Disposition'] = 'attachment; filename=%s' % file_name
    return response


def get_zip_response_from_bytes(data_bytes, file_name):
    """Create an HttpResponse for downloading a ZIP file.

    Args:
        data_bytes: The ZIP file contents as bytes.
        file_name: The download file name.

    Returns:
        HttpResponse: Configured for zip download.
    """
    response = HttpResponse(data_bytes,
                            content_type="application/zip")
    response["X-Accel-Buffering"] = "no"
    response['Content-Disposition'] = 'attachment; filename=%s' % file_name
    return response


def get_wb_response(wb, file_name):
    """Save an openpyxl Workbook and return it as an xlsx download response.

    Args:
        wb: An openpyxl Workbook instance.
        file_name: The download file name.

    Returns:
        HttpResponse: Configured for xlsx download.
    """
    return get_wb_response_from_bytes(save_and_return_bytes(wb), file_name)


def render_to_string_from_source(template_source, context_dict=None):
    """Render a Django template string with the given context.

    Args:
        template_source: Django template source string.
        context_dict: Optional context dictionary for rendering.

    Returns:
        str: The rendered template output.
    """
    t = engines['django'].from_string(template_source)
    return t.render(context_dict)


def sum_by_tuple_element_in_list(input_list, decimal_places=None):
    """Sum values in a list of 2-tuples, grouped by the first element.

    Args:
        input_list: List of ``(key, value)`` tuples
            (e.g. ``[('Jan 2015', 1544.4), ('Jan 2015', 200.0)]``).
        decimal_places: Optional number of decimal places to round sums to.

    Yields:
        tuple: ``(key, summed_value)`` for each distinct key, preserving insertion order.
    """
    distinct_group_values = OrderedDict(input_list).keys()
    for group in distinct_group_values:
        sum_of_elements = sum(val for (key, val) in input_list if key == group)
        if decimal_places is not None:
            sum_of_elements = round(sum_of_elements, decimal_places)
        yield (group, sum_of_elements)


def median(input_list):
    """Calculate the median value of a numeric list.

    Args:
        input_list: List of numbers.

    Returns:
        float: The median value.
    """
    quotient, remainder = divmod(len(input_list), 2)
    if remainder:
        return sorted(input_list)[quotient]
    return float(sum(sorted(input_list)[quotient - 1:quotient + 1]) / 2)


def mode(input_list):
    """Return the most frequently occurring value in a list, or 0 if no repeats.

    Args:
        input_list: List of values.

    Returns:
        The mode value, or 0 if all values are unique.
    """
    m = max([input_list.count(a) for a in input_list])
    return [x for x in input_list if input_list.count(x) == m][0] if m > 1 else 0


def math_range(input_list):
    """Return the range (max - min) of a numeric list.

    Args:
        input_list: List of numbers.

    Returns:
        float: The range, or 0 for an empty list.
    """
    return max(input_list) - min(input_list) if input_list else 0


def get_subclasses(classes, level=0):
    """Recursively collect all subclasses of the given class(es).

    Args:
        classes: A class or list of classes.
        level: Recursion depth (used internally). Defaults to 0.

    Returns:
        list: All classes including their subclasses at every depth.
    """
    # for convenience, only one class can can be accepted as argument
    # converting to list if this is the case
    if not isinstance(classes, list):
        classes = [classes]

    if level < len(classes):
        classes += classes[level].__subclasses__()
        return get_subclasses(classes, level + 1)
    else:
        return classes


def image(instance, file_name, image_url):
    if image_url:
        urls = [image_url, instance.find_full_image_url(file_name)]
        return mark_safe('<br>Full Image:<br>'.join([
            "<a href='%(image_url)s' target='_blank'><img style='max-width: 100px' src='%(image_url)s' alt='Image 1'"
            " /></a>" % {'image_url': url} for url in urls if url]))


def get_pdf_response_from_file(pdf, file_name):
    """Create an HttpResponse for inline PDF display.

    Args:
        pdf: PDF file contents as bytes.
        file_name: File name (without extension) for the Content-Disposition header.

    Returns:
        HttpResponse: Configured for inline PDF display.
    """
    response = HttpResponse(pdf, content_type='application/pdf')
    response["X-Accel-Buffering"] = "no"
    response['Content-Disposition'] = 'inline; filename=%s.pdf' % file_name
    return response


def format_as_currency(value, decimal_precision=2, currency_symbol='$'):
    """Format a numeric value as a currency string with HTML markup.

    Negative values are wrapped in a ``text-danger`` span with parentheses.

    Args:
        value: Numeric value to format.
        decimal_precision: Number of decimal places. Defaults to 2.
        currency_symbol: Currency symbol prefix. Defaults to ``'$'``.

    Returns:
        SafeString: HTML-safe currency string, or the original value if not numeric.
    """
    if value is None:
        return value
    if not is_number(value):
        return value
    value = float(value)
    is_negative = value < 0
    display_format = f'<span class="text-danger">({currency_symbol}%s)</span>' if is_negative else f'{currency_symbol}%s'
    decimal_precision = decimal_precision if is_int(decimal_precision) and decimal_precision >= 0 else 2
    return mark_safe(display_format % ('%s' % ('{:20,.%sf}' % decimal_precision).format(math.fabs(value)).strip()))


def list_to_table(data, table_class='', has_header=False):
    """Convert a 2D list into an HTML table string.

    Args:
        data: List of lists (rows of cell values).
        table_class: CSS class(es) for the ``<table>`` element.
        has_header: If True, treat the first row as ``<thead>``.

    Returns:
        str: HTML table markup.
    """
    def _get_table_part(rows, group_tag, cell_tag):
        _html = ['<%s>' % group_tag]
        for index, row in enumerate(rows):
            _html.extend(['<tr>'] + imap(lambda x: '<{t}>{v}</{t}>'.format(t=cell_tag, v=x), row) + ['</tr>'])
        _html.append('</%s>' % group_tag)
        return _html

    html = ['<table class="%s">' % table_class]
    if has_header:
        html.extend(_get_table_part(data[:1], 'thead', 'th'))
        data = data[1:]
    html.extend(_get_table_part(data, 'tbody', 'td'))
    html.append('</table>')
    return ''.join(html)


def list_to_ul(iterable, css_class_name=''):
    """Convert an iterable into an HTML unordered list.

    Args:
        iterable: Items to render as ``<li>`` elements.
        css_class_name: Optional CSS class for the ``<ul>``.

    Returns:
        SafeString: HTML ``<ul>`` markup, or empty string if iterable is falsy.
    """
    if not iterable:
        return ''
    return mark_safe(f'''<ul class="{css_class_name}">{"".join(f"<li>{value}</li>" for value in iterable)}</ul>''')


def get_id_from_url(request):
    resolved = resolve(request.path_info)
    if resolved.args:
        return resolved.args[0]
    if resolved.kwargs:
        return resolved.kwargs['object_id']
    return None


def get_count_dict(iterable, by_property=None):
    """Count occurrences of elements or element properties in an iterable.

    Args:
        iterable: Sequence of items to count.
        by_property: Optional attribute name (str) or list of attribute names
            to group by. Supports dict key access as well.

    Returns:
        dict: Mapping of element (or property value) to count.

    Example:
        ```python
        get_count_dict(['a', 'b', 'a'])  # {'a': 2, 'b': 1}
        ```
    """
    count_dict = dict()
    for el in iterable:
        if isinstance(by_property, (list, tuple)):
            key = tuple(imap(lambda p: getattr(el, p), by_property))
        else:
            if by_property:
                key = el.get(by_property, None) if isinstance(el, dict) else getattr(el, by_property)
            else:
                key = el
        val = count_dict.get(key, 0) + 1
        count_dict[key] = val
    return count_dict


def ifilter(fn, iterable):
    """Eager version of ``filter`` that returns a list instead of an iterator.

    Args:
        fn: Predicate function.
        iterable: Items to filter.

    Returns:
        list: Filtered items.
    """
    return list(filter(fn, iterable))


def imap(fn, iterable):
    """Eager version of ``map`` that returns a list instead of an iterator.

    Args:
        fn: Mapping function.
        iterable: Items to map over.

    Returns:
        list: Mapped results.
    """
    return list(map(fn, iterable))


def is_user_admin():
    return current_user().has_perm('user.is_admin')


def get_property(obj, name, fn):
    if not hasattr(obj, name):
        setattr(obj, name, fn())
    return getattr(obj, name)


def humane_currency(value):
    """Format a number as a human-readable currency string (e.g. ``$1.5M``).

    Args:
        value: Numeric value to format.

    Returns:
        str: Abbreviated currency string, or None if value is None.
    """
    if value is None:
        return value
    return f'${humane_number(value)}'


def humane_number(value):
    """Format a number with magnitude suffix (K, M, B, T).

    Args:
        value: Numeric value to format.

    Returns:
        str: Abbreviated number string (e.g. ``'1.5M'``), or None if value is None.
    """
    if value is None:
        return value
    value = float('{:.3g}'.format(value))
    magnitude = 0
    while abs(value) >= 1000:
        magnitude += 1
        value /= 1000.0
    return '{}{}'.format('{:f}'.format(value).rstrip('0').rstrip('.'), ['', 'K', 'M', 'B', 'T'][magnitude])


class JSONResponseMixin:
    """Mixin that renders a JSON response from the template view context.

    Provides ``render_to_json_response`` and ``get_data`` methods for use
    with Django class-based views.
    """

    def render_to_json_response(self, context, **response_kwargs):
        """Return a JsonResponse with the serialized context.

        Args:
            context: View context data.
            **response_kwargs: Additional kwargs passed to JsonResponse.

        Returns:
            JsonResponse: The JSON HTTP response.
        """
        return JsonResponse(
            self.get_data(context),
            **response_kwargs, safe=False
        )

    def get_data(self, context):
        """Return the data to be serialized as JSON. Override to customize.

        Args:
            context: View context data.

        Returns:
            The context object (default implementation).
        """
        return context


class JSONView(JSONResponseMixin, TemplateView):
    """A TemplateView that returns JSON instead of rendered HTML."""

    def render_to_response(self, context, **response_kwargs):
        return self.render_to_json_response(context, **response_kwargs)


def get_random_color_hex():
    r = lambda: random.randint(0, 255)
    return '#%02X%02X%02X' % (r(), r(), r())


def write_text_to_file(content, file_path):
    with open(file_path, 'w') as f:
        f.write(content)


def group_by_property(iterable, prop=None, prop_fn=None):
    """Group items by an attribute or a key function.

    Args:
        iterable: Items to group.
        prop: Attribute name to group by.
        prop_fn: Callable that extracts the group key from an item.

    Returns:
        dict: Mapping of group key to list of items.

    Example:
        ```python
        group_by_property(users, prop='department')
        ```
    """
    if not prop and not prop_fn:
        return dict()
    group = dict()
    for item in iterable:
        key = getattr(item, prop) if prop else prop_fn(item)
        items = group.get(key, [])
        items.append(item)
        group[key] = items
    return group


def short_uuid():
    """Generate a short UUID string (last segment of a UUID5).

    Returns:
        str: A 12-character hex string.
    """
    return str(uuid.uuid5(uuid.NAMESPACE_DNS, f"django-reusable@{datetime.now()}")).split('-')[-1]


def is_valid_email(email):
    """Check whether a string is a valid email address.

    Args:
        email: String to validate.

    Returns:
        bool: True if the email is valid.
    """
    try:
        validate_email(email)
        return True
    except ValidationError:
        return False


def chunks(lst, n):
    """Yield successive n-sized chunks from a list.

    Args:
        lst: The list to split.
        n: Chunk size.

    Yields:
        list: Sub-lists of up to n elements.
    """
    for i in range(0, len(lst), n):
        yield lst[i:i + n]


def next_element_in_iterable(iterable, curr):
    """Return the next element after curr in a list, wrapping around to the start.

    Args:
        iterable: Indexable sequence.
        curr: Current element to find.

    Returns:
        The next element, or the first element if curr is last or not found.
    """
    if not iterable:
        return None
    try:
        i = iterable.index(curr)
        return iterable[0 if i == (len(iterable) - 1) else i + 1]
    except ValueError:
        return iterable[0]


def get_csv_bytes(data):
    """Convert a 2D list to CSV file bytes.

    Args:
        data: List of rows (each row is a list of values).

    Returns:
        bytes: CSV file contents.
    """
    file_path = get_temp_file_path()
    f = open(file_path, 'w')
    wr = csv.writer(f, quoting=csv.QUOTE_ALL)
    wr.writerows(data)
    f.close()
    return get_bytes_and_delete(file_path)


def get_html_list_from_iterable(iterable, fn, tag='ul'):
    list_items = ''.join([f'<li>{fn(value)}</li>' for value in iterable])
    return mark_safe(f'<{tag}>{list_items}</{tag}>')


def get_json_bytes(data):
    """Serialize data to pretty-printed JSON file bytes.

    Handles ``datetime`` and ``date`` objects by converting to string.

    Args:
        data: Serializable data structure.

    Returns:
        bytes: JSON file contents.
    """
    def converter(o):
        if isinstance(o, datetime) or isinstance(o, date):
            return str(o)

    file_path = get_temp_file_path()
    with open(file_path, 'w') as f:
        f.write(json.dumps(data, default=converter, indent=2))
    return get_bytes_and_delete(file_path)


def get_tz_offset(dt, timezone_name='US/Pacific'):
    """Calculate the UTC offset in hours for a timezone at a given datetime.

    Args:
        dt: Naive datetime to check.
        timezone_name: Timezone name string. Defaults to ``'US/Pacific'``.

    Returns:
        float: UTC offset in hours.
    """
    tz = timezone(timezone_name)
    target_dt = tz.localize(dt)
    utc_dt = utc.localize(dt)
    return (utc_dt - target_dt).total_seconds() / 3600


def get_absolute_url(path):
    """Build an absolute URL for the given path using the current request or settings.

    Uses ``CURRENT_HOST`` setting if available, otherwise derives from the request.

    Args:
        path: URL path (e.g. ``'/api/data/'``).

    Returns:
        str: Full absolute URL.
    """
    request = global_request()
    current_host = request.get_host() if request else settings.APP_HOST
    scheme = request.scheme if request else 'http'
    host = getattr(settings, 'CURRENT_HOST', None) or f'{scheme}://{current_host}'
    absolute_url = host + path
    return absolute_url


def pick(input_dict: dict, keys_to_pick: []):
    """Return a new dict containing only the specified keys.

    Args:
        input_dict: Source dictionary.
        keys_to_pick: Keys to include.

    Returns:
        dict: Filtered dictionary.
    """
    return dict((k, v) for (k, v) in input_dict.items() if k in keys_to_pick)


def omit(input_dict: dict, keys_to_omit: []):
    """Return a new dict excluding the specified keys.

    Args:
        input_dict: Source dictionary.
        keys_to_omit: Keys to exclude.

    Returns:
        dict: Filtered dictionary.
    """
    return dict((k, v) for (k, v) in input_dict.items() if k not in keys_to_omit)


def find(fn, iterable):
    """Return the first item in iterable that matches the predicate, or None.

    Args:
        fn: Predicate function.
        iterable: Items to search.

    Returns:
        The first matching item, or None.
    """
    filtered = ifilter(fn, iterable)
    return filtered[0] if filtered else None


def get_offset_range(minus=0, plus=0):
    """Generate a list of integer offsets from -minus to +plus, inclusive of 0.

    Args:
        minus: Number of negative offsets.
        plus: Number of positive offsets.

    Returns:
        list[int]: Sorted offset range (e.g. ``[-2, -1, 0, 1, 2]``).
    """
    return list(reversed([x * -1 for x in range(1, minus + 1)])) + [0] + list(range(1, plus + 1))


def spaces(num):
    return ' ' * num


def none_safe_get(obj, attr, default=None):
    """Safely get an attribute from an object that may be None.

    Args:
        obj: Object to access (may be None).
        attr: Attribute name.
        default: Value to return if obj is None or attr is missing.

    Returns:
        The attribute value, or default.
    """
    return getattr(obj, attr, default) if obj is not None else default
