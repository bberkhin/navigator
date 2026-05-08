"""
Функции, которые GigaChat может вызывать в ходе диалога.
Каждая функция состоит из двух частей:
  - схема (FUNCTION_*) — описание для модели в формате JSON Schema
  - реализация (*_impl) — Python-код, который выполняется когда модель решила вызвать функцию
"""
import json
import yaml
from pathlib import Path

from gigachat.models import Function, FunctionParameters

PROGRAMS_DIR = Path(__file__).resolve().parent.parent.parent / 'content' / 'programs'

# --- Вспомогательные константы ---

SUPPORT_FORM_LABELS = {
    'loan': 'Заём',
    'subsidy': 'Субсидия',
    'grant': 'Грант',
    'tax': 'Налоговая льгота',
}

STAGE_LABELS = {
    'rd': 'НИОКР',
    'pilot': 'Пилот',
    'production': 'Серийное производство',
    'scale': 'Масштабирование',
    'modernization': 'Модернизация',
}

RELEVANCE_LABELS = {
    'high': 'Высокая',
    'medium': 'Средняя',
    'low': 'Низкая',
}


# ---------------------------------------------------------------------------
# ФУНКЦИЯ 1: search_programs
# ---------------------------------------------------------------------------

# Схема — то, что видит GigaChat. Описывает параметры и их допустимые значения.
# Модель сама заполняет аргументы исходя из контекста диалога.
FUNCTION_SEARCH_PROGRAMS = Function(
    name='search_programs',
    description=(
        'Поиск подходящих программ господдержки по параметрам предприятия. '
        'Вызывай когда пользователь описывает свой проект, называет ОКВЭД, '
        'размер предприятия, стадию проекта или тип нужного финансирования.'
    ),
    parameters=FunctionParameters(
        type='object',
        properties={
            'support_form': {
                'type': 'string',
                'enum': ['loan', 'subsidy', 'grant', 'tax'],
                'description': 'Форма поддержки: loan=заём, subsidy=субсидия, grant=грант, tax=налоговая льгота',
            },
            'project_stage': {
                'type': 'string',
                'enum': ['rd', 'pilot', 'production', 'scale', 'modernization'],
                'description': 'Стадия проекта: rd=НИОКР, pilot=пилот, production=серийное производство, scale=масштабирование, modernization=модернизация',
            },
            'okveds': {
                'type': 'array',
                'items': {'type': 'string'},
                'description': 'Список ОКВЭД предприятия, например ["28.41", "25.73"]',
            },
            'relevance': {
                'type': 'string',
                'enum': ['high', 'medium', 'low'],
                'description': 'Минимальный уровень релевантности: high=только высокая, medium=высокая и средняя',
            },
            'max_amount_mln': {
                'type': 'number',
                'description': 'Минимально необходимая сумма финансирования в млн рублей',
            },
        },
        # Ни один параметр не обязателен — можно искать с любым набором фильтров
        required=[],
    ),
)


def search_programs_impl(
    support_form: str = None,
    project_stage: str = None,
    okveds: list = None,
    relevance: str = None,
    max_amount_mln: float = None,
) -> str:
    """
    Выполняет фильтрацию YAML-файлов программ по переданным параметрам.
    Возвращает строку — краткий список подходящих программ для GigaChat,
    чтобы модель могла сформулировать ответ пользователю.
    """
    results = []

    for path in sorted(PROGRAMS_DIR.glob('*.yaml')):
        with open(path, encoding='utf-8') as f:
            prog = yaml.safe_load(f)

        # Фильтр по форме поддержки
        if support_form and prog.get('support_form') != support_form:
            continue

        # Фильтр по стадии проекта
        if project_stage and prog.get('project_stage') != project_stage:
            continue

        # Фильтр по релевантности
        if relevance:
            order = ['high', 'medium', 'low']
            min_idx = order.index(relevance)
            prog_idx = order.index(prog.get('relevance', 'low'))
            if prog_idx > min_idx:
                continue

        # Фильтр по ОКВЭД — программа подходит если хотя бы один ОКВЭД совпадает
        if okveds:
            prog_okveds = prog.get('okveds', [])
            # Сравниваем первые 5 символов (группа ОКВЭД), чтобы 28.41 совпало с 28.4
            if not any(
                any(q[:5] in p or p[:5] in q for p in prog_okveds)
                for q in okveds
            ):
                continue

        # Фильтр по сумме — программа должна покрывать запрошенную сумму
        if max_amount_mln and prog.get('max_amount_mln'):
            if prog['max_amount_mln'] < max_amount_mln:
                continue

        results.append(prog)

    if not results:
        return 'По заданным параметрам программы не найдены. Попробуйте смягчить критерии поиска.'

    # Формируем текстовое описание для модели
    lines = [f'Найдено программ: {len(results)}\n']
    for p in results:
        amount = ''
        if p.get('max_amount_mln'):
            amount = f"до {p['max_amount_mln']} млн ₽"
            if p.get('min_amount_mln'):
                amount = f"от {p['min_amount_mln']} до {p['max_amount_mln']} млн ₽"
        rate = f", {p['rate_percent']}% годовых" if p.get('rate_percent') else ''
        term = f", {p['term']}" if p.get('term') else ''
        relevance_label = RELEVANCE_LABELS.get(p.get('relevance', ''), '')
        form_label = SUPPORT_FORM_LABELS.get(p.get('support_form', ''), '')

        lines.append(
            f"• {p['title']} ({p['admin_org']})\n"
            f"  Форма: {form_label}, {amount}{rate}{term}\n"
            f"  Релевантность: {relevance_label}\n"
            f"  Ссылка: /catalog/{p['slug']}/\n"
        )
        if p.get('center_notes'):
            lines.append(f"  Заметка эксперта: {p['center_notes']}\n")

    return '\n'.join(lines)


