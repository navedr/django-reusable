# Google Places API Integration for USAddressField

This document explains how to set up and use Google Places API integration with the USAddressField for enhanced address autocomplete functionality.

## Features

The USAddressField now includes optional Google Places API integration that provides:

- **Real-time address suggestions** as users type in the street address field
- **Automatic field population** when a user selects an address suggestion
- **US-only address restriction** for relevant results
- **Graceful fallback** when API key is not configured

## Setup Instructions

### 1. Get a Google Places API Key

1. Go to the [Google Cloud Console](https://console.cloud.google.com/)
2. Create a new project or select an existing one
3. Enable the **Places API**
4. Create credentials (API key)
5. Restrict the API key to your domain for security

### 2. Configure Django Settings

Add your Google Places API key to your Django settings:

```python
# settings.py

# Google Places API configuration
GOOGLE_PLACES_API_KEY = 'your-google-places-api-key-here'
```

**Security Note:** Never commit your API key to version control. Use environment variables:

```python
import os

GOOGLE_PLACES_API_KEY = os.environ.get('GOOGLE_PLACES_API_KEY')
```

### 3. Set Environment Variable

```bash
# In your .env file or environment
export GOOGLE_PLACES_API_KEY=your-actual-api-key-here
```

## How It Works

### With API Key Configured

When `GOOGLE_PLACES_API_KEY` is set in Django settings:

1. **Google Places script loads** automatically
2. **Street address field becomes autocomplete-enabled**
3. **User types** in the street address field
4. **Google suggests addresses** in a dropdown
5. **User selects an address** from suggestions
6. **All fields auto-populate**:
   - Street Address (street number + route)
   - City (locality)
   - State (administrative_area_level_1, shortened)
   - ZIP Code (postal_code)

### Without API Key

When no API key is configured:

1. **No Google script loads** (saves bandwidth)
2. **Fallback ZIP code lookup** provides basic city/state suggestions
3. **Standard browser autocomplete** still works where supported
4. **User sees informational message** about enabling Google Places

## Usage Examples

### Basic Model Usage

```python
from django.db import models
from django_reusable.models.fields import USAddressField

class Company(models.Model):
    name = models.CharField(max_length=200)
    address = USAddressField()  # Automatically uses Google Places if configured
```

### Form Usage

```python
from django import forms
from django_reusable.forms.fields import USAddressFormField

class AddressForm(forms.Form):
    home_address = USAddressFormField()  # Google Places integration included
    work_address = USAddressFormField(required=False)
```

### Admin Integration

The field works automatically in Django admin:

```python
from django.contrib import admin
from .models import Company

@admin.register(Company)
class CompanyAdmin(admin.ModelAdmin):
    fields = ['name', 'address']  # Google Places autocomplete will be active
```

## Technical Details

### Address Component Mapping

Google Places API components are mapped to form fields as follows:

| Google Component | Form Field | Description |
|------------------|------------|-------------|
| `street_number` + `route` | `street_address` | Combined street number and street name |
| `locality` | `city` | City name |
| `administrative_area_level_1` | `state` | State abbreviation (e.g., "CA") |
| `postal_code` | `zip_code` | ZIP code |

### Restrictions Applied

- **Country restriction**: US only (`componentRestrictions: { country: 'us' }`)
- **Type restriction**: Addresses only (`types: ['address']`)
- **Field restriction**: Only address components returned for efficiency

### Fallback Behavior

When Google Places is not available, the widget provides:

1. **Manual ZIP code lookup** for common ZIP codes
2. **Standard HTML autocomplete attributes** for browser support
3. **Input formatting** (automatic ZIP code formatting)
4. **Validation** for all address components

## Security Considerations

1. **API Key Restriction**: Restrict your Google Places API key to your specific domain
2. **Rate Limiting**: Google Places API has usage limits - monitor your usage
3. **Environment Variables**: Never hardcode API keys in your source code
4. **HTTPS**: Google Places API requires HTTPS in production

## Troubleshooting

### Common Issues

1. **"Google Places API not loaded"** in console:
   - Check that `GOOGLE_PLACES_API_KEY` is set in settings
   - Verify the API key is valid and Places API is enabled

2. **No autocomplete suggestions**:
   - Verify API key has correct permissions
   - Check browser developer tools for JavaScript errors
   - Ensure you're testing with valid US addresses

3. **API key errors**:
   - Check Google Cloud Console for API usage and errors
   - Verify the API key is properly restricted but allows your domain

### Testing

To test the integration:

1. **Without API key**: Should show fallback message and basic functionality
2. **With valid API key**: Should show green success message and autocomplete
3. **Try typing**: "1600 Pennsylvania Ave" should suggest the White House

## Cost Considerations

Google Places API is a paid service:
- **Autocomplete requests**: Charged per request
- **Place details**: Charged per detail request
- **Free tier**: Google provides monthly credits

Monitor usage in Google Cloud Console and set up billing alerts.
