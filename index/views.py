from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.shortcuts import render

def index(request):
    return render(request, 'index/index.html')

@login_required
def verificar_grupos(request):
    user = request.user
    grupos = list(user.groups.values_list('name', flat=True))  # Obtém os nomes dos grupos

    return JsonResponse({'usuario': user.username, 'grupos': grupos})
