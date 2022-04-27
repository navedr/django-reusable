import os

from django import forms
from django.utils.safestring import mark_safe

from .utils import xstr


class FileLinkWidget(forms.TextInput):
    def __init__(self, base_path, base_url, attrs=None):
        self.base_path = base_path
        self.base_url = base_url
        super(FileLinkWidget, self).__init__(attrs)

    def get_link(self, value):
        if value and os.path.exists(os.path.join(self.base_path, value)):
            return mark_safe('<a href="%s" target="_blank" class="btn btn-default">Open</a>' %
                             os.path.join(self.base_url, value))
        return ''

    def render(self, name, value, attrs=None, renderer=None):
        html = '''
            <div class="input-group">
                %s
                <span class="input-group-btn"> 
                    %s
                </span>
            </div>
        ''' % (super().render(name, value, attrs, renderer), self.get_link(value))
        return html


class ReadonlySelect(forms.Select):
    def render(self, name, value, attrs=None, renderer=None):
        matches = [t for (v, t) in self.choices if v == value]
        text = matches[0] if matches else None
        return f'''{text}<input name="{name}" value="{value}" type="hidden" />'''


class ReadOnlyInput(forms.TextInput):
    def render(self, name, value, attrs=None, renderer=None):
        attrs = attrs or {}
        attrs['style'] = 'display: none;'
        return f'{xstr(value)}{super().render(name, value, attrs, renderer)}'


class DateInput(forms.DateInput):
    input_type = 'date'
