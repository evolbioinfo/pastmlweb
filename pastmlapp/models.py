import uuid as uuid

from django.db import models
from django.db.models import SET_NULL
from pastml.acr import COPY
from pastml.ml import MPPA, MAP, JOINT, ML, ALL
from pastml.models.f81_like import F81, JC, EFT
from pastml.parsimony import ACCTRAN, DELTRAN, DOWNPASS, MP

MODEL_CHOICES = (
    (F81, 'F81 (Felsenstein 1981)'),
    (JC, 'JC (Jukes-Cantor)'),
    (EFT, 'EFT (estimate-from-tips)'),
)

METHOD_CHOICES = (
    (MPPA, 'max likelihood: MPPA (marginal posterior probabilities approximation)'),
    (MAP, 'max likelihood: MAP (maximum a posteriori)'),
    (JOINT, 'max likelihood: joint'),
    (ML, 'max likelihood: ML (apply all available max likelihood methods)'),
    (ACCTRAN, 'max parsimony: ACCTRAN (accelerated transformation)'),
    (DELTRAN, 'max parsimony: DELTRAN (delayed transformation)'),
    (DOWNPASS, 'max parsimony: DOWNPASS'),
    (MP, 'max likelihood: MP (apply all available max parsimony methods)'),
    (ALL, 'all: ALL (apply all available methods)'),
    (COPY, 'as-is: COPY (copy node states from the annotation table)'),
)


class TreeData(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    tree = models.FileField(upload_to='',
                            help_text=u'A <b>rooted</b> tree (in <a href=https://en.wikipedia.org/wiki/Newick_format '
                                      u'target=_blank>Newick</a> format).')

    data = models.FileField(upload_to='',
                            help_text=u'An annotation table specifying tip states '
                                      u'(in <a href="https://en.wikipedia.org/wiki/Comma-separated_values" '
                                      u'target="_blank">CSV</a> format). '
                                      u'You will be asked to choose columns of interest at the next step.')
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

    model = models.CharField(max_length=4, default=F81, choices=MODEL_CHOICES,
                             help_text=u'Evolutionary model for state changes (for max likelihood methods only).')
    prediction_method = models.CharField(max_length=128, default=MPPA, choices=METHOD_CHOICES,
                                         help_text=u'Ancestral state prediction method.')

    email = models.EmailField(default=None, blank=True, null=True,
                              help_text=u"If specified, you'll receive an email at this address "
                                        u"once the PastML reconstruction is ready.")
    title = models.CharField(max_length=128, default='PastML reconstruction is ready!', blank=True, null=True,
                             help_text=u"The title to be used in the email.")

    html_compressed = models.CharField(max_length=256, default=None, blank=True, null=True)

    created_at = models.DateTimeField(auto_now_add=True)


class Column(models.Model):
    analysis = models.ForeignKey('pastmlapp.Analysis', null=True, on_delete=SET_NULL)

    column = models.CharField(max_length=512,
                              help_text=u'Column containing tip values for the state to be reconstructed with PastML.')

