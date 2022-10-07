from formtools.wizard.views import NamedUrlSessionWizardView

from django_reusable.forms import forms
from .models import Person


class MusicianWizardView(NamedUrlSessionWizardView):
    class FirstForm(forms.Form):
        persons = forms.ModelMultipleChoiceField(queryset=Person.objects)

    form_list = [
        ('first', FirstForm)
    ]

    def done(self, form_list, **kwargs):
        pass

