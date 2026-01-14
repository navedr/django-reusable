from django.contrib import admin
from django.contrib.admin import FieldListFilter


class TextInputFilter(admin.SimpleListFilter):
    template = 'django_reusable/filters/input-filter.html'

    def lookups(self, request, model_admin):
        # Dummy, required to show the filter.
        return (('Dummy', 'Dummy'),)

    def queryset(self, request, queryset):
        return queryset


class SearchInFilter(admin.SimpleListFilter):
    title = 'Search In'
    parameter_name = 'search'
    lookup_choices = []

    def lookups(self, request, model_admin):
        return self.lookup_choices

    def queryset(self, request, queryset):
        return queryset


class MultiSelectFilterMixin:
    """
    Base mixin for multi-select admin filters using <select multiple>.

    Provides common functionality for filters that allow multiple values
    to be selected and filtered with OR logic (field__in lookup).
    """

    template = 'django_reusable/filters/multi-select-filter.html'

    def expected_parameters(self):
        """Return list of expected URL parameters for this filter"""
        return [self.parameter_name]

    def get_selected_values(self):
        """Get list of currently selected values from URL parameters"""
        return self.used_parameters.get(self.parameter_name, [])

    def queryset(self, request, queryset):
        """Apply filtering with __in lookup for selected values"""
        values = self.get_selected_values()
        if values:
            lookup_field = self.field_path
            try:
                return queryset.filter(**{f'{lookup_field}__in': values})
            except Exception as e:
                # Invalid values - return unfiltered queryset
                return queryset
        return queryset

    @property
    def options(self):
        """Get all available options for the select element"""
        return self.lookups(self.request, self.model_admin)

    @property
    def selected_values(self):
        """Get currently selected values"""
        return self.get_selected_values()

    @property
    def other_params(self):
        """Get other GET parameters (excluding this filter's parameter)"""
        # Use request.GET which is a QueryDict that preserves multiple values
        params = self.request.GET.copy()
        params.pop(self.parameter_name, None)
        return params

    @property
    def clear_url(self):
        """Build URL to clear this filter"""
        # Use request.GET to preserve multiple values in other parameters
        params = self.request.GET.copy()
        params.pop(self.parameter_name, None)
        if params:
            return '?' + params.urlencode()
        return '?'

    def choices(self, changelist):
        """
        For compatibility with FieldListFilter.
        Return empty generator since we use a custom template.
        """
        return iter([])


class MultiSelectAllValuesFieldFilter(MultiSelectFilterMixin, FieldListFilter):
    """
    Multi-select filter for all distinct values in a model field.

    Usage:
        class MyAdmin(admin.ModelAdmin):
            list_filter = [
                ('field_name', MultiSelectAllValuesFieldFilter),
            ]
    """

    def __init__(self, field, request, params, model, model_admin, field_path):
        self.field = field
        self.field_path = field_path
        self.parameter_name = f'{field_path}__in'
        self.title = field.verbose_name
        self.request = request
        self.model_admin = model_admin
        self.params = params

        # Call parent init first
        super().__init__(field, request, params, model, model_admin, field_path)

        # Extract selected values AFTER super().__init__() to avoid it being overwritten
        # Always use request.GET.getlist() for multiple values
        self.used_parameters = {}
        if self.parameter_name in request.GET:
            value = request.GET.getlist(self.parameter_name)
            # Ensure all values are strings for proper comparison in template
            value = [str(v) for v in value if v]
            if value:
                self.used_parameters[self.parameter_name] = value

    def lookups(self, request, model_admin):
        """Get all distinct values from database"""
        qs = model_admin.get_queryset(request)
        values = qs.order_by(self.field.name).values_list(
            self.field.name, flat=True
        ).distinct()

        # Return (value, label) tuples
        return [(str(val), str(val)) for val in values if val is not None]

    def has_output(self):
        return True


class MultiSelectChoicesFieldFilter(MultiSelectFilterMixin, FieldListFilter):
    """
    Multi-select filter for fields with predefined choices.

    Works with fields where value != label, like:
        position = models.CharField(
            choices=[('SE', 'Software Engineer'), ('MGR', 'Manager')]
        )

    Usage:
        class MyAdmin(admin.ModelAdmin):
            list_filter = [
                ('position', MultiSelectChoicesFieldFilter),
            ]
    """

    def __init__(self, field, request, params, model, model_admin, field_path):
        self.field = field
        self.field_path = field_path
        self.parameter_name = f'{field_path}__in'
        self.title = field.verbose_name
        self.lookup_choices = field.choices or []
        self.request = request
        self.model_admin = model_admin
        self.params = params

        # Call parent init first
        super().__init__(field, request, params, model, model_admin, field_path)

        # Extract selected values AFTER super().__init__() to avoid it being overwritten
        # Always use request.GET.getlist() for multiple values
        self.used_parameters = {}
        if self.parameter_name in request.GET:
            value = request.GET.getlist(self.parameter_name)
            # Ensure all values are strings for proper comparison in template
            value = [str(v) for v in value if v]
            if value:
                self.used_parameters[self.parameter_name] = value

    def lookups(self, request, model_admin):
        """Return field's defined choices"""
        return self.lookup_choices

    def has_output(self):
        return True


class MultiSelectRelatedFieldFilter(MultiSelectFilterMixin, FieldListFilter):
    """
    Multi-select filter for ForeignKey and ManyToManyField relationships.

    Usage:
        class MyAdmin(admin.ModelAdmin):
            list_filter = [
                ('author', MultiSelectRelatedFieldFilter),
            ]
    """

    def __init__(self, field, request, params, model, model_admin, field_path):
        self.field = field
        self.field_path = field_path
        self.parameter_name = f'{field_path}__in'
        self.title = field.verbose_name
        self.request = request
        self.model_admin = model_admin
        self.params = params

        # Get related model
        if hasattr(field, 'related_model'):
            self.related_model = field.related_model
        else:
            self.related_model = field.remote_field.model

        # Call parent init first
        super().__init__(field, request, params, model, model_admin, field_path)

        # Extract selected values AFTER super().__init__() to avoid it being overwritten
        # Always use request.GET.getlist() for multiple values
        self.used_parameters = {}
        if self.parameter_name in request.GET:
            value = request.GET.getlist(self.parameter_name)
            # Ensure all values are strings for proper comparison in template
            value = [str(v) for v in value if v]
            if value:
                self.used_parameters[self.parameter_name] = value

    def lookups(self, request, model_admin):
        """Query related model for available objects"""
        qs = self.related_model.objects.all()

        # Respect any custom queryset from model_admin
        if hasattr(model_admin, 'get_field_queryset'):
            custom_qs = model_admin.get_field_queryset(None, self.field, request)
            if custom_qs:
                qs = custom_qs

        # Return (pk, str) tuples
        return [(str(obj.pk), str(obj)) for obj in qs]

    def queryset(self, request, queryset):
        """Apply filtering with proper type conversion for PKs"""
        values = self.get_selected_values()
        if values:
            try:
                # Convert string PKs to integers
                pk_list = [int(v) for v in values]
                return queryset.filter(**{f'{self.field_path}__in': pk_list})
            except (ValueError, TypeError):
                return queryset
        return queryset

    def has_output(self):
        return True
