import os
from django.contrib.sites.models import Site
from django.shortcuts import render, get_object_or_404, redirect
from django.template.loader import render_to_string
from pastml.ml import F81, is_ml
from pastml.tree import read_forest

from pastmlapp.forms import TreeDataForm, AnalysisForm
from pastmlapp.models import TreeData, Analysis, Column
from .tasks import apply_pastml


def result(request, id):
    analysis = get_object_or_404(Analysis, pk=id)
    data = 'Could not load ancestral character reconstruction {}'.format(id)
    try:
        with open(analysis.html_compressed, 'r') as f:
            data = f.read()
    except:
        pass
    return render(request, 'pastmlapp/result.html', {'text': data})


def result_full(request, id):
    analysis = get_object_or_404(Analysis, pk=id)
    data = 'Could not load full tree visualisation for {} (probably your tree is too big).'.format(id)
    try:
        with open(analysis.html_compressed.replace('.compressed.html', '.full.html'), 'r') as f:
            data = f.read()
    except:
        pass
    return render(request, 'pastmlapp/result.html', {'text': data})


def detail(request, id):
    analysis = get_object_or_404(Analysis, pk=id)
    if os.path.exists(analysis.html_compressed):
        columns = [column.column for column in Column.objects.filter(
                analysis=analysis
            )]
        context = {'id': id, 'model': analysis.model if is_ml(analysis.prediction_method) else None,
                   'prediction_method': analysis.prediction_method,
                   'columns': ', '.join(columns)}
        # itol_id_file = os.path.join(os.path.dirname(analysis.html_compressed), 'pastml_{}_itol.txt'.format(id))
        # if os.path.exists(itol_id_file):
        #     with open(itol_id_file, 'r') as f:
        #         context['itol'] = f.readline().strip('\n')
        if os.path.exists(analysis.html_compressed.replace('.compressed.html', '.full.html')):
            context['other_html'] = 1

        if not os.path.exists(analysis.html_compressed.replace('{}.compressed.html'.format(analysis.id),
                                                               'pastml_{}.zip'.format(analysis.id))):
            context['rec_error'] = True

    else:
        context = {}
    return render(request, 'pastmlapp/layout.html', {
        'title': 'Results',
        'content': render_to_string('pastmlapp/detail.html', request=request, context=context)
    })


def detail_full(request, id):
    analysis = get_object_or_404(Analysis, pk=id)
    if os.path.exists(analysis.html_compressed):
        columns = [column.column for column in Column.objects.filter(
                analysis=analysis
            )]
        context = {'id': id, 'full': 1, 'model': analysis.model if is_ml(analysis.prediction_method) else None,
                   'prediction_method': analysis.prediction_method,
                   'columns': ', '.join(columns)}
        if not os.path.exists(analysis.html_compressed.replace('{}.compressed.html'.format(analysis.id),
                                                               'pastml_{}.zip'.format(analysis.id))):
            context['rec_error'] = True

    else:
        context = {}
    return render(request, 'pastmlapp/layout.html', {
        'title': 'Results',
        'content': render_to_string('pastmlapp/detail.html', request=request, context=context)
    })


def index(request):
    if request.method == 'POST':
        return redirect('pastmlapp:pastml')
    return render(request, 'pastmlapp/layout.html', {
        'title': 'PastML',
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
        'title': 'Run PastML',
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
            wd = os.path.dirname(tree)

            html_compressed = os.path.join(wd, '{}.compressed.html'.format(analysis.id))

            columns = [column.column for column in Column.objects.filter(
                analysis=analysis
            )]
            analysis.html_compressed = html_compressed
            analysis.save()

            work_dir = os.path.join(wd, 'pastml_{}'.format(analysis.id))

            html = os.path.join(wd, '{}.full.html'.format(analysis.id)) \
                if sum(len(_) for _ in read_forest(tree)) <= 1000 else None

            root_date = form.cleaned_data['root_date'] \
                if 'root_date' in form.cleaned_data and form.cleaned_data['root_date'] else None
            if root_date is not None:
                root_date = root_date.split(' ')
            apply_pastml.delay(id=analysis.id, data=tree_data.data.path, tree=tree,
                               data_sep=tree_data.data_sep if tree_data.data_sep and tree_data.data_sep != '<tab>' else '\t',
                               id_index=form.cleaned_data['id_column'], columns=columns,
                               root_date=root_date,
                               model=form.cleaned_data['model'] if 'model' in form.cleaned_data and form.cleaned_data['model'] else F81,
                               prediction_method=form.cleaned_data['prediction_method'],
                               name_column=columns[0], html_compressed=html_compressed, html=html, email=None,
                               title='', url=Site.objects.get_current(request=request).domain,
                               work_dir=work_dir, no_trimming=form.cleaned_data['no_trimming'],
                               timeline_type=form.cleaned_data['timeline_type'])

            return redirect('pastmlapp:detail', id=analysis.id)
    else:
        form = AnalysisForm(instance=analysis)

    return render(request, 'pastmlapp/layout.html', {
        'title': 'Run PastML',
        'content': render_to_string('pastmlapp/analysis.html', request=request, context={
            'form': form
        })
    })


def feedback(request):
    return render(request, 'pastmlapp/layout.html', {
        'title': 'Contact us',
        'content': render_to_string('pastmlapp/feedback.html')
    })


def helppage(request):
    return render(request, 'pastmlapp/layout.html', {
        'title': 'PastML How To',
        'content': render_to_string('pastmlapp/help.html')
    })


def cite(request):
    return render(request, 'pastmlapp/layout.html', {
        'title': 'Cite PastML',
        'content': render_to_string('pastmlapp/cite.html')
    })


def install(request):
    return render(request, 'pastmlapp/layout.html', {
        'title': 'Install PastML locally',
        'content': render_to_string('pastmlapp/install.html')
    })

