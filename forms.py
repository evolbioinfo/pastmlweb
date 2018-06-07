from django import forms
from django.core.exceptions import NON_FIELD_ERRORS

from pastmlapp.models import TreeData, Analysis, Column
from pastmlapp.tasks import send_feedback_email_task
from django.forms import ModelForm, CharField, HiddenInput

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
    extra_field_count = CharField(widget=HiddenInput())

    class Meta:
        model = Analysis
        fields = ['date_column', 'model', 'prediction_method', 'email', 'title']

    def __init__(self, *args, **kwargs):
        extra_fields = kwargs.pop('extra', 0)

        super(AnalysisForm, self).__init__(*args, **kwargs)
        td = TreeData.objects.get(pk=self.instance.tree_data.id)
        self.column_choices = tuple((str(_), str(_))
                                 for _ in pd.read_table(td.data.url, sep=td.data_sep,
                                                        index_col=td.id_index, header=0).columns)

        self.fields['date_column'] = forms.ChoiceField(required=False, choices=((None, ''),) + self.column_choices,
                                                       help_text=u'(optional) Column containing tip dates.')

        columns = Column.objects.filter(
            analysis=self.instance
        )
        extra_fields = max(len(columns) - 1, extra_fields)

        self.fields['extra_field_count'].initial = extra_fields

        for i in range(extra_fields + 1):
            field_name = 'column_{}'.format(i)
            self.fields[field_name] = forms.ChoiceField(required=i == 0, choices=self.column_choices,
                                                        help_text=u'Column containing a{} state to be reconstructed with PASTML.'.format('nother' if i > 0 else ''),
                                                        widget=forms.Select(attrs={'class': 'column-list-new'} if i == len(columns) else {}))
            self.initial[field_name] = columns[i].column if i < len(columns) else self.column_choices[0]

    def clean(self):
        super(AnalysisForm, self).clean()
        columns = set()
        for i in range(int(self.cleaned_data['extra_field_count']) + 1):
            field_name = 'column_{}'.format(i)
            if field_name not in self.cleaned_data:
                continue
            print(i, "({})".format(self.cleaned_data[field_name]))
            column = self.cleaned_data[field_name]
            if column in columns:
                self.add_error(field_name, 'Duplicate')
            elif not column:
                self.add_error(field_name, 'Empty column {}'.format(i))
            else:
                columns.add(column)

        self.cleaned_data["columns"] = columns

    def save(self, commit=True):
        super(AnalysisForm, self).save(commit=commit)
        analysis = self.instance

        for _ in self.cleaned_data["columns"]:
            Column.objects.create(
                analysis=analysis,
                column=_,
            )

    def get_column_fields(self):
        for field_name in self.fields:
            if field_name.startswith('column_'):
                yield self[field_name]
