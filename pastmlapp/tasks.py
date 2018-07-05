from celery.task import task
from celery.utils.log import get_task_logger

from pastmlapp.emails import send_feedback_email

logger = get_task_logger(__name__)


@task(name="send_feedback_email_task")
def send_feedback_email_task(email, message):
    """sends an email when feedback form is filled successfully"""
    logger.info("Sent feedback email")
    return send_feedback_email(email, message)


@task(name="apply_pastml")
def apply_pastml(data, tree, data_sep, id_index, columns, date_column, model, prediction_method, name_column,
                 html_compressed, html):
    from cytopast.pastml_analyser import pastml_pipeline
    pastml_pipeline(tree=tree, data=data, data_sep=data_sep, id_index=id_index, columns=columns,
                    date_column=date_column,
                    model=model, prediction_method=prediction_method, name_column=name_column,
                    html_compressed=html_compressed, html=html)
