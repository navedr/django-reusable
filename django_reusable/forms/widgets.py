import os

from django import forms
from django.utils.safestring import mark_safe

from django_reusable.utils import xstr


class FileLinkWidget(forms.TextInput):
    """
    A custom widget that renders a file link if the file exists.

    Args:
        base_path (str): The base path where the files are stored.
        base_url (str): The base URL to access the files.
        attrs (dict, optional): Additional attributes for the widget. Defaults to None.
    """

    def __init__(self, base_path, base_url, attrs=None):
        self.base_path = base_path
        self.base_url = base_url
        super(FileLinkWidget, self).__init__(attrs)

    def get_link(self, value):
        """
        Generates an HTML link to the file if it exists.

        Args:
            value (str): The file name.

        Returns:
            str: The HTML link to the file or an empty string if the file does not exist.
        """
        if value and os.path.exists(os.path.join(self.base_path, value)):
            return mark_safe('<a href="%s" target="_blank" class="btn btn-default">Open</a>' %
                             os.path.join(self.base_url, value))
        return ''

    def render(self, name, value, attrs=None, renderer=None):
        """
        Renders the widget as HTML.

        Args:
            name (str): The name of the widget.
            value (str): The value of the widget.
            attrs (dict, optional): Additional attributes for the widget. Defaults to None.
            renderer (Renderer, optional): The renderer to use. Defaults to None.

        Returns:
            str: The rendered HTML of the widget.
        """
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
    """
    A custom select widget that renders as read-only.
    """

    def render(self, name, value, attrs=None, renderer=None):
        """
        Renders the widget as HTML.

        Args:
            name (str): The name of the widget.
            value (str): The value of the widget.
            attrs (dict, optional): Additional attributes for the widget. Defaults to None.
            renderer (Renderer, optional): The renderer to use. Defaults to None.

        Returns:
            str: The rendered HTML of the widget.
        """
        matches = [t for (v, t) in self.choices if v == value]
        text = matches[0] if matches else None
        return f'''{xstr(text, '---')}<input name="{name}" value="{value}" type="hidden" />'''


class ReadonlyMultiSelect(forms.SelectMultiple):
    """
    A custom multi-select widget that renders as read-only.
    """

    def render(self, name, value, attrs=None, renderer=None):
        """
        Renders the widget as HTML.

        Args:
            name (str): The name of the widget.
            value (str or list): The value of the widget.
            attrs (dict, optional): Additional attributes for the widget. Defaults to None.
            renderer (Renderer, optional): The renderer to use. Defaults to None.

        Returns:
            str: The rendered HTML of the widget.
        """
        value_list = value if isinstance(value, list) or isinstance(value, tuple) else eval(value)
        matches = [t for (v, t) in self.choices if v in value_list]
        text = ', '.join(matches) if matches else None
        attrs = attrs or {}
        attrs['style'] = 'display: none;'
        default_widget = super().render(name, value, attrs, renderer)
        return f'''{xstr(text, '---')}{default_widget}'''


class ReadOnlyInput(forms.TextInput):
    """
    A custom text input widget that renders as read-only.
    """

    def render(self, name, value, attrs=None, renderer=None):
        """
        Renders the widget as HTML.

        Args:
            name (str): The name of the widget.
            value (str): The value of the widget.
            attrs (dict, optional): Additional attributes for the widget. Defaults to None.
            renderer (Renderer, optional): The renderer to use. Defaults to None.

        Returns:
            str: The rendered HTML of the widget.
        """
        attrs = attrs or {}
        attrs['style'] = 'display: none;'
        return f'{xstr(value)}{super().render(name, value, attrs, renderer)}'


class DateInput(forms.DateInput):
    """
    A custom date input widget.
    """
    input_type = 'date'


class SingleCharSplitInput(forms.TextInput):
    """
    A custom text input widget that splits the input into multiple single-character fields.

    Args:
        split (int, optional): The number of single-character fields. Defaults to 2.
        *args: Variable length argument list.
        **kwargs: Arbitrary keyword arguments.
    """

    def __init__(self, split=2, *args, **kwargs):
        self.split = split
        super().__init__(*args, **kwargs)

    def render(self, name, value, attrs=None, renderer=None):
        """
        Renders the widget as HTML.

        Args:
            name (str): The name of the widget.
            value (str): The value of the widget.
            attrs (dict, optional): Additional attributes for the widget. Defaults to None.
            renderer (Renderer, optional): The renderer to use. Defaults to None.

        Returns:
            str: The rendered HTML of the widget.
        """
        attrs = attrs or {}
        split_input_attrs = attrs.copy()
        split_input_attrs.update({
            'minlength': 1,
            'maxlength': 1,
            'style': 'width: 20px; margin-right: 3px;',
            'class': 'form-control split-char',
            'id': '',
        })
        attrs_str = " ".join([f'{k}="{v}"' for (k, v) in split_input_attrs.items()])
        inputs = [f'<input {attrs_str} />' for x in range(0, self.split)]
        attrs['style'] = 'display: none;'
        return '''
                <script>
                    $(document).ready(function () {
                        $('input.split-char').on("keyup", function(){
                            if($(this).val().length == $(this).attr("maxlength")){
                                $(this).next().focus();
                                $("#id_%s").val(Array.from($('input.split-char')).map(x => x.value).join(''));
                            }
                        }); 
                    })
                </script>
               ''' % (name, ) + f'''    
            <div class='single-char-split-inputs'>
                <div>{"".join(inputs)}</div>
                {super().render(name, value, attrs, renderer)}
            </div>
        '''