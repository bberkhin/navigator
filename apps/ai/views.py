# JsonResponse — возвращает HTTP-ответ в формате JSON (для API-эндпоинтов)
# require_POST — декоратор-ограничитель: принимает только POST-запросы, иначе 405 Method Not Allowed
# settings — объект настроек Django, через него читаем GIGACHAT_AUTH_KEY и GIGACHAT_SCOPE из .env
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.conf import settings
import json

# GigaChat — основной клиент SDK, открывает сессию с API Сбера
# Chat — объект запроса: содержит список сообщений для отправки модели
# Messages — одно сообщение в диалоге (роль + текст)
# MessagesRole — перечисление ролей: SYSTEM, USER, ASSISTANT, FUNCTION
from gigachat import GigaChat
from gigachat.models import Chat, Messages, MessagesRole

from .functions import ALL_FUNCTIONS, FUNCTION_REGISTRY

# Системный промпт — скрытая инструкция модели, которую пользователь не видит.
# Отправляется первым сообщением с ролью SYSTEM при каждом запросе.
# Задаёт личность, область знаний и обязательный дисклеймер в конце ответов.
SYSTEM_PROMPT = """Ты — AI-консультант Центра НТР станкостроения НГТУ (Новосибирск).
Помогаешь предприятиям станкоинструментальной отрасли Новосибирской области найти подходящие меры господдержки.
Отвечай только на вопросы о мерах господдержки, программах финансирования, требованиях к заявителям, ОКВЭД, ФРП, РФРП НСО, Минпромторг, РНФ, Сколково.
На вопросы не по теме вежливо объясни, что специализируешься только на господдержке для промышленных предприятий.
В конце каждого ответа добавляй: "⚠ Данная информация носит консультационный характер. Для точной экспертизы запишитесь на консультацию к специалисту Центра."
Отвечай по-русски, кратко и конкретно."""


@require_POST  # только POST-запросы; браузерный GET сюда не пройдёт
def chat(request):
    # --- Парсинг входящего JSON ---
    # Фронтенд отправляет: {"message": "текст вопроса"}
    # Если тело не является валидным JSON — возвращаем 400 Bad Request
    try:
        body = json.loads(request.body)
        user_message = body.get('message', '').strip()
    except (json.JSONDecodeError, KeyError):
        return JsonResponse({'error': 'Неверный формат запроса'}, status=400)

    if not user_message:
        return JsonResponse({'error': 'Пустое сообщение'}, status=400)

    # --- История диалога в Django-сессии ---
    # Сессия привязана к браузеру пользователя через cookie sessionid.
    # При первом обращении история пуста — get() вернёт [].
    # Каждое сообщение хранится как {'role': 'user'/'assistant', 'content': '...'}
    history = request.session.get('ai_history', [])

    # Добавляем новый вопрос пользователя в историю до отправки в GigaChat,
    # чтобы он попал в контекст текущего запроса
    history.append({'role': 'user', 'content': user_message})

    # --- Формирование списка сообщений для GigaChat ---
    # GigaChat принимает весь диалог целиком при каждом запросе —
    # модель не хранит контекст на своей стороне между вызовами.
    # Структура: [SYSTEM, USER, ASSISTANT, USER, ASSISTANT, ..., USER (текущий)]
    messages = [Messages(role=MessagesRole.SYSTEM, content=SYSTEM_PROMPT)]

    # Берём только последние 10 сообщений истории — ограничение контекстного окна.
    # Слишком длинная история увеличивает стоимость запроса и время ответа.
    for msg in history[-10:]:
        role = MessagesRole.USER if msg['role'] == 'user' else MessagesRole.ASSISTANT
        messages.append(Messages(role=role, content=msg['content']))

    # --- Запрос к GigaChat API с поддержкой function calling ---
    try:
        with GigaChat(
            credentials=settings.GIGACHAT_AUTH_KEY,  # OAuth-ключ из .env
            scope=settings.GIGACHAT_SCOPE,            # GIGACHAT_API_PERS — личный доступ
            verify_ssl_certs=False,                   # отключаем проверку сертификата Сбера
        ) as giga:

            # Цикл нужен потому что модель может вызвать функцию,
            # получить результат и затем снова вызвать функцию (цепочка вызовов).
            # Ограничиваем 5 итерациями — защита от бесконечного цикла.
            for _ in range(5):
                resp = giga.chat(Chat(
                    messages=messages,
                    functions=ALL_FUNCTIONS,  # передаём схемы всех доступных функций
                    function_call='auto',     # модель сама решает: вызвать функцию или ответить текстом
                ))
                choice = resp.choices[0]
                msg = choice.message

                if msg.function_call:
                    # Модель решила вызвать функцию — выполняем её на нашей стороне

                    fn_name = msg.function_call.name
                    fn_args = msg.function_call.arguments
                    print(f'[AI] Function call: {fn_name}({fn_args})')

                    # Добавляем в контекст сообщение ассистента с вызовом функции
                    messages.append(Messages(
                        role=MessagesRole.ASSISTANT,
                        content='',
                        function_call=msg.function_call,
                    ))

                    # Находим реализацию функции в реестре и вызываем её
                    fn_impl = FUNCTION_REGISTRY.get(fn_name)
                    if fn_impl:
                        fn_result = fn_impl(**fn_args)
                    else:
                        fn_result = f'Функция {fn_name} не найдена'

                    print(f'[AI] Function result:\n{fn_result}')

                    # Добавляем результат в контекст с ролью FUNCTION —
                    # это сигнал для модели: «вот данные, теперь ответь пользователю»
                    messages.append(Messages(
                        role=MessagesRole.FUNCTION,
                        name=fn_name,
                        content=json.dumps({'result': fn_result}, ensure_ascii=False),
                    ))
                    # Продолжаем цикл — следующая итерация получит финальный ответ

                else:
                    # Модель вернула текстовый ответ — цикл завершён
                    answer = msg.content
                    break
            else:
                answer = 'Не удалось получить ответ после нескольких попыток.'

        # Сохраняем только финальный ответ в историю (без промежуточных вызовов функций)
        history.append({'role': 'assistant', 'content': answer})
        request.session['ai_history'] = history[-20:]
        request.session.modified = True

        return JsonResponse({'answer': answer})

    except Exception as e:
        return JsonResponse({'error': f'Ошибка GigaChat: {e}'}, status=500)


def chat_clear(request):
    # Удаляем историю из сессии. pop() с default=None не бросает KeyError
    # если ключа нет — безопасно вызывать повторно
    request.session.pop('ai_history', None)
    return JsonResponse({'ok': True})
