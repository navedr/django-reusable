import json


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

    return ' • '.join(lines) if lines else "No address entered"
