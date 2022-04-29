from django.contrib import admin


class TextInputFilter(admin.SimpleListFilter):
    template = 'django_reusable/filters/input-filter.pug'

    def lookups(self, request, model_admin):
        # Dummy, required to show the filter.
        return (('Dummy', 'Dummy'),)


class SearchInFilter(admin.SimpleListFilter):
    title = 'Search In'
    parameter_name = 'search'
    lookup_choices = []

    def lookups(self, request, model_admin):
        return self.lookup_choices

    def queryset(self, request, queryset):
        return queryset