from collections import OrderedDict

import pandas as pd
from django import forms
from django.core.exceptions import NON_FIELD_ERRORS
from django.forms import ModelForm, widgets
from multiselectfield import MultiSelectFormField
from pastml.acr import parse_date
from pastml.ml import is_ml
from pastml.tree import read_forest, read_tree

from pastmlapp.models import TreeData, Analysis, Column

MAX_N_TREES = 5


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
            'tree': forms.FileInput(attrs={'id': 'nwk'})
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
            try:
                nwks = f.read().decode().replace('\n', '').split(';')
                if not nwks:
                    self.add_error('tree',
                                   u'Could not find any trees (in Newick format) in the file.')
                else:
                    n_trees = len([read_tree(nwk + ';') for nwk in nwks[:-1]])
                    if n_trees > MAX_N_TREES:
                        self.add_error('tree',
                                       u'The file contains too many trees ({}), the limit is {}.'
                                       .format(n_trees, MAX_N_TREES))
            except:
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
        fields = ['prediction_method', 'model', 'root_date', 'timeline_type', 'no_trimming']#, 'email', 'title']

    def __init__(self, data=None, *args, **kwargs):
        super(AnalysisForm, self).__init__(data, *args, **kwargs)
        td = TreeData.objects.get(pk=self.instance.tree_data.id)
        self.column_choices = tuple((str(_), str(_))
                                    for _ in pd.read_table(td.data.path, sep=td.data_sep, header=0).columns)

        self.fields['tip_id_column'] = forms.ChoiceField(required=True, choices=self.column_choices,
                                                         help_text=u'Column containing tip ids '
                                                                   u'(in the same format as in the tree).')

        multi_column = len(self.column_choices) > 2

        self.fields['character_column(s)' if multi_column else 'character_column'] = \
            MultiSelectFormField(choices=self.column_choices, max_choices=6, min_choices=1,
                                 help_text=u'Column(s) whose ancestral states are to be reconstructed '
                                           u'(to select multiple columns keep Shift pressed).',
                                 widget=widgets.SelectMultiple) \
                if multi_column else \
                forms.ChoiceField(required=True, choices=self.column_choices,
                                  help_text=u'Column whose ancestral states are to be reconstructed.',
                                  initial=self.column_choices[1])

        self.fields.keyOrder = ['tip_id_column', 'character_column{}'.format('(s)' if multi_column else ''),
                                'prediction_method', 'model', 'root_date', 'timeline_type', 'no_trimming'] #, 'email', 'title']
        self.fields = OrderedDict((k, self.fields[k]) for k in self.fields.keyOrder)

    def clean_prediction_method(self):
        m = self.cleaned_data['prediction_method']
        if not is_ml(m):
            self.fields['model'].required = False
        return m

    def clean_root_date(self):
        root_date = self.cleaned_data.get('root_date', None)
        if root_date:
            try:
                root_dates = [_.strip(' ') for _ in root_date.replace('\t', ' ').split(' ') if _.strip(' ')]
                n_dates = len([parse_date(_) for _ in root_dates])
                n_trees = len(read_forest(TreeData.objects.get(pk=self.instance.tree_data.id).tree.path))
                if 1 < n_dates < n_trees:
                    self.add_error('root_date',
                                   u'Not enough dates for your {} trees.'.format(n_trees))
                root_date = ' '.join(root_dates)
            except ValueError:
                self.add_error('root_date',
                               u'Your root date format is invalid, please use YYYY-mm-dd or float.')
        return root_date

    def save(self, commit=True):
        self.cleaned_data['id_column'] = next(i for (i, (c, _)) in enumerate(self.column_choices)
                                              if c == self.cleaned_data['tip_id_column'])
        super(AnalysisForm, self).save(commit=commit)
        analysis = self.instance

        for _ in self.cleaned_data["character_column(s)"] if "character_column(s)" in self.cleaned_data \
                else [self.cleaned_data['character_column']]:
            Column.objects.create(
                analysis=analysis,
                column=_,
            )
