import json
from django.db import models
from django.core.exceptions import ValidationError

from .lookups import JSONExtract
from ..utils.address_utils import format_us_address
from django_reusable.forms.fields import USAddressFormField, CheckboxMultipleChoiceField, CurrencyFormField


class MultipleChoiceField(models.TextField):
    """Model field that stores multiple choice selections as a JSON array.

    Stores values as a JSON array in a TextField (e.g. ``["Admin", "User"]``).
    Renders as checkboxes in forms via ``CheckboxMultipleChoiceField``. Automatically
    adds a ``get_<field>_display()`` method to the model that returns a
    comma-separated string of selected values.

    Example:
        ```python
        class Person(TimeStampedModel):
            roles = MultipleChoiceField(
                choices=[('Admin', 'Admin'), ('User', 'User'), ('Guest', 'Guest')],
                null=True, blank=True, default=['Guest'],
            )

        person = Person.objects.first()
        person.roles                  # ['Admin', 'User']
        person.get_roles_display()    # 'Admin, User'
        ```
    """

    description = "A field for storing multiple choice selections as JSON array"

    def __init__(self, choices=None, *args, **kwargs):
        # Pass choices to the parent class so Django handles them properly
        if choices is not None:
            kwargs['choices'] = choices
        super().__init__(*args, **kwargs)

    def from_db_value(self, value, expression, connection):
        """Convert database value to Python object"""
        if value is None:
            return []
        if isinstance(value, str):
            try:
                result = json.loads(value)
                return result if isinstance(result, list) else []
            except json.JSONDecodeError:
                return []
        return value if isinstance(value, list) else []

    def to_python(self, value):
        """Convert value to Python object"""
        if isinstance(value, list):
            return value
        if value is None:
            return []
        if isinstance(value, str):
            try:
                result = json.loads(value)
                return result if isinstance(result, list) else []
            except json.JSONDecodeError:
                return []
        return []

    def get_prep_value(self, value):
        """Convert Python object to database value"""
        if value is None:
            return json.dumps([])
        if isinstance(value, list):
            return json.dumps(value)
        return json.dumps([])

    def validate(self, value, model_instance):
        """Validate the choice selections"""

        if value is None:
            return

        if isinstance(value, str):
            try:
                value = json.loads(value)
            except json.JSONDecodeError:
                raise ValidationError("Invalid JSON format for multiple choice field")

        if not isinstance(value, list):
            raise ValidationError("Multiple choice field must be a list")

        # Validate choices if defined
        if self.choices:
            valid_choices = [choice[0] for choice in self.choices]
            for selected_value in value:
                if selected_value not in valid_choices:
                    raise ValidationError(f"'{selected_value}' is not a valid choice")

    def contribute_to_class(self, cls, name, **kwargs):
        """Called when the field is added to a model class"""
        super().contribute_to_class(cls, name, **kwargs)

        # Add a method to format the address for display
        def get(self):
            try:
                return ', '.join(getattr(self, name))
            except Exception:
                return str(getattr(self, name))

        get.__name__ = name
        setattr(cls, f'get_{name}_display', get)

    def formfield(self, **kwargs):
        # Don't call super().formfield() as TextField will override our form field
        # Instead, directly instantiate our custom form field
        defaults = {
            'choices': self.choices,
            'required': not self.blank,
            'initial': self.get_default(),
        }
        defaults.update(kwargs)

        # Return the form field directly without calling super()
        return CheckboxMultipleChoiceField(**defaults)


