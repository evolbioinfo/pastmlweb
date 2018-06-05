from django.db import models
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


class Question(models.Model):
    data = models.FileField(upload_to='documents/')
    tree = models.FileField(upload_to='documents/', validators=[validate_nwk_file_extension])

    data_sep = models.CharField(max_length=8, default='\t', blank=True, null=True)
    id_index = models.IntegerField(default=0)
    columns = models.CharField(max_length=512, default=None, blank=True, null=True)
    copy_columns = models.CharField(max_length=512, default=None, blank=True, null=True)
    date_column = models.CharField(max_length=128, default=None, blank=True, null=True)
    name_column = models.CharField(max_length=128, default=None, blank=True, null=True)
    model = models.CharField(max_length=4, default='F81', choices=MODEL_CHOICES)
    prediction_method = models.CharField(max_length=128, default='marginal_approx', choices=METHOD_CHOICES)
    tip_size_threshold = models.PositiveIntegerField(default=15)

    email = models.EmailField(default=None, blank=True, null=True)
    title = models.CharField(max_length=128, default='PASTML')

    created_at = models.DateTimeField(auto_now_add=True)
    html_compressed = models.CharField(max_length=256, default=None, blank=True, null=True)

    def __str__(self):
        return "Tree {}, data {}, columns {}, model {}, method {}"\
            .format(self.tree, self.data, self.columns, self.model, self.prediction_method)
