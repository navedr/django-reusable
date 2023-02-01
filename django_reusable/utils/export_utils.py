import csv
from tempfile import NamedTemporaryFile
from zipfile import ZipFile

from django.http import HttpResponse

from .file_utils import secure_filename
from .utils import get_temp_file_path, get_bytes_and_delete, TempFile, get_zip_response_from_bytes, get_bytes


def get_csv_bytes(data):
    file_path = get_temp_file_path()
    f = open(file_path, 'w')
    wr = csv.writer(f, quoting=csv.QUOTE_ALL)
    wr.writerows(data)
    f.close()
    return get_bytes_and_delete(file_path)


def get_csv_temp_file(data):
    f = NamedTemporaryFile('w')
    wr = csv.writer(f, quoting=csv.QUOTE_ALL)
    for row in data:
        wr.writerow(row)
    f.flush()
    return TempFile(f)


def get_csv_response_from_bytes(data_bytes, file_name):
    response = HttpResponse(data_bytes, content_type='text/csv')
    response["X-Accel-Buffering"] = "no"
    response['Content-Disposition'] = 'attachment; filename=%s' % file_name
    return response


def get_csv_response(data, file_name):
    csv_bytes = get_csv_bytes(data)
    return get_csv_response_from_bytes(csv_bytes, file_name)


def get_csv_package_response_from_sheets(sheets, file_name):
    with NamedTemporaryFile() as tmp_zip_file:
        with ZipFile(tmp_zip_file.name, "a") as out_zip_file:
            for (sheet_name, sheet) in sheets:
                with get_csv_temp_file(sheet) as csv_file:
                    out_zip_file.write(csv_file.name, secure_filename(f'{sheet_name}.csv'))
        return get_zip_response_from_bytes(get_bytes(tmp_zip_file.name), file_name)