# ---------------------------------------------------------------------------
# ФУНКЦИЯ 2: get_program_detail
# ---------------------------------------------------------------------------

FUNCTION_GET_PROGRAM_DETAIL = Function(
    name='get_program_detail',
    description=(
        'Получить полную карточку конкретной программы господдержки по slug. '
        'Вызывай когда пользователь просит рассказать подробнее о конкретной программе '
        '(например, «расскажи подробнее про ФРП», «что за программа Сколково»).'
    ),
    parameters=FunctionParameters(
        type='object',
        properties={
            'slug': {
                'type': 'string',
                'description': 'Slug программы, например frp-stankostroyenie или skolkovo-tech',
            },
        },
        required=['slug'],
    ),
)


def get_program_detail_impl(slug: str) -> str:
    path = PROGRAMS_DIR / f'{slug}.yaml'
    if not path.exists():
        return f'Программа с slug «{slug}» не найдена в базе.'

    with open(path, encoding='utf-8') as f:
        p = yaml.safe_load(f)

    amount = ''
    if p.get('max_amount_mln'):
        amount = f"до {p['max_amount_mln']} млн ₽"
        if p.get('min_amount_mln'):
            amount = f"от {p['min_amount_mln']} до {p['max_amount_mln']} млн ₽"

    rate = f"{p['rate_percent']}% годовых" if p.get('rate_percent') else 'не указана'
    term = p.get('term', 'не указан')
    form_label = SUPPORT_FORM_LABELS.get(p.get('support_form', ''), p.get('support_form', ''))
    stage_label = STAGE_LABELS.get(p.get('project_stage', ''), p.get('project_stage', ''))
    relevance_label = RELEVANCE_LABELS.get(p.get('relevance', ''), '')
    okveds = ', '.join(p.get('okveds', [])) or 'не указаны'
    deadline = p.get('deadline_at') or 'без фиксированного дедлайна'
    verified = f"{p.get('verified_by', '—')} ({p.get('verified_at', '—')})"

    errors = ''
    if p.get('typical_errors'):
        errors = '\nТипичные ошибки заявителей:\n' + '\n'.join(f'  — {e}' for e in p['typical_errors'])

    notes = f"\nЗаметка эксперта Центра: {p['center_notes']}" if p.get('center_notes') else ''

    return (
        f"Программа: {p['title']}\n"
        f"Оператор: {p['admin_org']}\n"
        f"Форма поддержки: {form_label}\n"
        f"Сумма финансирования: {amount}\n"
        f"Ставка: {rate}\n"
        f"Срок: {term}\n"
        f"Стадия проекта: {stage_label}\n"
        f"Профиль предприятия: {p.get('enterprise_profile', 'не указан')}\n"
        f"ОКВЭД: {okveds}\n"
        f"Дедлайн: {deadline}\n"
        f"Релевантность: {relevance_label}\n"
        f"Официальный сайт: {p.get('official_url', '—')}\n"
        f"Верифицировано: {verified}"
        f"{errors}"
        f"{notes}"
    )


# ---------------------------------------------------------------------------
# ФУНКЦИЯ 3: check_eligibility
# ---------------------------------------------------------------------------

FUNCTION_CHECK_ELIGIBILITY = Function(
    name='check_eligibility',
    description=(
        'Проверить соответствие конкретного предприятия требованиям программы господдержки. '
        'Вызывай когда пользователь спрашивает «подхожу ли я под программу», '
        '«можем ли мы подать заявку» или называет конкретные параметры своего предприятия.'
    ),
    parameters=FunctionParameters(
        type='object',
        properties={
            'slug': {
                'type': 'string',
                'description': 'Slug программы для проверки',
            },
            'okveds': {
                'type': 'array',
                'items': {'type': 'string'},
                'description': 'ОКВЭД предприятия, например ["28.41", "25.73"]',
            },
            'enterprise_size': {
                'type': 'string',
                'enum': ['micro', 'small', 'medium', 'large'],
                'description': 'Размер: micro=микро (<15 чел), small=малое (<100 чел), medium=среднее (<250 чел), large=крупное',
            },
            'revenue_mln': {
                'type': 'number',
                'description': 'Годовая выручка предприятия в млн рублей',
            },
            'region': {
                'type': 'string',
                'description': 'Регион регистрации предприятия, например «Новосибирская область»',
            },
        },
        required=['slug'],
    ),
)


