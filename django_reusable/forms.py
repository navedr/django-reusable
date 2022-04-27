from django import forms
from django.forms import HiddenInput, BaseInlineFormSet

from django_reusable.widgets import ReadOnlyInput


class HiddenModelForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields:
            self.fields[field].widget = HiddenInput()


class ReadOnlyModelForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields:
            self.fields[field].widget = ReadOnlyInput()


class EnhancedBaseInlineFormSet(BaseInlineFormSet):
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
