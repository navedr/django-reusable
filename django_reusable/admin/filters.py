from django.contrib import admin

class TextInputFilter(admin.SimpleListFilter):
    """
    A filter that provides a text input for filtering in the admin interface.
    """
    template = 'django_reusable/filters/input-filter.html'

    def lookups(self, request, model_admin):
        """
        Returns a dummy lookup to display the filter.
        """
        return (('Dummy', 'Dummy'),)

    def queryset(self, request, queryset):
        """
        Returns the filtered queryset.
        """
        return queryset

class SearchInFilter(admin.SimpleListFilter):
    """
    A filter that allows searching within specified fields in the admin interface.
    """
    title = 'Search In'
    parameter_name = 'search'
    lookup_choices = []

    def lookups(self, request, model_admin):
        """
        Returns the lookup choices for the filter.
        """
        return self.lookup_choices

    def queryset(self, request, queryset):
        """
        Returns the filtered queryset.
        """
        return queryset