def check_eligibility_impl(
    slug: str,
    okveds: list = None,
    enterprise_size: str = None,
    revenue_mln: float = None,
    region: str = None,
) -> str:
    path = PROGRAMS_DIR / f'{slug}.yaml'
    if not path.exists():
        return f'Программа «{slug}» не найдена.'

    with open(path, encoding='utf-8') as f:
        p = yaml.safe_load(f)

    blockers = []
    warnings = []

    # Проверка ОКВЭД
    if okveds:
        prog_okveds = p.get('okveds', [])
        if prog_okveds:
            match = any(
                any(q[:5] in po or po[:5] in q for po in prog_okveds)
                for q in okveds
            )
            if not match:
                blockers.append(
                    f'ОКВЭД не совпадает. Программа требует: {", ".join(prog_okveds)}. '
                    f'У вас: {", ".join(okveds)}.'
                )
        else:
            warnings.append('ОКВЭД программы не задан — уточните у оператора.')

    # Проверка суммы vs размер предприятия (эвристика)
    if enterprise_size and p.get('min_amount_mln'):
        size_limits = {'micro': 30, 'small': 100, 'medium': 300, 'large': 9999}
        max_reasonable = size_limits.get(enterprise_size, 9999)
        if p['min_amount_mln'] > max_reasonable:
            warnings.append(
                f'Минимальная сумма программы ({p["min_amount_mln"]} млн ₽) '
                f'может быть высокой для предприятия вашего размера — уточните у эксперта.'
            )

    # Проверка выручки vs объём займа
    if revenue_mln and p.get('min_amount_mln'):
        if revenue_mln < p['min_amount_mln'] * 0.5:
            warnings.append(
                f'Выручка ({revenue_mln} млн ₽) значительно ниже минимального '
                f'объёма финансирования ({p["min_amount_mln"]} млн ₽) — '
                f'банк может отказать в обеспечении.'
            )

    # Проверка региона (программа НСО)
    if region and 'нсо' in p.get('slug', '').lower() or 'рфрп' in p.get('slug', '').lower():
        if region and 'новосибир' not in region.lower():
            blockers.append(
                f'Программа доступна только для предприятий Новосибирской области. '
                f'Ваш регион: {region}.'
            )

    # Итог
    if not blockers and not warnings:
        result = f'✅ По формальным критериям предприятие соответствует программе «{p["title"]}».'
        if p.get('center_notes'):
            result += f'\n\nЗаметка эксперта: {p["center_notes"]}'
        return result

    lines = [f'Результат проверки по программе «{p["title"]}»:\n']
    if blockers:
        lines.append('❌ Критические несоответствия (заявка будет отклонена):')
        lines += [f'  • {b}' for b in blockers]
    if warnings:
        lines.append('\n⚠ Предупреждения (требуют уточнения у эксперта):')
        lines += [f'  • {w}' for w in warnings]

    return '\n'.join(lines)


# ---------------------------------------------------------------------------
# ФУНКЦИЯ 4: book_consultation
# ---------------------------------------------------------------------------

FUNCTION_BOOK_CONSULTATION = Function(
    name='book_consultation',
    description=(
        'Создать заявку на консультацию со специалистом Центра НТР НГТУ. '
        'Вызывай когда пользователь явно хочет записаться на консультацию или '
        'задаёт вопрос, требующий персональной экспертизы. '
        'Перед вызовом убедись что у тебя есть номер телефона и описание вопроса.'
    ),
    parameters=FunctionParameters(
        type='object',
        properties={
            'phone': {
                'type': 'string',
                'description': 'Номер телефона для связи, например +7 913 123-45-67',
            },
            'question': {
                'type': 'string',
                'description': 'Краткое описание вопроса или задачи предприятия',
            },
            'program_slug': {
                'type': 'string',
                'description': 'Slug программы, если консультация по конкретной программе (необязательно)',
            },
        },
        required=['phone', 'question'],
    ),
)


def book_consultation_impl(phone: str, question: str, program_slug: str = '') -> str:
    # TODO: сохранять заявку в БД (модель ConsultRequest)
    return (
        f'✅ Заявка принята. Специалист Центра НТР свяжется с вами по номеру {phone} '
        f'в течение одного рабочего дня.'
    )


# ---------------------------------------------------------------------------
# Реестр всех функций — используется в views.py
# ---------------------------------------------------------------------------

# Схемы для передачи в GigaChat
ALL_FUNCTIONS = [
    FUNCTION_SEARCH_PROGRAMS,
    FUNCTION_GET_PROGRAM_DETAIL,
    FUNCTION_CHECK_ELIGIBILITY,
    FUNCTION_BOOK_CONSULTATION,
]

# Маппинг имя → реализация для выполнения вызовов модели
FUNCTION_REGISTRY = {
    'search_programs': search_programs_impl,
    'get_program_detail': get_program_detail_impl,
    'check_eligibility': check_eligibility_impl,
    'book_consultation': book_consultation_impl,
}
