import json
from django.db import models
from django.core.exceptions import ValidationError
from django.utils.html import format_html


class USAddressField(models.TextField):
    """
    A Django model field for storing US addresses in JSON format.

    The field stores address data as a JSON object with the following structure:
    {
        "street_address": "123 Main St",
        "street_address_2": "Apt 4B",  # Optional
        "city": "New York",
        "state": "NY",
        "zip_code": "10001"
    }
    """

    description = "A field for storing US addresses in JSON format"

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

        setattr(cls, f'get_{name}_display', format_address)

    def formfield(self, **kwargs):
        """Return the form field for this model field"""
        from django_reusable.forms.fields import USAddressFormField

        # Set our custom form field as the default
        defaults = {'form_class': USAddressFormField}
        defaults.update(kwargs)

        # Call the parent's formfield method with our custom form class
        return super().formfield(**defaults)


def format_us_address(address_data):
    """Helper function to format US address data for display"""
    if not address_data:
        return "No address"

    if isinstance(address_data, str):
        try:
            address_data = json.loads(address_data)
        except json.JSONDecodeError:
            return address_data

    if not isinstance(address_data, dict):
        return str(address_data)

    lines = []

    # Add street address
    street = address_data.get('street_address', '').strip()
    if street:
        lines.append(street)

    # Add street address 2 if present
    street2 = address_data.get('street_address_2', '').strip()
    if street2:
        lines.append(street2)

    # Add city, state, zip
    city = address_data.get('city', '').strip()
    state = address_data.get('state', '').strip()
    zip_code = address_data.get('zip_code', '').strip()

    if city or state or zip_code:
        city_state_zip = f"{city}, {state} {zip_code}".strip()
        if city_state_zip != ", ":
            lines.append(city_state_zip)

    return ' • '.join(lines) if lines else "Incomplete address"
