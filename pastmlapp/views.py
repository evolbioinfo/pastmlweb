import os
import datetime
from django.contrib.sites.models import Site
from django.shortcuts import render, get_object_or_404, redirect
from django.template.loader import render_to_string

from pastmlapp.forms import FeedbackForm, TreeDataForm, AnalysisForm
from pastmlapp.models import TreeData, Analysis, Column
from .tasks import apply_pastml


def result(request, id):
    analysis = get_object_or_404(Analysis, pk=id)
    data = 'Could not load PASTML analysis {}'.format(id)
    with open(analysis.html_compressed, 'r') as f:
        data = f.read()
    return render(request, 'pastmlapp/result.html', {'text': data})


def detail(request, id):
    analysis = get_object_or_404(Analysis, pk=id)
    if os.path.exists(analysis.html_compressed):
        context = {'id': id, 'model': analysis.model, 'prediction_method': analysis.prediction_method,
                   'iframe_param': datetime.datetime.now().timestamp()}
    else:
        context = {}
    return render(request, 'pastmlapp/layout.html', {
        'title': 'Results',
        'meta': """
            <meta http-Equiv="Cache-Control" Content="no-cache" />
            <meta http-Equiv="Pragma" Content="no-cache" />
            <meta http-Equiv="Expires" Content="0" />
        """,
        'content': render_to_string('pastmlapp/detail.html', request=request, context=context)
    })


def index(request):
    if request.method == 'POST':
        return redirect('pastmlapp:pastml')
    return render(request, 'pastmlapp/layout.html', {
        'title': 'PASTML',
        'meta': '',
        'content': render_to_string('pastmlapp/index.html')
    })


def pastml(request):
    if request.method == 'POST':
        tree_data = TreeData()
        form = TreeDataForm(instance=tree_data, data=request.POST, files=request.FILES)
        if form.is_valid():
            form.save()
            return redirect('pastmlapp:analysis', id=tree_data.id)
    else:
        form = TreeDataForm

    return render(request, 'pastmlapp/layout.html', {
        'title': 'Run PASTML',
        'meta': '',
        'content': render_to_string('pastmlapp/pastml.html', request=request, context={
            'form': form
        })
    })


def analysis(request, id):
    tree_data = TreeData.objects.get(pk=id)
    analysis = Analysis(tree_data=tree_data)

    if request.method == 'POST':
        form = AnalysisForm(instance=analysis, data=request.POST)
        if form.is_valid():
            form.save()

            tree = tree_data.tree.path
            html_compressed = '{}.compressed.html'.format(tree)

            columns = [column.column for column in Column.objects.filter(
                analysis=analysis
            )]
            analysis.html_compressed = html_compressed
            analysis.save()

            work_dir = os.path.join(os.path.dirname(tree), 'pastml_{}'.format(analysis.id))

            apply_pastml.delay(id=analysis.id, data=tree_data.data.path, tree=tree,
                               data_sep=tree_data.data_sep if tree_data.data_sep and tree_data.data_sep != '<tab>' else '\t',
                               id_index=form.cleaned_data['id_column'], columns=columns,
                               date_column=form.cleaned_data['date_column'] if 'date_column' in form.cleaned_data else None,
                               model=form.cleaned_data['model'], prediction_method=form.cleaned_data['prediction_method'],
                               name_column=columns[0], html_compressed=html_compressed, email=form.cleaned_data['email'],
                               title=form.cleaned_data['title'], url=Site.objects.get_current(request=request).domain,
                               work_dir=work_dir)

            return redirect('pastmlapp:detail', id=analysis.id)
    else:
        form = AnalysisForm(instance=analysis)

    return render(request, 'pastmlapp/layout.html', {
        'title': 'Run PASTML',
        'meta': '',
        'content': render_to_string('pastmlapp/analysis.html', request=request, context={
            'form': form
        })
    })


def feedback(request):
    if request.method == 'POST':
        form = FeedbackForm(data=request.POST)
        if form.is_valid():
            form.send_email()
            return redirect('pastmlapp:index')
    else:
        form = FeedbackForm

    return render(request, 'pastmlapp/layout.html', {
        'title': 'Contact us',
        'meta': '',
        'content': render_to_string('pastmlapp/feedback.html', request=request, context={
            'form': form
        })
    })
