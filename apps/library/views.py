import markdown
from pathlib import Path
from django.conf import settings
from django.shortcuts import render

MD_FILE = settings.BASE_DIR / 'content' / 'articles' / 'plan.md'


def library_index(request):
    text = MD_FILE.read_text(encoding='utf-8')
    md = markdown.Markdown(extensions=['tables', 'toc', 'fenced_code'])
    content_html = md.convert(text)
    toc_html = md.toc
    return render(request, 'library/index.html', {
        'content': content_html,
        'toc': toc_html,
        'title': 'План по навигатору',
    })
