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
def send_analysis_email(email, url, id, title, columns, model, prediction_method, error=None):
    """sends an email when PastML analysis is finished"""
    logger.info("Sent analysis is ready email")
    from django.core.mail import EmailMessage
    from pastml.ml import is_ml

    result_url = 'http://{}{}'.format(url, reverse('pastmlapp:detail', args=(id,)))
    help_url = 'http://{}{}'.format(url, reverse('pastmlapp:help'))
    feedback_url = 'http://{}{}'.format(url, reverse('pastmlapp:feedback'))

    if not error:
        body = """Dear PastML user,

You PastML ancestral scenario reconstruction is now ready and available at {url} .
We reconstructed the ancestral characters for {columns}, with {method}.

If you want to know more about PastML ancestral character reconstruction and visualisation algorithms please see our help page: {help} .

If you have experienced any problem or have suggestions on how to improve PastML (or just want to share your love for PastML :) ), 
please contact us via the feedback form ({feedback}) or send an email to anna.zhukova@pasteur.fr.

Kind regards,
PastML team

--
Evolutionary Bioinformatics
C3BI, USR 3756 IP CNRS
Paris, France
""".format(url=result_url, help=help_url, feedback=feedback_url, columns=','.join(columns),
           method='{} (model {})'.format(prediction_method, model) if is_ml(prediction_method) else prediction_method)

    else:
        body = """Dear PastML user,

Unfortunately we did not manage to reconstruct the ancestral scenario for your data, you might see more details at {url} .
We tried to perform the ancestral character reconstruction for {columns}, with {method}, but got the following error:
"{error}"

We were informed about this problem and are trying to fix it.

In the meanwhile, you can verify that your input data was correctly formatted (see our help page: {help} for input data format),
and/or contact us via the feedback form ({feedback}) or send an email to anna.zhukova@pasteur.fr to give us any additional details.

Kind regards,
PastML team

--
Evolutionary Bioinformatics
C3BI, USR 3756 IP CNRS
Paris, France
""".format(url=result_url, help=help_url, feedback=feedback_url, columns=','.join(columns),
               method='{} (model {})'.format(prediction_method, model) if is_ml(
                   prediction_method) else prediction_method, error=error)

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
                        date_column=date_column,
                        model=model, prediction_method=prediction_method, name_column=name_column,
                        html_compressed=html_compressed, html=html, verbose=True, work_dir=work_dir)
        shutil.make_archive(os.path.join(work_dir, '..', 'pastml_{}'.format(id)), 'zip', work_dir)
        try:
            shutil.rmtree(work_dir)
        except:
            pass
        if email:
            send_analysis_email.delay(email, url, id, title, columns, model, prediction_method, None)
    except Exception as e:
        e_str = str(e)
        with open(html_compressed, 'w+') as f:
            f.write('<p>Could not reconstruct the states...<br/>{}</p>'.format(e_str))
        if email:
            send_analysis_email.delay(email, url, id, title, columns, model, prediction_method, e_str)
        else:
            send_analysis_email.delay('anna.zhukova@pasteur.fr', url, id, title, columns, model, prediction_method, e_str)
        raise e
