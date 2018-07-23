import uuid as uuid
from django.db import models
from django.db.models import SET_NULL

MODEL_CHOICES = (
    ('F81', 'F81 (Felsenstein 1981)'),
    ('JC', 'JC (Jukes-Cantor)'),
    ('EFT', 'EFT (estimate-from-tips)'),
)

METHOD_CHOICES = (
    ('marginal_approx', 'max likelihood: MPPA (marginal posterior probabilities approximation)'),
    ('max_posteriori', 'max likelihood: MAP (maximum a posteriori)'),
    ('joint', 'max likelihood: joint'),
    # ('marginal', 'max likelihood: marginal'),
    ('acctran', 'max parsimony: ACCTRAN'),
    ('deltran', 'max parsimony: DELTRAN'),
    ('downpass', 'max parsimony: DOWNPASS'),
)


class TreeData(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    tree = models.FileField(upload_to='',
                            help_text=u'A rooted tree (in <a href=https://en.wikipedia.org/wiki/Newick_format '
                                      u'target=_blank>Newick</a> format).')

    data = models.FileField(upload_to='',
                            help_text=u'An annotation table specifying tip states '
                                      u'(in <a href="https://en.wikipedia.org/wiki/Comma-separated_values" '
                                      u'target="_blank">CSV</a> format).')
    data_sep = models.CharField(max_length=8, default='<tab>', blank=True, null=True,
                                help_text=u'Separator for the annotation table (default is "&lt;tab&gt;", '
                                          u'for a comma-separated file put ",").')

    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return "tree {}, data {}"\
            .format(self.tree, self.data)


class Analysis(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    tree_data = models.ForeignKey('pastmlapp.TreeData', null=True, on_delete=SET_NULL)

    id_column = models.IntegerField(default=0,
                                    help_text=u'The number of the column in the annotation file '
                                              u'containing the tip ids (by default 0, e.g. the first column).')

    date_column = models.CharField(max_length=128, default=None, blank=True, null=True,
                                   help_text=u'(optional) Column containing tip dates.')

    model = models.CharField(max_length=4, default='F81', choices=MODEL_CHOICES,
                             help_text=u'Evolutionary model for state changes (for max likelihood methods only).')
    prediction_method = models.CharField(max_length=128, default='marginal_approx', choices=METHOD_CHOICES,
                                         help_text=u'Ancestral state prediction method.')

    email = models.EmailField(default=None, blank=True, null=True,
                              help_text=u"If specified, you'll receive an email at this address "
                                        u"once the PASTML reconstruction is ready.")
    title = models.CharField(max_length=128, default='PASTML is ready!', blank=True, null=True,
                             help_text=u"The title to be used in the email.")

    html_compressed = models.CharField(max_length=256, default=None, blank=True, null=True)

    created_at = models.DateTimeField(auto_now_add=True)


class Column(models.Model):
    analysis = models.ForeignKey('pastmlapp.Analysis', null=True, on_delete=SET_NULL)

    column = models.CharField(max_length=512,
                              help_text=u'Column containing tip values for the state to be reconstructed with PASTML.')

