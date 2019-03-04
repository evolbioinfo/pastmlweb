from shutil import copyfile

from celery.task import task
from celery.utils.log import get_task_logger
from django.urls import reverse

logger = get_task_logger(__name__)


@task(name="send_feedback_email")
def send_feedback_email(email, message):
    """sends an email when feedback form is filled successfully"""
    logger.info("Sent feedback email")
    from django.core.mail import EmailMessage

    email = EmailMessage(subject='PastML web feedback', body=message, to=('anna.zhukova@pasteur.fr', ),
                         attachments=None, headers=None, cc=None, reply_to=(email,))
    return email.send(fail_silently=False)


@task(name="send_analysis_email")
def send_analysis_email(email, url, id, title, columns, model, prediction_method, itol_id, error=None):
    """sends an email when PastML analysis is finished"""
    logger.info("Sent analysis is ready email")
    from django.core.mail import EmailMessage
    from pastml.ml import is_ml

    result_url = 'http://{}{}'.format(url, reverse('pastmlapp:detail', args=(id,)))
    help_url = 'http://{}{}'.format(url, reverse('pastmlapp:help'))
    feedback_url = 'http://{}{}'.format(url, reverse('pastmlapp:feedback'))
    itol_url = 'http://itol.embl.de/external.cgi?tree={}'.format(itol_id) if itol_id else None

    if not error:
        body = """Dear PastML user,

You PastML ancestral scenario reconstruction is now ready and available at {url}. {itol}
We reconstructed ancestral characters with {method} for {columns}.

If you want to know more about PastML ancestral character reconstruction and visualisation algorithms please have a look at our help page: {help}.

If you have experienced any problem or have suggestions on how to improve PastML, 
please contact us via the feedback form ({feedback}) or send an email to anna.zhukova@pasteur.fr.

Kind regards,
PastML team

--
Evolutionary Bioinformatics
C3BI, USR 3756 IP CNRS
Paris, France
""".format(url=result_url, help=help_url, feedback=feedback_url, columns=', '.join(columns),
           method='{} (model {})'.format(prediction_method, model) if is_ml(prediction_method) else prediction_method,
           itol='The full tree visualisation is also available on iTOL: {}.'.format(itol_url) if itol_url else '')

    else:
        body = """Dear PastML user,

Unfortunately we did not manage to reconstruct the ancestral scenario for your data (see {url}{itol}).
We tried to perform ancestral character reconstruction with {method} for {columns}, but got the following error:
"{error}"

Please make sure that your input data was correctly formatted (see our help page: {help} for input data format). 

On our side, we were informed about this problem and are trying to fix it. 
If you wish to give us any additional details, please contact us via the feedback form ({feedback}) or send an email to anna.zhukova@pasteur.fr.

Kind regards,
PastML team

--
Evolutionary Bioinformatics
C3BI, USR 3756 IP CNRS
Paris, France
""".format(url=result_url, help=help_url, feedback=feedback_url, columns=', '.join(columns),
               method='{} (model {})'.format(prediction_method, model) if is_ml(
                   prediction_method) else prediction_method, error=error,
           itol=', {}'.format(itol_url) if itol_url else '')

    email = EmailMessage(subject='Your PastML analysis is ready' if not title else title,
                         body=body,
                         to=(email, ), attachments=None, headers=None, cc=None,
                         bcc=('anna.zhukova@pasteur.fr', ) if error else None)
    return email.send(fail_silently=False)


@task(name="apply_pastml")
def apply_pastml(id, data, tree, data_sep, id_index, columns, date_column, model, prediction_method, name_column,
                 html_compressed, email, title, url, work_dir):
    try:
        from pastml.acr import pastml_pipeline
        from pastml.tree import read_tree
        import os
        import shutil
        html = None
        if len(read_tree(tree)) <= 500:
            html = os.path.join(work_dir, 'pastml_tree.html')

        pastml_pipeline(tree=tree, data=data, data_sep=data_sep, id_index=id_index, columns=columns,
                        date_column=date_column if date_column else None,
                        model=model, prediction_method=prediction_method, name_column=name_column,
                        html_compressed=html_compressed, html=html, verbose=True, work_dir=work_dir,
                        upload_to_itol=True, itol_id='ZxuhG2okfKLQnsgd5xAEGQ', itol_project='pastmlweb',
                        itol_tree_name=id)
        itol_id = None
        itol_id_file = os.path.join(work_dir, 'iTOL_id.txt')
        if os.path.exists(itol_id_file):
            with open(os.path.exists(itol_id_file), 'r') as f:
                itol_id = f.readline()
            copyfile(itol_id_file, os.path.join(work_dir, '..', 'pastml_{}_itol.txt'.format(id)))
        shutil.make_archive(os.path.join(work_dir, '..', 'pastml_{}'.format(id)), 'zip', work_dir)
        try:
            shutil.rmtree(work_dir)
        except:
            pass
        if email:
            send_analysis_email.delay(email, url, id, title, columns, model, prediction_method, itol_id, None)
    except Exception as e:
        e_str = str(e)
        with open(html_compressed, 'w+') as f:
            f.write('<p>Could not reconstruct the states...<br/>{}</p>'.format(e_str))
        if email:
            send_analysis_email.delay(email, url, id, title, columns, model, prediction_method, itol_id, e_str)
        else:
            send_analysis_email.delay('anna.zhukova@pasteur.fr', url, id, title, columns, model, prediction_method,
                                      itol_id, e_str)
        raise e
