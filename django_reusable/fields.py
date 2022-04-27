from django import forms


class ChoiceFieldNoValidation(forms.ChoiceField):
    """
    An override of django's ChoiceField to ignore validation of the choices.
    Primarily used for cases where the choice fields are assigned options dynamically on the page.
    """
    def validate(self, value):
        pass