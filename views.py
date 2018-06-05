from time import sleep

from django.core.files import File
from django.db.models import FilePathField
from django.http import HttpResponse
from django.shortcuts import render, get_object_or_404, redirect

from pastmlapp.forms import QuestionForm, FeedbackForm
from pastmlapp.models import Question

from .tasks import send_feedback_email_task, apply_pastml


def feedback(request):
    if request.method == 'POST':
        form = FeedbackForm(request.POST)
        if form.is_valid():
            email = form.cleaned_data['email']
            msg = form.cleaned_data['message']
            # The delay is used to asynchronously process the task
            send_feedback_email_task.delay(email, msg)
            return redirect('pastmlapp:index')
    else:
        form = FeedbackForm
    return render(request, 'pastmlapp/feedback.html', {'form': form})


def index(request):
    latest_question_list = Question.objects.order_by('-created_at')[:5]
    context = {
        'latest_question_list': latest_question_list
    }
    return render(request, 'pastmlapp/index.html', context)


def detail(request, question_id):
    question = get_object_or_404(Question, pk=question_id)
    data = 'Could not load request {}'.format(question_id)
    with open(question.html_compressed, 'r') as f:
        data = f.read()
    return render(request, 'pastmlapp/detail.html', {'text': data})


def results(request, question_id):
    response = "You're looking at the results of question %s."
    return HttpResponse(response % question_id)


def pastml(request):
    if request.method == 'POST':
        question = Question()
        form = QuestionForm(instance=question, data=request.POST, files=request.FILES)
        if form.is_valid():
            form.save()
            columns = form.cleaned_data['columns'].split(' ') if form.cleaned_data['columns'] else None
            # The delay is used to asynchronously process the task
            tree = question.tree.url
            html_compressed = '{}.compressed.html'.format(tree)
            task = apply_pastml.delay(question.data.url, tree,
                                      form.cleaned_data['data_sep'] if form.cleaned_data['data_sep'] else '\t',
                                      form.cleaned_data['id_index'],
                                      columns, form.cleaned_data['date_column'], form.cleaned_data['model'],
                                      form.cleaned_data['prediction_method'], form.cleaned_data['name_column'],
                                      html_compressed, '{}.html'.format(tree))
            while task.state not in ('SUCCESS', 'FAILURE'):
                sleep(0.1)
            if task.failed():
                # Insert error message and return to the input form
                return render(request, 'pastmlapp/pastml.html', {
                    'form': form, 'error': task.state
                })
            question.html_compressed = html_compressed
            question.save()
            return redirect('pastmlapp:detail', question_id=question.id)
    else:
        form = QuestionForm
    return render(request, 'pastmlapp/pastml.html', {
        'form': form
    })
