from django.shortcuts import get_object_or_404, render, redirect
from django.contrib.auth.decorators import login_required
from .forms import PlanosFinanceirosForm
from .models import PlanosFinanceiros
from django.urls import reverse

@login_required
def criar_PlanosFinanceiros(request):
    if request.method == "POST":
        form = PlanosFinanceirosForm(request.POST)
        if form.is_valid():
            # Antes de salvar, definir o status como True (1)
            plano = form.save(commit=False)
            plano.status = True  # Garantir que o status será True (1)
            plano.save()  # Salvar no banco
            return redirect('lista_planos')
    else:
        form = PlanosFinanceirosForm()
    
    return render(request, 'financeiro/cadastro_plano_financeiro.html', {'form': form})

@login_required
def listar_planos(request):
    planos = PlanosFinanceiros.objects.all()

    # Filtro por status
    status_filter = request.GET.get('status_filter')
    if status_filter == 'ativo':
        planos = planos.filter(status=True)
    elif status_filter == 'inativo':
        planos = planos.filter(status=False)

    # Ordenação
    order_by = request.GET.get('order_by', 'finance_name')  # Padrão: ordenar pelo nome
    order_direction = request.GET.get('order_direction', 'asc')

    if order_direction == 'desc':
        order_by = f'-{order_by}'

    planos = planos.order_by(order_by)

    return render(request, 'financeiro/plano_financeiro_list.html', {'planos': planos})

@login_required
def editar_plano(request, id):
    plano = get_object_or_404(PlanosFinanceiros, id=id)

    if request.method == "POST":
        form = PlanosFinanceirosForm(request.POST, instance=plano)
        if form.is_valid():
            form.save()
            return redirect(reverse("lista_planos"))
    else:
        form = PlanosFinanceirosForm(instance=plano)

    return render(request, "financeiro/editar_plano.html", {"form": form})

@login_required
def toggle_plano_status(request, id):
    plano = get_object_or_404(PlanosFinanceiros, id=id)

    # Alternar status
    plano.status = not plano.status
    plano.save()

    # Redirecionar para a lista de planos
    return redirect("lista_planos")


