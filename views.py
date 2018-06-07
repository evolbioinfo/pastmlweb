from time import sleep

from django.core.files import File
from django.db.models import FilePathField
from django.http import HttpResponse
from django.shortcuts import render, get_object_or_404, redirect

from pastmlapp.forms import FeedbackForm, TreeDataForm, AnalysisForm
from pastmlapp.models import TreeData, Analysis, Column

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


def detail(request, id):
    analysis = get_object_or_404(Analysis, pk=id)
    data = 'Could not load PASTML analysis {}'.format(id)
    with open(analysis.html_compressed, 'r') as f:
        data = f.read()
    return render(request, 'pastmlapp/detail.html', {'text': data})


def results(request, id):
    response = "You're looking at the results of question %s."
    return HttpResponse(response % id)


def pastml(request):
    if request.method == 'POST':
        tree_data = TreeData()
        form = TreeDataForm(instance=tree_data, data=request.POST, files=request.FILES)
        if form.is_valid():
            form.save()
            return redirect('pastmlapp:analysis', id=tree_data.id)
    else:
        form = TreeDataForm
    return render(request, 'pastmlapp/pastml.html', {
        'form': form
    })


def analysis(request, id):
    tree_data = TreeData.objects.get(pk=id)
    analysis = Analysis(tree_data=tree_data)

    if request.method == 'POST':
        form = AnalysisForm(instance=analysis, data=request.POST)
        if form.is_valid():
            form.save()

            tree = tree_data.tree.url
            html_compressed = '{}.compressed.html'.format(tree)

            columns = [column.column for column in Column.objects.filter(
                analysis=analysis
            )]
            task = apply_pastml.delay(tree_data.data.url, tree,
                                      tree_data.data_sep if tree_data.data_sep else '\t',
                                      tree_data.id_index,
                                      columns, form.cleaned_data['date_column'], form.cleaned_data['model'],
                                      form.cleaned_data['prediction_method'], columns[0],
                                      html_compressed, '{}.html'.format(tree))
            while task.state not in ('SUCCESS', 'FAILURE'):
                sleep(0.1)
            if task.failed():
                # Insert error message and return to the input form
                return render(request, 'pastmlapp/analysis.html', {
                    'form': form, 'error': task.info
                })
            analysis.html_compressed = html_compressed
            analysis.save()

            return redirect('pastmlapp:detail', id=analysis.id)
    else:
        form = AnalysisForm(instance=analysis)
    return render(request, 'pastmlapp/analysis.html', {
        'form': form
    })
