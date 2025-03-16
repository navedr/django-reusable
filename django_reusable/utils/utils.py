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
from django.utils.encoding import Promise, force_text
from django.utils.safestring import mark_safe
from django.views.generic import TemplateView
from pytz import timezone, utc

from .conversion import is_number, is_int

locale.setlocale(locale.LC_ALL, '')


def global_request():
    """
    Retrieves the current global request from the middleware.

    Returns:
        HttpRequest: The current HTTP request.
    """
    from django_reusable.middleware import CRequestMiddleware
    return CRequestMiddleware.get_request()


def current_user():
    """
    Retrieves the current user from the global request.

    Returns:
        User: The current user.
    """
    return global_request().user


def truncate(value, digits):
    """
    Truncates a float value to a specified number of decimal places.

    Args:
        value (float): The value to truncate.
        digits (int): The number of decimal places to keep.

    Returns:
        float: The truncated value.
    """
    return int(value * math.pow(10, digits)) / math.pow(10, digits)


def fix_decimal_product_no(value):
    """
    Fixes the decimal representation of a product number by removing trailing '.0'.

    Args:
        value (str): The product number.

    Returns:
        str: The fixed product number.
    """
    if str(value)[-2:] == '.0':
        return str(value)[:-2]
    else:
        return str(value)


def strip_non_alpha_numeric(string):
    """
    Removes all non-alphanumeric characters from a string.

    Args:
        string (str): The input string.

    Returns:
        str: The cleansed string.
    """
    import re
    cleansed_string = re.sub("[^0-9A-Za-z]", "", string)
    return cleansed_string


def to_json(obj):
    """
    Converts an object to a JSON string.

    Args:
        obj (object): The object to convert.

    Returns:
        str: The JSON string representation of the object.
    """
    return json.dumps(obj, default=lambda o: o.__dict__, sort_keys=True, indent=4)


def _json_object_hook(d):
    """
    Converts a dictionary to a named tuple.

    Args:
        d (dict): The dictionary to convert.

    Returns:
        namedtuple: The named tuple representation of the dictionary.
    """
    return namedtuple('X', d.keys())(*d.values())


def from_json(data):
    """
    Converts a JSON string to an object.

    Args:
        data (str): The JSON string.

    Returns:
        object: The object representation of the JSON string.
    """
    return json.loads(data, object_hook=_json_object_hook)


def save_and_return_bytes(wb):
    """
    Saves an openpyxl Workbook to a temporary file and returns its bytes.

    Args:
        wb (Workbook): The openpyxl Workbook.

    Returns:
        bytes: The bytes of the saved workbook file.
    """
    file_path = get_temp_file_path()
    wb.save(file_path)
    return get_bytes_and_delete(file_path)


def get_bytes_and_delete(file_path):
    """
    Reads the bytes from a file and deletes the file.

    Args:
        file_path (str): The path to the file.

    Returns:
        bytes: The bytes of the file.
    """
    data = get_bytes(file_path)
    delete_file(file_path)
    return data


def delete_file(file_path):
    """
    Deletes a file.

    Args:
        file_path (str): The path to the file.

    Returns:
        bool: True if the file was deleted, False otherwise.
    """
    try:
        os.remove(file_path)
        return True
    except:
        return False


def rename_file(old_name, new_name):
    """
    Renames a file.

    Args:
        old_name (str): The current name of the file.
        new_name (str): The new name of the file.
    """
    os.rename(old_name, new_name)


def move_file(source, destination):
    """
    Moves a file to a new location.

    Args:
        source (str): The current path of the file.
        destination (str): The new path of the file.
    """
    os.rename(source, destination)


def get_bytes(file_path):
    """
    Reads the bytes from a file.

    Args:
        file_path (str): The path to the file.

    Returns:
        bytes: The bytes of the file.
    """
    in_file = open(file_path, "rb")  # opening for [r]eading as [b]inary
    data = in_file.read()  # if you only wanted to read 512 bytes, do .read(512)
    in_file.close()
    return data


