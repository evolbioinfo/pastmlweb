import celery
from celery.task import task
from celery.utils.log import get_task_logger
from django.contrib.sites.models import Site
from django.urls import reverse

logger = get_task_logger(__name__)


@task(name="send_feedback_email")
def send_feedback_email(email, message):
    """sends an email when feedback form is filled successfully"""
    logger.info("Sent feedback email")
    from django.core.mail import EmailMessage

    email = EmailMessage(subject='PASTML web feedback', body=message, to=('anna.zhukova@pasteur.fr', ),
                         attachments=None, headers=None, cc=None, reply_to=(email,))
    return email.send(fail_silently=False)

@task(name="send_analysis_email")
def send_analysis_email(email, url, title):
    """sends an email when feedback form is filled successfully"""
    logger.info("Sent analysis is ready email")
    from django.core.mail import EmailMessage

    email = EmailMessage(subject='Your PASTML analysis is ready' if not title else title,
                         body='You PASTML ancestral state reconstruction is available at {}'.format(url),
                         to=(email, ), attachments=None, headers=None, cc=None)
    return email.send(fail_silently=False)


@task(name="apply_pastml")
def apply_pastml(id, data, tree, data_sep, id_index, columns, date_column, model, prediction_method, name_column,
                 html_compressed, html, email, title, url):
    from cytopast.pastml_analyser import pastml_pipeline
    pastml_pipeline(tree=tree, data=data, data_sep=data_sep, id_index=id_index, columns=columns,
                    date_column=date_column,
                    model=model, prediction_method=prediction_method, name_column=name_column,
                    html_compressed=html_compressed, html=html)
    if email:
        url = 'http://{}{}'.format(url, reverse('pastmlapp:detail', args=(id,)))
        send_analysis_email.delay(email, url, title)