from django import forms
from django.core.exceptions import NON_FIELD_ERRORS
from multiselectfield import MultiSelectFormField

from pastmlapp.models import TreeData, Analysis, Column
from pastmlapp.tasks import send_feedback_email_task
from django.forms import ModelForm, CharField, HiddenInput, widgets

import pandas as pd


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
class TreeDataForm(ModelForm):
    class Meta:
        model = TreeData
        fields = ['tree', 'data', 'data_sep', 'id_index']
        error_messages = {
            NON_FIELD_ERRORS: {
                'unique_together': "%(model_name)s's %(field_labels)s are not unique.",
            }
        }

        widgets = {
            'data': forms.FileInput(attrs={'class': 'csv'}),
            'tree': forms.FileInput(attrs={'class': 'nwk'}),
        }


# Create the form class.
class AnalysisForm(ModelForm):
    class Meta:
        model = Analysis
        fields = ['date_column', 'model', 'prediction_method', 'email', 'title']

    def __init__(self, *args, **kwargs):
        super(AnalysisForm, self).__init__(*args, **kwargs)
        td = TreeData.objects.get(pk=self.instance.tree_data.id)
        column_choices = tuple((str(_), str(_))
                               for _ in pd.read_table(td.data.url, sep=td.data_sep,
                                                      index_col=td.id_index, header=0).columns)

        self.fields['date_column'] = forms.ChoiceField(required=False, choices=((None, ''),) + column_choices,
                                                       help_text=u'(optional) Column containing tip dates.')

        self.fields['column'] = MultiSelectFormField(choices=column_choices, max_choices=6, min_choices=1,
                                                     help_text=u'Column(s) whose ancestral states are to be reconstructed.',
                                                     widget=widgets.SelectMultiple)

    def save(self, commit=True):
        super(AnalysisForm, self).save(commit=commit)
        analysis = self.instance

        for _ in self.cleaned_data["column"]:
            Column.objects.create(
                analysis=analysis,
                column=_,
            )
