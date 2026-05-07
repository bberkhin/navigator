from django.shortcuts import render

def consult_index(request):
    submitted = request.method == 'POST'
    return render(request, 'consult/index.html', {'submitted': submitted})
