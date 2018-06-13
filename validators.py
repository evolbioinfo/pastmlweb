def validate_file_extension(value, valid_extensions, format='the correct'):
    import os
    from django.core.exceptions import ValidationError
    ext = os.path.splitext(value.name)[1]  # [0] returns path+filename
    if not ext.lower() in valid_extensions:
        raise ValidationError(u'According to the extension ({}) your file ({}) does not seem to be in {} format.'.format(ext, value, format))


def validate_nwk_file_extension(value):
    validate_file_extension(value, ['.nwk', '.newick', '.tre', '.tree', '.txt'], 'newick')