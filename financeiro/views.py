# financeiro/views.py

from django.shortcuts import render

def financeiro(request):
    # Sua lógica aqui
    return render(request, 'financeiro/financeiro.html')
