/**
 * Currency formatting functionality for CurrencyInput widget
 * Formats input as US currency with $ sign and commas on blur
 * Strips formatting before form submission to ensure proper validation
 */

function formatUSCurrency(value) {
    if (!value) return '';

    // Remove all non-numeric characters except decimal point and minus sign
    let cleanValue = value.toString().replace(/[^\d.-]/g, '');

    // Parse as float
    let num = parseFloat(cleanValue);
    if (isNaN(num)) return '';

    // Check if the number is a whole number
    const isWholeNumber = num % 1 === 0;

    // Format as US currency with commas, only show decimals if not a whole number
    return '$' + num.toLocaleString('en-US', {
        minimumFractionDigits: isWholeNumber ? 0 : 2,
        maximumFractionDigits: 2
    });
}

function stripCurrencyFormatting(value) {
    if (!value) return '';
    // Remove $ sign and commas, keep only numbers, decimal point, and minus sign
    return value.toString().replace(/[$,]/g, '');
}

// Initialize currency formatting when DOM is ready
document.addEventListener('DOMContentLoaded', function() {
    // Find all currency input fields
    const currencyInputs = document.querySelectorAll('input.currency-input');

    currencyInputs.forEach(function(input) {
        // Format on blur (when field loses focus)
        input.addEventListener('blur', function() {
            const formattedValue = formatUSCurrency(input.value);
            if (formattedValue) {
                input.value = formattedValue;
            }
        });

        // Strip formatting on focus (when field gains focus for editing)
        input.addEventListener('focus', function() {
            input.value = stripCurrencyFormatting(input.value);
        });

        // Also format on page load if there's an initial value
        if (input.value) {
            input.value = formatUSCurrency(input.value);
        }
    });

    // Strip formatting before form submission
    document.addEventListener('submit', function(e) {
        const form = e.target;
        const currencyFields = form.querySelectorAll('input.currency-input');

        currencyFields.forEach(function(field) {
            // Strip formatting so Django receives plain numbers
            field.value = stripCurrencyFormatting(field.value);
        });
    });
});

// Also handle dynamically added currency inputs
document.addEventListener('focusin', function(e) {
    if (e.target.classList.contains('currency-input')) {
        e.target.value = stripCurrencyFormatting(e.target.value);
    }
});

document.addEventListener('focusout', function(e) {
    if (e.target.classList.contains('currency-input')) {
        const formattedValue = formatUSCurrency(e.target.value);
        if (formattedValue) {
            e.target.value = formattedValue;
        }
    }
});
