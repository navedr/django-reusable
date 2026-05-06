import csv
from tempfile import NamedTemporaryFile
from zipfile import ZipFile

from django.http import HttpResponse

from .file_utils import secure_filename
from .utils import get_temp_file_path, get_bytes_and_delete, TempFile, get_zip_response_from_bytes, get_bytes


def get_csv_bytes(data):
    """Convert a 2D list of rows to CSV file bytes.

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


def get_csv_temp_file(data):
    """Write CSV data to a named temporary file and return it wrapped in a TempFile.

    Args:
        data: Iterable of rows (each row is an iterable of values).

    Returns:
        TempFile: Context manager wrapping the temp file.
    """
    f = NamedTemporaryFile('w')
    wr = csv.writer(f, quoting=csv.QUOTE_ALL)
    for row in data:
        wr.writerow(row)
    f.flush()
    return TempFile(f)


def get_csv_response_from_bytes(data_bytes, file_name):
    """Create an HttpResponse for downloading a CSV file from bytes.

    Args:
        data_bytes: The CSV file contents as bytes.
        file_name: The download file name.

    Returns:
        HttpResponse: Configured for CSV download.
    """
    response = HttpResponse(data_bytes, content_type='text/csv')
    response["X-Accel-Buffering"] = "no"
    response['Content-Disposition'] = 'attachment; filename=%s' % file_name
    return response


def get_csv_response(data, file_name):
    """Generate a CSV download response from a 2D list of data.

    Args:
        data: List of rows (each row is a list of values).
        file_name: The download file name.

    Returns:
        HttpResponse: Configured for CSV download.
    """
    csv_bytes = get_csv_bytes(data)
    return get_csv_response_from_bytes(csv_bytes, file_name)


def get_csv_package_response_from_sheets(sheets, file_name):
    """Package multiple CSV sheets into a ZIP file and return as a download response.

    Args:
        sheets: Iterable of ``(sheet_name, sheet_data)`` tuples, where sheet_data
            is a 2D list of rows. Each sheet becomes a CSV file in the ZIP.
        file_name: The download file name for the ZIP archive.

    Returns:
        HttpResponse: Configured for ZIP download containing the CSV files.

    Example:
        ```python
        sheets = [
            ('users', [['name', 'email'], ['Alice', 'a@b.com']]),
            ('orders', [['id', 'total'], [1, 99.99]]),
        ]
        response = get_csv_package_response_from_sheets(sheets, 'export.zip')
        ```
    """
    with NamedTemporaryFile() as tmp_zip_file:
        with ZipFile(tmp_zip_file.name, "a") as out_zip_file:
            for (sheet_name, sheet) in sheets:
                with get_csv_temp_file(sheet) as csv_file:
                    out_zip_file.write(csv_file.name, secure_filename(f'{sheet_name}.csv'))
        return get_zip_response_from_bytes(get_bytes(tmp_zip_file.name), file_name)
