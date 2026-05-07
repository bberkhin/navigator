from django.shortcuts import render


def navigator_index(request):
    return render(request, 'navigator/index.html')


def navigator_ai(request):
    return render(request, 'navigator/ai.html')


def navigator_anketa(request):
    return render(request, 'navigator/anketa.html')
