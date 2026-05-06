from django import forms
import json

from .widgets import USAddressWidget, CurrencyInput


class ChoiceFieldNoValidation(forms.ChoiceField):
    """ChoiceField that skips server-side choice validation.

    Use when choices are populated dynamically via JavaScript on the client side,
    so the submitted value may not be in the server-defined choices list.

    Example:
        ```python
        class MyForm(forms.Form):
            category = ChoiceFieldNoValidation(choices=[])
        ```
    """

    def validate(self, value):
        pass


class CheckboxMultipleChoiceField(forms.MultipleChoiceField):
    """MultipleChoiceField that renders as checkboxes and handles JSON serialization.

    Used as the default form field for ``MultipleChoiceField`` (model field).
    Accepts and produces Python lists; handles JSON string input from the
    database transparently.
    """
    widget = forms.CheckboxSelectMultiple

    def __init__(self, *args, **kwargs):
        kwargs.pop('max_length', None)
        kwargs.pop('widget', None)  # We use our own widget
        super().__init__(*args, **kwargs)

    def to_python(self, value):
        """Override to handle JSON string values properly"""
        if not value:
            return []

        # If it's already a list, return it
        if isinstance(value, list):
            return [str(item) for item in value]

        # If it's a JSON string, parse it
        if isinstance(value, str):
            try:
                parsed = json.loads(value)
                if isinstance(parsed, list):
                    return [str(item) for item in parsed]
                else:
                    return [str(parsed)]
            except json.JSONDecodeError:
                return [str(value)]

        return [str(value)]

    def validate(self, value):
        """Override validation to handle our custom data format"""
        if self.required and not value:
            raise forms.ValidationError(self.error_messages['required'], code='required')

        # Validate each choice
        if value and self.choices:
            valid_choices = [str(choice[0]) for choice in self.choices]
            for item in value:
                if str(item) not in valid_choices:
                    raise forms.ValidationError(
                        self.error_messages['invalid_choice'],
                        code='invalid_choice',
                        params={'value': item},
                    )

    def widget_attrs(self, widget):
        attrs = super().widget_attrs(widget)
        if isinstance(widget, forms.CheckboxSelectMultiple):
            attrs['class'] = (attrs.get('class', '') + ' unstyled').strip()
        return attrs


class USAddressFormField(forms.Field):
    """Form field for US addresses with multi-component input and validation.

    Renders as five separate inputs (street, street line 2, city, state dropdown,
    ZIP code) via ``USAddressWidget``. Produces a dict with keys
    ``street_address``, ``street_address_2``, ``city``, ``state``, ``zip_code``.

    Validates that required address components are present, state is a 2-letter
    code, and ZIP matches ``XXXXX`` or ``XXXXX-XXXX`` format.

    This is the default form field for ``USAddressField`` (model field) and
    is normally not used directly.
    """
    widget = USAddressWidget

    def __init__(self, *args, **kwargs):
        # Remove TextField-specific parameters that this form field doesn't use
        kwargs.pop('max_length', None)
        kwargs.pop('widget', None)  # We use our own widget
        super().__init__(*args, **kwargs)

    def to_python(self, value):
        """Convert form data to Python object"""
        if not value:
            return None

        if isinstance(value, dict):
            # Clean empty values
            cleaned_value = {}
            for key, val in value.items():
                if val and val.strip():
                    cleaned_value[key] = val.strip()

            # Return None if no meaningful data
            if not any(cleaned_value.values()):
                return None

            return cleaned_value

        return value

    def validate(self, value):
        """Validate the address data"""
        super().validate(value)

        if not value and self.required:
            raise forms.ValidationError("Address is required.")

        if not value:
            return

        # Validate required fields
        required_fields = {
            'street_address': 'Street address',
            'city': 'City',
            'state': 'State',
            'zip_code': 'ZIP code'
        }

        for field, display_name in required_fields.items():
            if field not in value or not value[field]:
                raise forms.ValidationError(f"{display_name} is required.")

        # Validate state format (2-letter code)
        if len(value['state']) != 2:
            raise forms.ValidationError("State must be a 2-letter code.")

        # Basic zip code validation
        zip_code = str(value['zip_code'])
        if not (len(zip_code) == 5 and zip_code.isdigit()) and not (
                len(zip_code) == 10 and zip_code[5] == '-' and
                zip_code[:5].isdigit() and zip_code[6:].isdigit()
        ):
            raise forms.ValidationError("ZIP code must be in format 12345 or 12345-6789.")

    def prepare_value(self, value):
        """Prepare value for display in the widget"""
        if isinstance(value, str):
            try:
                return json.loads(value)
            except json.JSONDecodeError:
                return None
        return value


class CurrencyFormField(forms.DecimalField):
    """DecimalField for currency input with client-side formatting.

    Defaults to ``max_digits=10`` and ``decimal_places=2``. Uses
    ``CurrencyInput`` widget which adds ``$`` sign and comma separators via
    JavaScript on blur.

    This is the default form field for ``CurrencyField`` (model field).
    """
    def __init__(self, *args, **kwargs):
        kwargs['max_digits'] = kwargs.get('max_digits', 10)
        kwargs['decimal_places'] = kwargs.get('decimal_places', 2)
        kwargs['widget'] = kwargs.get('widget', CurrencyInput())
        super().__init__(*args, **kwargs)
