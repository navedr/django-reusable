import csv
from django.http import HttpResponse
from collections import OrderedDict


def export_as_csv_action(description="Export selected as CSV file",
                         fields=None, exclude=None, header=True):
    """
    This function returns an export csv action
    'fields' and 'exclude' work like in django ModelForm
    'header' is whether or not to output the column names as the first row
    """
    def export_as_csv(modeladmin, request, queryset):
        """
        Generic csv export admin action.
        based on http://djangosnippets.org/snippets/1697/
        """
        opts = modeladmin.model._meta
        field_names = set([field.name for field in opts.fields])
        verbose_names = dict(
            (field.name, field.verbose_name)
            for field in opts.fields
        )
        if fields:
            field_names =list(OrderedDict.fromkeys(fields))
            verbose_names.update(dict((field, field.replace('_', ' ')) for field in fields
                                      if field not in verbose_names))
        elif exclude:
            excludeset = set(exclude)
            field_names = field_names - excludeset
        response = HttpResponse(content_type='text/csv')
        response["X-Accel-Buffering"] = "no"
        response['Content-Disposition'] = 'attachment; filename=%s.csv' % str(
            opts.verbose_name_plural.title()).replace('.', '_').replace(' ', '_')
        writer = csv.writer(response)
        if header:
            headers = [verbose_names[key].title() for key in field_names]
            writer.writerow(list(headers))
        for obj in queryset:
            writer.writerow([str(getattr(obj, field)).encode('utf-8') for field in field_names])
        return response
    export_as_csv.short_description = description
    return export_as_csv
