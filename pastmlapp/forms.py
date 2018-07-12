import os
from collections import OrderedDict

from django import forms
from django.core.exceptions import NON_FIELD_ERRORS
from ete3 import Tree
from multiselectfield import MultiSelectFormField

from pastmlapp.models import TreeData, Analysis, Column
from pastmlapp.tasks import send_feedback_email
from django.forms import ModelForm, CharField, EmailField, widgets

import pandas as pd


class FeedbackForm(forms.Form):
    error_css_class = "error"
    email = EmailField(label="Email Address", help_text=u'Your email address.')
    message = CharField(label="Message", widget=forms.Textarea(attrs={'rows': 5}))

    def send_email(self):
        return send_feedback_email.delay(self.cleaned_data['email'], self.cleaned_data['message']).id


# Create the form class.
class TreeDataForm(ModelForm):
    error_css_class = "error"

    class Meta:
        model = TreeData
        fields = ['tree', 'data', 'data_sep']
        error_messages = {
            NON_FIELD_ERRORS: {
                'unique_together': "%(model_name)s's %(field_labels)s are not unique.",
            }
        }

        widgets = {
            'data': forms.FileInput(attrs={'id': 'csv'}),
            'tree': forms.FileInput(attrs={'id': 'nwk'}),
        }

    def clean(self):
        cleaned_data = super().clean()

        sep = cleaned_data.get('data_sep', '\t')
        if not sep or sep == '<tab>':
            self.cleaned_data['data_sep'] = '\t'
            sep = '\t'

        f = cleaned_data.get('tree', None)
        if f:
            f = f.file  # the file in Memory
            tree, tree_str = None, None
            try:
                tree_str = f.read().decode()
                for format in range(10):
                    try:
                        tree = Tree(tree_str, format=format)
                        break
                    except:
                        pass
            except:
                pass
            if not tree:
                self.add_error('tree',
                               u'Your tree does not seem to be in Newick format.')

        f = cleaned_data.get('data', None)
        if f:
            f = f.file
            try:
                df = pd.read_table(f, sep=sep, header=0)
                if len(df.columns) < 2:
                    get_col_name = lambda _: '"{}..."'.format(_[:10]) if len(_) > 10 else '"{}"'.format(_)
                    self.add_error('data', u'Your annotation table contains {} column: {}, '
                                           u'while it must contain at least 2: tip ids and their states. '
                                           u'Please check if the separator ("{}") is correct.'
                                   .format(len(df.columns), ', '.join(get_col_name(_) for _ in df.columns),
                                           '<tab>' if sep == '\t' else sep))
            except:
                self.add_error('data', u'We could not parse your annotation table, '
                                       u'please check if the separator ("{}") is correct.'
                               .format('<tab>' if sep == '\t' else sep))
        return cleaned_data


class AnalysisForm(ModelForm):
    error_css_class = "error"

    class Meta:
        model = Analysis
        fields = ['model', 'prediction_method', 'email', 'title']

    def __init__(self, data=None, *args, **kwargs):
        super(AnalysisForm, self).__init__(data, *args, **kwargs)
        td = TreeData.objects.get(pk=self.instance.tree_data.id)
        self.column_choices = tuple((str(_), str(_))
                                    for _ in pd.read_table(td.data.path, sep=td.data_sep, header=0).columns)

        self.fields['tip_id_column'] = forms.ChoiceField(required=True, choices=self.column_choices,
                                                         help_text=u'Column containing tip ids.')

        multi_column = len(self.column_choices) > 2

        self.fields['column(s)' if multi_column else 'column'] = \
            MultiSelectFormField(choices=self.column_choices, max_choices=6, min_choices=1,
                                 help_text=u'Column(s) whose ancestral states are to be reconstructed.',
                                 widget=widgets.SelectMultiple) \
                if multi_column else \
                forms.ChoiceField(required=True, choices=self.column_choices,
                                  help_text=u'Column whose ancestral states are to be reconstructed.',
                                  initial=self.column_choices[1])

        if multi_column:
            self.fields['date_column'] = forms.ChoiceField(required=False, choices=((None, ''),) + self.column_choices,
                                                           help_text=u'(optional) Column containing tip dates.')
        self.fields.keyOrder = ['tip_id_column'] + (['column(s)', 'date_column'] if multi_column else ['column']) \
                               + ['model', 'prediction_method', 'email', 'title']
        self.fields = OrderedDict((k, self.fields[k]) for k in self.fields.keyOrder)

        if data and data.get('prediction_method', None) in ['marginal_approx', 'max_posteriori', 'joint', 'marginal']:
            self.fields['model'].widget.attrs['disabled'] = 'false'
        else:
            self.fields['model'].widget.attrs['disabled'] = 'true'

    def save(self, commit=True):
        self.cleaned_data['id_column'] = next(i for (i, (c, _)) in enumerate(self.column_choices)
                                              if c == self.cleaned_data['tip_id_column'])
        super(AnalysisForm, self).save(commit=commit)
        analysis = self.instance

        for _ in self.cleaned_data["column(s)"] if "column(s)" in self.cleaned_data else [self.cleaned_data['column']]:
            Column.objects.create(
                analysis=analysis,
                column=_,
            )