def get_temp_file_path(extn=None):
    """
    Generates a temporary file path.

    Args:
        extn (str, optional): The file extension. Defaults to None.

    Returns:
        str: The temporary file path.
    """
    import uuid
    file_name = str(uuid.uuid4()) + (f'.{extn}' if extn else '')
    file_path = os.path.join(settings.MEDIA_ROOT, "tmp", file_name)
    return file_path


def xstr(s, default=''):
    """
    Converts a value to a string, using a default value if the input is None.

    Args:
        s (any): The value to convert.
        default (str, optional): The default value. Defaults to ''.

    Returns:
        str: The string representation of the value.
    """
    return default if s is None else str(s)


def prepend_project_directory(directory_name):
    """
    Prepends the project directory to a given directory name.

    Args:
        directory_name (str): The directory name.

    Returns:
        str: The full path with the project directory prepended.
    """
    return os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), directory_name)


def unicode_to_string(x):
    """
    Converts a Unicode string to an ASCII string, ignoring characters that cannot be encoded.

    Args:
        x (str): The Unicode string to convert.

    Returns:
        str: The ASCII string.
    """
    return encoding.smart_str(x, encoding='ascii', errors='ignore')


class CustomEncoder(DjangoJSONEncoder):
    """
    Custom JSON encoder that handles Django's FieldFile and Promise objects.
    """

    def default(self, o):
        """
        Overrides the default method to provide custom serialization for FieldFile and Promise objects.

        Args:
            o (object): The object to serialize.

        Returns:
            str: The serialized object.
        """
        if isinstance(o, FieldFile):
            return o.url if o.name else ''
        elif isinstance(o, Promise):
            return force_text(o)
        else:
            try:
                return super().default(o)
            except:
                return force_text(o)


def coalesce(value, replace):
    """
    Returns the value if it is not None, otherwise returns the replace value.

    Args:
        value (any): The value to check.
        replace (any): The value to return if the original value is None.

    Returns:
        any: The original value or the replace value.
    """
    if value is None:
        return replace
    return value


def query_to_dicts(query_string, params=None):
    """
    Runs a simple query and produces a generator that returns the results as dictionaries.

    Args:
        query_string (str): The SQL query to execute.
        params (tuple, optional): The parameters to use in the query. Defaults to None.

    Yields:
        dict: A dictionary representing a row in the query result.
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
    """
    Runs a simple query and produces a generator that returns the results as lists.

    Args:
        query_string (str): The SQL query to execute.
        col_index (int, optional): The column index to return. Defaults to None.
        params (tuple, optional): The parameters to use in the query. Defaults to None.

    Yields:
        list: A list representing a row in the query result.
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
    """
    Renders a form field as HTML.

    Args:
        field (Field): The form field to render.
        name (str): The name of the form field.

    Returns:
        str: The HTML representation of the form field.
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
    """
    Retrieves the fields and properties of a Django model.

    Args:
        model (Model): The Django model.

    Returns:
        list: A list of tuples containing the field/property name and its verbose name.
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
    """
    Context manager for handling multiple temporary files.
    """

    def __init__(self, *files):
        """
        Initializes the TempFiles context manager.

        Args:
            files (list): A list of file objects.
        """
        self.files = files

    def __exit__(self, exc_type, exc_val, exc_tb):
        """
        Closes all files on exit.
        """
        for f in self.files:
            f.close()

    def __enter__(self):
        """
        Enters the context manager.

        Returns:
            list: The list of file objects.
        """
        return self.files


class TempFilesFromBytes(TempFiles):
    """
    Context manager for handling multiple temporary files created from bytes.
    """

    def __init__(self, *file_bytes):
        """
        Initializes the TempFilesFromBytes context manager.

        Args:
            file_bytes (list): A list of byte objects.
        """
        files = []
        for file_byte in file_bytes:
            f = NamedTemporaryFile()
            f.write(file_byte)
            f.close()
        super().__init__(*files)


