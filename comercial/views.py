from django.shortcuts import get_object_or_404, redirect, render
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from .forms import CentroCustoForm
from .models import CentroCusto
from django.urls import reverse

@login_required
def cadastro_centro_custo(request):
    if request.method == 'POST':
        form = CentroCustoForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('lista_centros_custo')
    else:
        form = CentroCustoForm()

    return render(request, 'comercial/cadastro_centro_custo.html', {'form': form})

@login_required
def lista_centros_custo(request):
    centros_custo = CentroCusto.objects.all()

    # Filtro de status
    status_filter = request.GET.get('status_filter')
    if status_filter:
        if status_filter == 'ativo':
            centros_custo = centros_custo.filter(status=True)
        elif status_filter == 'inativo':
            centros_custo = centros_custo.filter(status=False)

    # Ordenação
    order_by = request.GET.get('order_by', 'name')
    order_direction = request.GET.get('order_direction', 'asc')
    if order_direction == 'desc':
        order_by = f"-{order_by}"

    centros_custo = centros_custo.order_by(order_by)

    return render(request, 'comercial/centro_custo_list.html', {'centros_custo': centros_custo})

@login_required
def toggle_centro_custo_status(request, id):
    centro = get_object_or_404(CentroCusto, id=id)
    
    # Alternar status
    centro.status = not centro.status
    centro.save()

    # Redirecionar para a lista de centros de custo
    return redirect("lista_centros_custo")

@login_required
def editar_centro_custo(request, id):
    centro = get_object_or_404(CentroCusto, id=id)

    if request.method == "POST":
        form = CentroCustoForm(request.POST, instance=centro)
        if form.is_valid():
            form.save()
            return redirect(reverse("lista_centros_custo"))
    else:
        form = CentroCustoForm(instance=centro)

    return render(request, "comercial/centro_custo_edit.html", {"form": form})

def get_centros(request):
    centros = list(CentroCusto.objects.values("id", "name", "status "))
    return JsonResponse({"centros": centros})




