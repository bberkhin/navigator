import yaml
from pathlib import Path
from django.shortcuts import render
from django.http import Http404

PROGRAMS_DIR = Path(__file__).resolve().parent.parent.parent / 'content' / 'programs'

SUPPORT_FORM_LABELS = {
    'loan': 'Заём',
    'subsidy': 'Субсидия',
    'grant': 'Грант',
    'tax': 'Налоговая льгота',
}

RELEVANCE_LABELS = {
    'high': ('Высокая', 'relevance--high'),
    'medium': ('Средняя', 'relevance--medium'),
    'low': ('Низкая', 'relevance--low'),
}

STAGE_LABELS = {
    'rd': 'НИОКР',
    'pilot': 'Пилот',
    'production': 'Серийное производство',
    'scale': 'Масштабирование',
    'modernization': 'Модернизация',
}


def _load_programs():
    programs = []
    for path in sorted(PROGRAMS_DIR.glob('*.yaml')):
        with open(path, encoding='utf-8') as f:
            data = yaml.safe_load(f)
        data['support_form_label'] = SUPPORT_FORM_LABELS.get(data.get('support_form'), data.get('support_form', ''))
        rel = data.get('relevance', 'medium')
        data['relevance_label'], data['relevance_css'] = RELEVANCE_LABELS.get(rel, (rel, ''))
        data['stage_label'] = STAGE_LABELS.get(data.get('project_stage'), data.get('project_stage', ''))
        programs.append(data)
    return programs


def catalog_list(request):
    programs = _load_programs()
    support_filter = request.GET.get('type', '')
    stage_filter = request.GET.get('stage', '')
    if support_filter:
        programs = [p for p in programs if p.get('support_form') == support_filter]
    if stage_filter:
        programs = [p for p in programs if p.get('project_stage') == stage_filter]
    return render(request, 'catalog/list.html', {
        'programs': programs,
        'support_filter': support_filter,
        'stage_filter': stage_filter,
        'support_form_labels': SUPPORT_FORM_LABELS,
        'stage_labels': STAGE_LABELS,
    })


def catalog_detail(request, slug):
    for path in PROGRAMS_DIR.glob('*.yaml'):
        with open(path, encoding='utf-8') as f:
            data = yaml.safe_load(f)
        if data.get('slug') == slug:
            data['support_form_label'] = SUPPORT_FORM_LABELS.get(data.get('support_form'), data.get('support_form', ''))
            rel = data.get('relevance', 'medium')
            data['relevance_label'], data['relevance_css'] = RELEVANCE_LABELS.get(rel, (rel, ''))
            data['stage_label'] = STAGE_LABELS.get(data.get('project_stage'), data.get('project_stage', ''))
            return render(request, 'catalog/detail.html', {'program': data})
    raise Http404
