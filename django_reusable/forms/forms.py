from django import forms
from django.forms import HiddenInput, BaseInlineFormSet

from .widgets import ReadOnlyInput


class HiddenModelForm(forms.ModelForm):
    """
    A ModelForm where all fields are rendered as hidden inputs.
    """

    def __init__(self, *args, **kwargs):
        """
        Initializes the HiddenModelForm and sets all field widgets to HiddenInput.
        """
        super().__init__(*args, **kwargs)
        for field in self.fields:
            self.fields[field].widget = HiddenInput()


class ReadOnlyModelForm(forms.ModelForm):
    """
    A ModelForm where all fields are rendered as read-only inputs.
    """

    def __init__(self, *args, **kwargs):
        """
        Initializes the ReadOnlyModelForm and sets all field widgets to ReadOnlyInput.
        """
        super().__init__(*args, **kwargs)
        for field in self.fields:
            self.fields[field].widget = ReadOnlyInput()


class EnhancedBaseInlineFormSet(BaseInlineFormSet):
    """
    A custom BaseInlineFormSet with enhanced functionality for limiting querysets.

    Attributes:
        limit_saved_queryset_value_fields (list): Fields to limit the queryset based on saved instance values.
        default_field_queryset (dict): Default querysets for fields.
        limit_field_queryset_model_fields (dict): Fields to limit the queryset based on model fields.
    """
    limit_saved_queryset_value_fields = []
    default_field_queryset = dict()
    limit_field_queryset_model_fields = dict()

    def add_fields(self, form, index):
        """
        Adds fields to the form and customizes their querysets based on instance values or defaults.

        Args:
            form (forms.ModelForm): The form to which fields are added.
            index (int): The index of the form in the formset.
        """
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
