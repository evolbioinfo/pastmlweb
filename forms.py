from django import forms
from django.core.exceptions import NON_FIELD_ERRORS

from pastmlapp.tasks import send_feedback_email_task
from django.forms import ModelForm
from pastmlapp.models import Question


class FeedbackForm(forms.Form):
    email = forms.EmailField(label="Email Address")
    message = forms.CharField(
        label="Message", widget=forms.Textarea(attrs={'rows': 5}))
    honeypot = forms.CharField(widget=forms.HiddenInput(), required=False)

    def send_email(self):
        # try to trick spammers by checking whether the honeypot field is
        # filled in; not super complicated/effective but it works
        if self.cleaned_data['honeypot']:
            return False
        send_feedback_email_task.delay(
            self.cleaned_data['email'], self.cleaned_data['message'])


# Create the form class.
class QuestionForm(ModelForm):
    class Meta:
        model = Question
        fields = ['data', 'tree', 'email', 'data_sep', 'id_index', 'columns', 'date_column',
        'name_column', 'model', 'prediction_method', 'title']
        error_messages = {
            NON_FIELD_ERRORS: {
                'unique_together': "%(model_name)s's %(field_labels)s are not unique.",
            }
        }

        widgets = {
            'data': forms.FileInput(attrs={'class': 'csv'}),
            'tree': forms.FileInput(attrs={'class': 'nwk'}),
            'email': forms.EmailInput(attrs={'class': 'email'}),
        }