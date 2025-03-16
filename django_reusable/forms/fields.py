from django import forms


class ChoiceFieldNoValidation(forms.ChoiceField):
    """
    An override of django's ChoiceField to ignore validation of the choices.
    Primarily used for cases where the choice fields are assigned options dynamically on the page.
    """

    def validate(self, value):
        """
        Overrides the validate method to bypass validation of the choices.

        Args:
            value (str): The value to be validated.

        Returns:
            None
        """
        pass