class TempFile(object):
    """
    Context manager for handling a single temporary file.
    """

    def __init__(self, file):
        """
        Initializes the TempFile context manager.

        Args:
            file (file): The file object.
        """
        self.file = file

    def __exit__(self, exc_type, exc_val, exc_tb):
        """
        Closes the file on exit.
        """
        self.file.close()

    def __enter__(self):
        """
        Enters the context manager.

        Returns:
            file: The file object.
        """
        return self.file


def get_wb_response_from_bytes(data_bytes, file_name):
    """
    Creates an HTTP response with the given workbook data bytes.

    Args:
        data_bytes (bytes): The bytes of the workbook data.
        file_name (str): The name of the file to be used in the response.

    Returns:
        HttpResponse: An HTTP response with the workbook data.
    """
    response = HttpResponse(data_bytes,
                            content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
    response["X-Accel-Buffering"] = "no"
    response['Content-Disposition'] = 'attachment; filename=%s' % file_name
    return response


def get_zip_response_from_bytes(data_bytes, file_name):
    """
    Creates an HTTP response with the given ZIP file data bytes.

    Args:
        data_bytes (bytes): The bytes of the ZIP file data.
        file_name (str): The name of the file to be used in the response.

    Returns:
        HttpResponse: An HTTP response with the ZIP file data.
    """
    response = HttpResponse(data_bytes,
                            content_type="application/zip")
    response["X-Accel-Buffering"] = "no"
    response['Content-Disposition'] = 'attachment; filename=%s' % file_name
    return response


def get_wb_response(wb, file_name):
    """
    Creates an HTTP response with the given workbook.

    Args:
        wb (Workbook): The openpyxl Workbook.
        file_name (str): The name of the file to be used in the response.

    Returns:
        HttpResponse: An HTTP response with the workbook data.
    """
    return get_wb_response_from_bytes(save_and_return_bytes(wb), file_name)


def render_to_string_from_source(template_source, context_dict=None):
    """
    Renders a template from a string source with the given context.

    Args:
        template_source (str): The template source as a string.
        context_dict (dict, optional): The context dictionary. Defaults to None.

    Returns:
        str: The rendered template as a string.
    """
    t = engines['django'].from_string(template_source)
    return t.render(context_dict)


def sum_by_tuple_element_in_list(input_list, decimal_places=None):
    """
    Sums values in a list of tuples grouped by the first element in each tuple.

    Args:
        input_list (list): A list of tuples, where each tuple contains a group key and a value.
        decimal_places (int, optional): The number of decimal places to round the sum to. Defaults to None.

    Yields:
        tuple: A tuple containing the group key and the sum of values for that group.
    """
    distinct_group_values = OrderedDict(input_list).keys()
    for group in distinct_group_values:
        sum_of_elements = sum(val for (key, val) in input_list if key == group)
        if decimal_places is not None:
            sum_of_elements = round(sum_of_elements, decimal_places)
        yield (group, sum_of_elements)


def median(input_list):
    """
    Calculates the median of a list of numbers.

    Args:
        input_list (list): A list of numbers.

    Returns:
        float: The median value.
    """
    quotient, remainder = divmod(len(input_list), 2)
    if remainder:
        return sorted(input_list)[quotient]
    return float(sum(sorted(input_list)[quotient - 1:quotient + 1]) / 2)


def mode(input_list):
    """
    Calculates the mode of a list of numbers.

    Args:
        input_list (list): A list of numbers.

    Returns:
        int: The mode value, or 0 if there is no mode.
    """
    m = max([input_list.count(a) for a in input_list])
    return [x for x in input_list if input_list.count(x) == m][0] if m > 1 else 0


def math_range(input_list):
    """
    Calculates the range of a list of numbers.

    Args:
        input_list (list): A list of numbers.

    Returns:
        int: The range of the list, or 0 if the list is empty.
    """
    return max(input_list) - min(input_list) if input_list else 0


def get_subclasses(classes, level=0):
    """
    Returns the list of all subclasses for a given class or list of classes.

    Args:
        classes (type or list): The class or list of classes to find subclasses for.
        level (int, optional): The current recursion level. Defaults to 0.

    Returns:
        list: A list of all subclasses.
    """
    if not isinstance(classes, list):
        classes = [classes]

    if level < len(classes):
        classes += classes[level].__subclasses__()
        return get_subclasses(classes, level + 1)
    else:
        return classes


def image(instance, file_name, image_url):
    """
    Generates HTML for displaying an image with a link.

    Args:
        instance (object): The instance containing the image.
        file_name (str): The name of the image file.
        image_url (str): The URL of the image.

    Returns:
        str: The HTML string for the image.
    """
    if image_url:
        urls = [image_url, instance.find_full_image_url(file_name)]
        return mark_safe('<br>Full Image:<br>'.join([
            "<a href='%(image_url)s' target='_blank'><img style='max-width: 100px' src='%(image_url)s' alt='Image 1'"
            " /></a>" % {'image_url': url} for url in urls if url]))


def get_pdf_response_from_file(pdf, file_name):
    """
    Creates an HTTP response with the given PDF file.

    Args:
        pdf (bytes): The PDF file data.
        file_name (str): The name of the file to be used in the response.

    Returns:
        HttpResponse: An HTTP response with the PDF file.
    """
    response = HttpResponse(pdf, content_type='application/pdf')
    response["X-Accel-Buffering"] = "no"
    response['Content-Disposition'] = 'inline; filename=%s.pdf' % file_name
    return response


def format_as_currency(value, decimal_precision=2, currency_symbol='$'):
    """
    Formats a number as a currency string.

    Args:
        value (float): The value to format.
        decimal_precision (int, optional): The number of decimal places. Defaults to 2.
        currency_symbol (str, optional): The currency symbol. Defaults to '$'.

    Returns:
        str: The formatted currency string.
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
    """
    Converts a list of lists to an HTML table.

    Args:
        data (list): A list of lists representing the table rows.
        table_class (str, optional): The CSS class for the table. Defaults to ''.
        has_header (bool, optional): Whether the first row is a header. Defaults to False.

    Returns:
        str: The HTML string for the table.
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
    """
    Converts an iterable to an HTML unordered list.

    Args:
        iterable (iterable): The iterable to convert.
        css_class_name (str, optional): The CSS class name for the <ul> element. Defaults to ''.

    Returns:
        str: The HTML string for the unordered list.
    """
    if not iterable:
        return ''
    return mark_safe(f'''<ul class="{css_class_name}">{"".join(f"<li>{value}</li>" for value in iterable)}</ul>''')


def get_id_from_url(request):
    """
    Extracts the object ID from the URL in the request.

    Args:
        request (HttpRequest): The HTTP request object.

    Returns:
        str or None: The object ID if found, otherwise None.
    """
    resolved = resolve(request.path_info)
    if resolved.args:
        return resolved.args[0]
    if resolved.kwargs:
        return resolved.kwargs['object_id']
    return None


def get_count_dict(iterable, by_property=None):
    """
    Counts the occurrences of elements in an iterable, optionally by a specified property.

    Args:
        iterable (iterable): The iterable to count elements from.
        by_property (str or list, optional): The property or properties to count by. Defaults to None.

    Returns:
        dict: A dictionary with elements or properties as keys and their counts as values.
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
    """
    Filters an iterable using a function.

    Args:
        fn (function): The function to filter by.
        iterable (iterable): The iterable to filter.

    Returns:
        list: A list of filtered elements.
    """
    return list(filter(fn, iterable))


def imap(fn, iterable):
    """
    Maps a function to an iterable.

    Args:
        fn (function): The function to apply.
        iterable (iterable): The iterable to map the function to.

    Returns:
        list: A list of mapped elements.
    """
    return list(map(fn, iterable))


def is_user_admin():
    """
    Checks if the current user has admin permissions.

    Returns:
        bool: True if the current user is an admin, False otherwise.
    """
    return current_user().has_perm('user.is_admin')


def get_property(obj, name, fn):
    """
    Gets a property from an object, setting it with a function if it does not exist.

    Args:
        obj (object): The object to get the property from.
        name (str): The name of the property.
        fn (function): The function to set the property if it does not exist.

    Returns:
        any: The value of the property.
    """
    if not hasattr(obj, name):
        setattr(obj, name, fn())
    return getattr(obj, name)


def humane_currency(value):
    """
    Formats a number as a human-readable currency string.

    Args:
        value (float): The value to format.

    Returns:
        str: The formatted currency string.
    """
    if value is None:
        return value
    return f'${humane_number(value)}'


def humane_number(value):
    """
    Formats a number as a human-readable string with magnitude suffixes.

    Args:
        value (float): The value to format.

    Returns:
        str: The formatted number string.
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
    """
    A mixin that can be used to render a JSON response.
    """

    def render_to_json_response(self, context, **response_kwargs):
        """
        Returns a JSON response, transforming 'context' to make the payload.

        Args:
            context (dict): The context dictionary to transform.
            **response_kwargs: Additional response keyword arguments.

        Returns:
            JsonResponse: The JSON response.
        """
        return JsonResponse(
            self.get_data(context),
            **response_kwargs, safe=False
        )

    def get_data(self, context):
        """
        Returns an object that will be serialized as JSON by json.dumps().

        Args:
            context (dict): The context dictionary to transform.

        Returns:
            dict: The transformed context dictionary.
        """
        return context


class JSONView(JSONResponseMixin, TemplateView):
    """
    A view that renders a JSON response.
    """

    def render_to_response(self, context, **response_kwargs):
        """
        Renders the view to a JSON response.

        Args:
            context (dict): The context dictionary to transform.
            **response_kwargs: Additional response keyword arguments.

        Returns:
            JsonResponse: The JSON response.
        """
        return self.render_to_json_response(context, **response_kwargs)


def get_random_color_hex():
    """
    Generates a random color in hexadecimal format.

    Returns:
        str: The random color in hexadecimal format.
    """
    r = lambda: random.randint(0, 255)
    return '#%02X%02X%02X' % (r(), r(), r())


def write_text_to_file(content, file_path):
    """
    Writes text content to a file.

    Args:
        content (str): The text content to write.
        file_path (str): The path to the file.
    """
    with open(file_path, 'w') as f:
        f.write(content)


def group_by_property(iterable, prop=None, prop_fn=None):
    """
    Groups elements in an iterable by a specified property or function.

    Args:
        iterable (iterable): The iterable to group.
        prop (str, optional): The property to group by. Defaults to None.
        prop_fn (function, optional): The function to group by. Defaults to None.

    Returns:
        dict: A dictionary with properties or function results as keys and lists of grouped elements as values.
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
    """
    Generates a short UUID.

    Returns:
        str: The short UUID.
    """
    return str(uuid.uuid5(uuid.NAMESPACE_DNS, f"django-reusable@{datetime.now()}")).split('-')[-1]


def is_valid_email(email):
    """
    Checks if an email address is valid.

    Args:
        email (str): The email address to check.

    Returns:
        bool: True if the email address is valid, False otherwise.
    """
    try:
        validate_email(email)
        return True
    except ValidationError:
        return False


def chunks(lst, n):
    """
    Yields successive n-sized chunks from a list.

    Args:
        lst (list): The list to chunk.
        n (int): The size of each chunk.

    Yields:
        list: The next chunk of the list.
    """
    for i in range(0, len(lst), n):
        yield lst[i:i + n]


def next_element_in_iterable(iterable, curr):
    """
    Gets the next element in an iterable, wrapping around if necessary.

    Args:
        iterable (iterable): The iterable to get the next element from.
        curr (any): The current element.

    Returns:
        any: The next element in the iterable.
    """
    if not iterable:
        return None
    try:
        i = iterable.index(curr)
        return iterable[0 if i == (len(iterable) - 1) else i + 1]
    except ValueError:
        return iterable[0]


def get_csv_bytes(data):
    """
    Converts data to CSV format and returns it as bytes.

    Args:
        data (list): The data to convert to CSV.

    Returns:
        bytes: The CSV data as bytes.
    """
    file_path = get_temp_file_path()
    f = open(file_path, 'w')
    wr = csv.writer(f, quoting=csv.QUOTE_ALL)
    wr.writerows(data)
    f.close()
    return get_bytes_and_delete(file_path)


def get_html_list_from_iterable(iterable, fn, tag='ul'):
    """
    Converts an iterable to an HTML list using a function to format each element.

    Args:
        iterable (iterable): The iterable to convert.
        fn (function): The function to format each element.
        tag (str, optional): The HTML tag to use for the list. Defaults to 'ul'.

    Returns:
        str: The HTML string for the list.
    """
    list_items = ''.join([f'<li>{fn(value)}</li>' for value in iterable])
    return mark_safe(f'<{tag}>{list_items}</{tag}>')


def get_json_bytes(data):
    """
    Converts data to JSON format and returns it as bytes.

    Args:
        data (any): The data to convert to JSON.

    Returns:
        bytes: The JSON data as bytes.
    """

    def converter(o):
        if isinstance(o, datetime) or isinstance(o, date):
            return str(o)

    file_path = get_temp_file_path()
    with open(file_path, 'w') as f:
        f.write(json.dumps(data, default=converter, indent=2))
    return get_bytes_and_delete(file_path)


def get_tz_offset(dt, timezone_name='US/Pacific'):
    """
    Calculates the timezone offset for a given datetime and timezone.

    Args:
        dt (datetime): The datetime to calculate the offset for.
        timezone_name (str, optional): The name of the timezone. Defaults to 'US/Pacific'.

    Returns:
        float: The timezone offset in hours.
    """
    tz = timezone(timezone_name)
    target_dt = tz.localize(dt)
    utc_dt = utc.localize(dt)
    return (utc_dt - target_dt).total_seconds() / 3600


def get_absolute_url(path):
    """
    Constructs an absolute URL from a path.

    Args:
        path (str): The path to construct the URL from.

    Returns:
        str: The absolute URL.
    """
    request = global_request()
    current_host = request.get_host() if request else settings.APP_HOST
    scheme = request.scheme if request else 'http'
    host = getattr(settings, 'CURRENT_HOST', None) or f'{scheme}://{current_host}'
    absolute_url = host + path
    return absolute_url


def pick(input_dict: dict, keys_to_pick: []):
    """
    Picks specified keys from a dictionary.

    Args:
        input_dict (dict): The dictionary to pick keys from.
        keys_to_pick (list): The keys to pick.

    Returns:
        dict: A dictionary with the picked keys and their values.
    """
    return dict((k, v) for (k, v) in input_dict.items() if k in keys_to_pick)


def omit(input_dict: dict, keys_to_omit: []):
    """
    Omits specified keys from a dictionary.

    Args:
        input_dict (dict): The dictionary to omit keys from.
        keys_to_omit (list): The keys to omit.

    Returns:
        dict: A dictionary without the omitted keys.
    """
    return dict((k, v) for (k, v) in input_dict.items() if k not in keys_to_omit)


def find(fn, iterable):
    """
    Finds the first element in an iterable that matches a function.

    Args:
        fn (function): The function to match elements.
        iterable (iterable): The iterable to search.

    Returns:
        any: The first matching element, or None if no match is found.
    """
    filtered = ifilter(fn, iterable)
    return filtered[0] if filtered else None


def get_offset_range(minus=0, plus=0):
    """
    Generates a range of offsets.

    Args:
        minus (int, optional): The number of negative offsets. Defaults to 0.
        plus (int, optional): The number of positive offsets. Defaults to 0.

    Returns:
        list: A list of offsets.
    """
    return list(reversed([x * -1 for x in range(1, minus + 1)])) + [0] + list(range(1, plus + 1))


def spaces(num):
    """
    Generates a string of spaces.

    Args:
        num (int): The number of spaces.

    Returns:
        str: The string of spaces.
    """
    return ' ' * num


def none_safe_get(obj, attr, default=None):
    """
    Safely gets an attribute from an object, returning a default value if the object is None.

    Args:
        obj (object): The object to get the attribute from.
        attr (str): The name of the attribute.
        default (any, optional): The default value to return if the object is None. Defaults to None.

    Returns:
        any: The attribute value or the default value.
    """
    return getattr(obj, attr, default) if obj is not None else default
