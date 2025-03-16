import csv
from tempfile import NamedTemporaryFile
from zipfile import ZipFile

from django.http import HttpResponse

from .file_utils import secure_filename
from .utils import get_temp_file_path, get_bytes_and_delete, TempFile, get_zip_response_from_bytes, get_bytes


def get_csv_bytes(data):
    """
    Generates a CSV file from the given data and returns its bytes.

    Args:
        data (list): A list of rows, where each row is a list of values.

    Returns:
        bytes: The bytes of the generated CSV file.
    """
    file_path = get_temp_file_path()
    f = open(file_path, 'w')
    wr = csv.writer(f, quoting=csv.QUOTE_ALL)
    wr.writerows(data)
    f.close()
    return get_bytes_and_delete(file_path)


def get_csv_temp_file(data):
    """
    Generates a CSV file from the given data and returns it as a temporary file.

    Args:
        data (list): A list of rows, where each row is a list of values.

    Returns:
        TempFile: A temporary file containing the generated CSV data.
    """
    f = NamedTemporaryFile('w')
    wr = csv.writer(f, quoting=csv.QUOTE_ALL)
    for row in data:
        wr.writerow(row)
    f.flush()
    return TempFile(f)


def get_csv_response_from_bytes(data_bytes, file_name):
    """
    Creates an HTTP response with the given CSV data bytes.

    Args:
        data_bytes (bytes): The bytes of the CSV data.
        file_name (str): The name of the file to be used in the response.

    Returns:
        HttpResponse: An HTTP response with the CSV data.
    """
    response = HttpResponse(data_bytes, content_type='text/csv')
    response["X-Accel-Buffering"] = "no"
    response['Content-Disposition'] = 'attachment; filename=%s' % file_name
    return response


def get_csv_response(data, file_name):
    """
    Creates an HTTP response with the given CSV data.

    Args:
        data (list): A list of rows, where each row is a list of values.
        file_name (str): The name of the file to be used in the response.

    Returns:
        HttpResponse: An HTTP response with the CSV data.
    """
    csv_bytes = get_csv_bytes(data)
    return get_csv_response_from_bytes(csv_bytes, file_name)


def get_csv_package_response_from_sheets(sheets, file_name):
    """
    Creates a ZIP file containing multiple CSV files from the given sheets and returns it as an HTTP response.

    Args:
        sheets (list): A list of tuples, where each tuple contains a sheet name and a list of rows.
        file_name (str): The name of the ZIP file to be used in the response.

    Returns:
        HttpResponse: An HTTP response with the ZIP file containing the CSV data.
    """
    with NamedTemporaryFile() as tmp_zip_file:
        with ZipFile(tmp_zip_file.name, "a") as out_zip_file:
            for (sheet_name, sheet) in sheets:
                with get_csv_temp_file(sheet) as csv_file:
                    out_zip_file.write(csv_file.name, secure_filename(f'{sheet_name}.csv'))
        return get_zip_response_from_bytes(get_bytes(tmp_zip_file.name), file_name)
