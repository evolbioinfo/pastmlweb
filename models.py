from django.db import models
from django.db.models import SET_NULL

from .validators import validate_nwk_file_extension

MODEL_CHOICES = (
    ('F81', 'F81 (Felsenstein 1981)'),
    ('JC', 'JC (Jukes-Cantor)'),
)

METHOD_CHOICES = (
    ('marginal_approx', 'max likelihood: marginal approximation'),
    ('max_posteriori', 'max likelihood: maximum posteriori'),
    ('joint', 'max likelihood: joint'),
    ('marginal', 'max likelihood: marginal'),
    ('downpass', 'parsimony: downpass'),
    ('acctran', 'parsimony: acctran'),
    ('deltran', 'parsimony: deltran'),
)


class TreeData(models.Model):
    tree = models.FileField(upload_to='documents/', validators=[validate_nwk_file_extension], help_text=u'A <a href=https://en.wikipedia.org/wiki/Newick_format target=_blank>newick</a> file containing a rooted tree')

    data = models.FileField(upload_to='documents/', help_text=u'A file containing the annotations (as a table)')
    data_sep = models.CharField(max_length=8, default='\t', blank=True, null=True, help_text=u'Separator for the annotation file (e.g. put , for a comma-separated file, by default is set to tab)')
    id_index = models.IntegerField(default=0, help_text=u'The number of the column in the annotation file containing the tip ids (by default 0, e.g. the first column).')

    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return "tree {}, data {}"\
            .format(self.tree, self.data)


class Analysis(models.Model):
    tree_data = models.ForeignKey('pastmlapp.TreeData', null=True, on_delete=SET_NULL)

    date_column = models.CharField(max_length=128, default=None, blank=True, null=True, help_text=u'(optional) Column containing tip dates.')

    model = models.CharField(max_length=4, default='F81', choices=MODEL_CHOICES, help_text=u'Evolutionary model for state changes.')
    prediction_method = models.CharField(max_length=128, default='marginal_approx', choices=METHOD_CHOICES, help_text=u'Ancestral state prediction method.')

    email = models.EmailField(default=None, blank=True, null=True, help_text=u"If specified, we'll send an email once the analysis is finished")
    title = models.CharField(max_length=128, default='PASTML', help_text=u"The title to be used in the email.")

    html_compressed = models.CharField(max_length=256, default=None, blank=True, null=True)

    created_at = models.DateTimeField(auto_now_add=True)
    task_id = models.CharField(max_length=32, default=None, blank=True, null=True)


class Column(models.Model):
    analysis = models.ForeignKey('pastmlapp.Analysis', null=True, on_delete=SET_NULL)

    column = models.CharField(max_length=512, help_text=u'Column containing a state to be reconstructed with PASTML.')