class USAddressField(models.TextField):
    """Model field that stores a US address as a JSON object.

    Stored format:

        {"street_address": "123 Main St", "street_address_2": "Apt 4B",
         "city": "New York", "state": "NY", "zip_code": "10001"}

    Renders in forms as five separate inputs (street, street 2, city, state
    dropdown, ZIP) via ``USAddressWidget``. Automatically adds a
    ``get_<field>_display()`` method that returns a formatted address string.

    Supports querying individual components via custom lookups:

    - ``address__city='New York'``
    - ``address__state='NY'``
    - ``address__zip_code='10001'``
    - ``address__city__icontains='new'``

    Example:
        ```python
        class Person(TimeStampedModel):
            home_address = USAddressField(blank=True, null=True)

        person = Person.objects.first()
        person.home_address              # {'street_address': '...', ...}
        person.get_home_address_display() # '123 Main St, New York, NY 10001'

        # Query by component
        Person.objects.filter(home_address__state='NY')
        Person.objects.filter(home_address__city__icontains='york')
        ```
    """

    description = "A field for storing US addresses in JSON format"
    class_lookups = {
        'street_address': JSONExtract.create_instance('street_address'),
        'street_address_2': JSONExtract.create_instance('street_address_2'),
        'city': JSONExtract.create_instance('city'),
        'state': JSONExtract.create_instance('state'),
        'zip_code': JSONExtract.create_instance('zip_code'),
    }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def from_db_value(self, value, expression, connection):
        """Convert database value to Python object"""
        if value is None:
            return value
        if isinstance(value, str):
            try:
                return json.loads(value)
            except json.JSONDecodeError:
                return value
        return value

    def to_python(self, value):
        """Convert value to Python object"""
        if isinstance(value, dict):
            return value
        if value is None:
            return value
        if isinstance(value, str):
            try:
                return json.loads(value)
            except json.JSONDecodeError:
                return value
        return value

    def get_prep_value(self, value):
        """Convert Python object to database value"""
        if value is None:
            return value
        if isinstance(value, dict):
            return json.dumps(value)
        return value

    def validate(self, value, model_instance):
        """Validate the address data"""
        super().validate(value, model_instance)

        if value is None:
            return

        if isinstance(value, str):
            try:
                value = json.loads(value)
            except json.JSONDecodeError:
                raise ValidationError("Invalid JSON format for address")

        if not isinstance(value, dict):
            raise ValidationError("Address must be a dictionary")

        # Validate required fields
        required_fields = ['street_address', 'city', 'state', 'zip_code']
        for field in required_fields:
            if field not in value or not value[field]:
                raise ValidationError(f"Address field '{field}' is required")

        # Validate state format (2-letter code)
        if len(value['state']) != 2:
            raise ValidationError("State must be a 2-letter code")

        # Basic zip code validation
        zip_code = str(value['zip_code'])
        if not (len(zip_code) == 5 or (len(zip_code) == 10 and zip_code[5] == '-')):
            raise ValidationError("Zip code must be in format XXXXX or XXXXX-XXXX")

    def contribute_to_class(self, cls, name, **kwargs):
        """Called when the field is added to a model class"""
        super().contribute_to_class(cls, name, **kwargs)

        # Add a method to format the address for display
        def format_address(self):
            address_value = getattr(self, name)
            return format_us_address(address_value)

        format_address.__name__ = name
        setattr(cls, f'get_{name}_display', format_address)

    def formfield(self, **kwargs):

        # Set our custom form field as the default
        defaults = {'form_class': USAddressFormField}
        defaults.update(kwargs)

        # Call the parent's formfield method with our custom form class
        return super().formfield(**defaults)


class CurrencyField(models.DecimalField):
    """DecimalField pre-configured for currency values.

    Defaults to ``decimal_places=2``. Renders in forms with ``CurrencyInput``,
    which adds client-side ``$`` formatting and comma separators.

    Example:
        ```python
        class Musician(models.Model):
            net_worth = CurrencyField(max_digits=20, decimal_places=2,
                                      null=True, blank=True)
        ```
    """

    description = "A field for storing currency values"

    def __init__(self, *args, **kwargs):
        # Set default max_digits and decimal_places if not provided
        kwargs.setdefault('decimal_places', 2)
        super().__init__(*args, **kwargs)

    def formfield(self, **kwargs):
        # Set our custom form field as the default
        defaults = {'form_class': CurrencyFormField}
        defaults.update(kwargs)

        # Call the parent's formfield method with our custom form class
        return super().formfield(**defaults)
