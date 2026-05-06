from django import forms
from django.forms import HiddenInput, BaseInlineFormSet

from .widgets import ReadOnlyInput


class HiddenModelForm(forms.ModelForm):
    """ModelForm that renders all fields as hidden inputs.

    Useful for embedding form data in a page without visible fields, e.g.
    confirmation steps or passing data through intermediate views.
    """
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields:
            self.fields[field].widget = HiddenInput()


class ReadOnlyModelForm(forms.ModelForm):
    """ModelForm that renders all fields as read-only text with hidden inputs.

    Each field is replaced with a ``ReadOnlyInput`` widget that displays the
    value as plain text while preserving the value in a hidden ``<input>``
    for form submission.
    """
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields:
            self.fields[field].widget = ReadOnlyInput()


class EnhancedBaseInlineFormSet(BaseInlineFormSet):
    """Inline formset with queryset limiting for ForeignKey fields.

    For saved (existing) rows, ForeignKey dropdowns are restricted to only the
    currently selected value, preventing users from changing already-saved
    relations. For new (unsaved) rows, a custom default queryset can be applied.

    Attributes:
        limit_saved_queryset_value_fields: List of field names whose querysets
            should be limited to the current value on saved instances.
        default_field_queryset: Dict mapping field names to default querysets
            for new (unsaved) inline rows.
        limit_field_queryset_model_fields: Dict mapping field names to lists of
            model field names to pass to ``.only()`` for queryset optimization.
    """
    limit_saved_queryset_value_fields = []
    default_field_queryset = dict()
    limit_field_queryset_model_fields = dict()

    def add_fields(self, form, index):
        super().add_fields(form, index)
        if form.instance.pk:
            if self.limit_saved_queryset_value_fields:
                for field in self.limit_saved_queryset_value_fields:
                    form.fields[field].queryset = form.fields[field].queryset.filter(
                        id=getattr(form.instance, f'{field}_id'))
        else:
            for (field, queryset) in self.default_field_queryset.items():
                form.fields[field].queryset = queryset
        if self.limit_saved_queryset_value_fields:
            for (field, limit_fields) in self.limit_field_queryset_model_fields.items():
                form.fields[field].queryset = form.fields[field].queryset.only(*limit_fields)
