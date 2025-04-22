from .models import Request, Product, RequestProduct, RequestFile, Quotation, CentroCusto, PlanoFinanceiro, Armazem, Funcionario
from .forms import RequestForm, ProductForm, CentroCustoForm, PlanoFinanceiroForm, ArmazemForm, FuncionarioForm
from django.shortcuts import render, redirect, get_object_or_404
from django.views.generic.edit import CreateView, UpdateView
from django.db.models import Exists, OuterRef, Prefetch, Q
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.decorators import login_required
from django.views.decorators.csrf import csrf_exempt
from django.http import JsonResponse
from django.urls import reverse_lazy
from django.contrib import messages
from django.utils import timezone

def index(request):
    return redirect('lista_estoque')

class RequestCreateView(LoginRequiredMixin, CreateView):
    model = Request
    fields = ['request_text']
    template_name = 'suprimentos/forms/request_form.html'

    def form_valid(self, form):
        form.instance.created_by = self.request.user
        form.instance.status = 'Criada'
        response = super().form_valid(form)

        num_products = int(self.request.POST.get('num_products', 0))
        for i in range(1, num_products + 1):
            product_id = self.request.POST.get(f'product_{i}')
            quantity = self.request.POST.get(f'quantity_{i}')

            if product_id and quantity:
                try:
                    product = Product.objects.get(id=product_id)
                    quantity = int(quantity)

                    RequestProduct.objects.create(
                        request=form.instance,
                        product=product,
                        quantity=quantity
                    )
                except Product.DoesNotExist:
                    messages.error(self.request, f"Produto com ID {product_id} não encontrado.")
                    return redirect('request_create')

        messages.success(self.request, 'Solicitação criada com sucesso!')
        return response

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['products'] = Product.objects.all()
        context['form_title'] = 'Criando uma Solicitação de Produto'
        return context

    def get_success_url(self):
        return reverse_lazy('solicitante')

class RequestUpdateView(LoginRequiredMixin, UpdateView):
    model = Request
    form_class = RequestForm
    template_name = 'suprimentos/forms/request_form.html'
    success_url = reverse_lazy('solicitante')

    def form_valid(self, form):
        form.instance.status = self.get_object().status  # Mantém o status original
        messages.success(self.request, 'Solicitação atualizada com sucesso.')
        return super().form_valid(form)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['form_title'] = 'Editando Solicitação'
        return context

    def dispatch(self, request, *args, **kwargs):
        request_obj = self.get_object()
        if request_obj.status == 'esperando cotação':
            messages.error(request, 'Solicitação não pode ser editada após estar esperando cotação.')
            return redirect('solicitante')
        return super().dispatch(request, *args, **kwargs)

class ProductCreateView(LoginRequiredMixin, CreateView):
    model = Product
    form_class = ProductForm
    template_name = 'suprimentos/product/products_form.html'
    success_url = reverse_lazy('product_list')
    success_message = 'Produto adicionado com sucesso'

    def form_valid(self, form):
        form.instance.created_by = self.request.user  # Associa o usuário atual ao produto
        response = super().form_valid(form)
        messages.success(self.request, self.success_message)  # Mensagem de sucesso
        return response

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['form_title'] = 'Criando um produto'
        return context

@login_required
def all_requests(request):
    user_groups = request.user.groups.values_list('name', flat=True)

    # Obtendo todas as requests com status específico
    requests = Request.objects.filter(
        Q(status="esperando cotação") | 
        Q(status="Standby") | 
        Q(status="Desaprovada") | 
        Q(status="Aprovada") | 
        Q(status="Aguardando avaliação")
    ).annotate(
        has_quotation=Exists(Quotation.objects.filter(request_id=OuterRef('id')))
    ).prefetch_related(
        Prefetch('quotation_set', queryset=Quotation.objects.all(), to_attr='quotations')
    )

    return render(request, 'suprimentos/all_requests.html', {
        'all_requests': requests, 
        'titulo': "Todas as Solicitações",
        'user_groups': user_groups,
    })

@login_required
def admin_requests(request):
    user_groups = request.user.groups.values_list('name', flat=True)

    # Verificar se o usuário tem o grupo 'admin' para acessar as cotações
    is_admin = 'admin' in user_groups

    # Filtrando as solicitações com base no parâmetro 'titulo'
    if request.GET.get('titulo') == "Todas as Compras":
        requests = Request.objects.filter(status="esperando cotação")
    else:
        requests = Request.objects.all()

    # Caso o usuário seja um admin, incluir as cotações
    if is_admin:
        requests = requests.annotate(
            has_quotation=Exists(Quotation.objects.filter(request_id=OuterRef('id')))
        ).prefetch_related(
            Prefetch('quotation_set', queryset=Quotation.objects.all(), to_attr='quotations')
        )

    return render(request, 'suprimentos/admin_requests.html', {
        'all_requests': requests, 
        'titulo': "Admin", 
        'user_groups': user_groups,
    })

@login_required
def solicitante(request):
    # Filtra as solicitações feitas pelo usuário logado
    requests = Request.objects.filter(created_by=request.user)
    
    # Contexto para o template
    context = {
        'all_requests': requests, 
        'titulo': 'Minhas Solicitações'
    }
    
    # Renderiza a página com as solicitações filtradas
    return render(request, 'suprimentos/requests.html', context)

@login_required
def request_create(request):
    if request.method == "GET":
        # Buscar centros de custo para preencher o select no formulário
        centros = CentroCusto.objects.all()
        context = {
            "form_title": 'Solicitação de Compra',
            "centros": centros  # Enviando os centros para o template
        }
        return render(request, "suprimentos/forms/request_form.html", context)

    if request.method == "POST":
        # Captura do texto da solicitação
        request_text = request.POST.get('request_text')
        centro_id = request.POST.get('cost_center')  # ID do centro de custo selecionado
        company = request.POST.get('company')  # Captura o valor do campo 'company'

        # Verifica se o centro de custo existe
        try:
            centro_custo = CentroCusto.objects.get(id=centro_id)
        except CentroCusto.DoesNotExist:
            return JsonResponse({"error": "Centro de custo inválido"}, status=400)

        # Criação da nova solicitação
        new_request = Request.objects.create(
            request_text=request_text,
            created_by=request.user,
            pub_date=timezone.now(),
            status='Criada',
            cost_center=centro_custo,  # Salva o centro de custo
            company=company  # Salva o valor do campo 'company'
        )

        # Inserção dos produtos associados à solicitação
        for i in range(1, len(request.POST) // 2 + 1):
            product_id = request.POST.get(f'product_{i}')
            quantity = request.POST.get(f'quantity_{i}')

            if product_id and quantity:
                try:
                    product = Product.objects.get(id=product_id)
                    RequestProduct.objects.create(
                        request=new_request,
                        product=product,
                        quantity=quantity
                    )
                except Product.DoesNotExist:
                    continue  # Caso o produto não exista, simplesmente ignora

        return redirect('solicitante')  # Redireciona para a página de solicitações

    return JsonResponse({"error": "Método inválido"}, status=405)

@login_required
def update_request_status(request):
    if request.method != "POST":
        return JsonResponse({"error": "Método inválido"}, status=405)

    # Recuperando os dados da requisição
    request_id = request.POST.get('request_id')
    new_status = request.POST.get('new_status')

    if not request_id or not new_status:
        return JsonResponse({"error": "ID da solicitação e novo status são obrigatórios"}, status=400)

    try:
        request_obj = get_object_or_404(Request, id=request_id)
        request_obj.status = new_status
        request_obj.save()

        return JsonResponse({"message": f"Status da solicitação {request_id} atualizado para {new_status}"})
    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)

@login_required
def request_publish(request, request_id):
    # Recupera a solicitação com o id fornecido
    request_obj = get_object_or_404(Request, id=request_id)
    
    # Altera o status para "Esperando Cotação"
    request_obj.status = "esperando cotação"
    request_obj.save()

    # Adiciona a mensagem de sucesso
    messages.success(request, 'Solicitação enviada para cotação')
    
    # Redireciona para a página com todas as solicitações
    return redirect('solicitante')

@login_required
def request_delete(request, request_id):
    # Recupera a solicitação com o id fornecido
    request_obj = get_object_or_404(Request, id=request_id)
    
    # Altera o status para "Excluída"
    request_obj.status = "excluida"
    request_obj.save()

    # Adiciona a mensagem de sucesso
    messages.success(request, 'Solicitação excluída com sucesso.')

    # Redireciona para a página com todas as solicitações
    return redirect('solicitante')

@login_required
def request_approve(request, request_id):
    # Obtém o objeto de solicitação com base no ID
    request_obj = get_object_or_404(Request, id=request_id)

    # Atualiza o status para 'Aprovada'
    request_obj.status = 'Aprovada'  # Substitua 'Aprovada' pelo status que sua aplicação usa
    request_obj.save()

    # Redireciona para a página
    return redirect('admin_requests')

@login_required
def request_disapprove(request, request_id):
    # Obtém o objeto de solicitação com base no ID
    request_obj = get_object_or_404(Request, id=request_id)

    # Atualiza o status para 'Desaprovada'
    request_obj.status = 'Desaprovada'  # Substitua 'Desaprovada' pelo status que sua aplicação usa
    request_obj.save()

    # Redireciona para a página
    return redirect('admin_requests')

@login_required
def request_standby(request, request_id):
    # Obtém o objeto de solicitação com base no ID
    request_obj = get_object_or_404(Request, id=request_id)

    # Atualiza o status para 'Em Standby'
    request_obj.status = 'Standby'  # Substitua 'Standby' pelo status que sua aplicação usa
    request_obj.save()

    # Redireciona para a página 
    return redirect('admin_requests')

@login_required
def request_to_evaluate(request, request_id):
    # Recupera a solicitação com o ID fornecido
    request_obj = get_object_or_404(Request, id=request_id)

    request_obj.status = "Aguardando avaliação"
    request_obj.comment = None
    request_obj.save()

    # Adiciona uma mensagem de sucesso
    messages.success(request, 'Solicitação enviada para avaliação do gestor.')

    # Redireciona para a página das solicitações
    return redirect('all_requests')

@login_required
def request_list(request):
    all_requests = Request.objects.exclude(status="excluida")
    print("🔍 QuerySet:", all_requests)
    print("🔍 Total de registros:", all_requests.count())
    return render(request, 'sua_template.html', {'all_requests': all_requests})

@login_required
def request_revision(request, request_id):
    if request.method == 'POST':
        # Obtém a instância do objeto Request com o ID fornecido
        request_obj = get_object_or_404(Request, id=request_id)

        # Pega o comentário enviado no formulário (do modal)
        comentario = request.POST.get('comment', '')  # 'comment' é o nome do campo do modal

        # Atualiza o status para "revisão"
        request_obj.status = 'Revisão Solicitada'

        # Adiciona o comentário, se houver
        if comentario:
            request_obj.comment = comentario  # Substitui pelo campo 'comment'

        # Salva as mudanças no banco de dados
        request_obj.save()

        # Adiciona a mensagem de sucesso
        messages.success(request, 'Solicitação enviada para revisão com sucesso!')

        # Retorna uma resposta vazia (para manter a lógica do modal)
        return JsonResponse({'status': 'success'})

    else:
        return JsonResponse({'status': 'error', 'message': 'Método não permitido.'}, status=405)

@login_required
def handle_request_creation(request):
    request_text = request.POST.get("request_text")
    if not request_text:
        return JsonResponse({"error": "O texto da solicitação é obrigatório!"}, status=400)

    product_fields = [key for key in request.POST.keys() if key.startswith("product_")]
    if not product_fields:
        return JsonResponse({"error": "Adicione pelo menos um produto"}, status=400)

    try:
        user = request.user
        new_request = Request.objects.create(
            request_text=request_text,
            created_by=user,
            pub_date=timezone.now(),
            status="Criada"
        )

        for key in product_fields:
            index = key.split("_")[1]
            product_id = request.POST.get(f"product_{index}")
            quantity = request.POST.get(f"quantity_{index}")

            if not product_id or not quantity:
                return JsonResponse({
                    "error": f"Produto {index}: campos obrigatórios não preenchidos"
                }, status=400)

        new_request.save()

        # Mensagem de sucesso
        messages.success(request, 'Solicitação criada com sucesso!')
        return redirect('solicitante')

    except Exception as e:
        return JsonResponse({
            "error": "Erro ao criar solicitação",
            "details": str(e)
        }, status=500)

@login_required
def request_list_view(request):
    all_requests = Request.objects.all()

    for req in all_requests:
        req.user = req.created_by

    return render(request, 'suprimentos/all_requests.html', {'all_requests': all_requests})

@login_required
def upload_request_files(request):
    if request.method != "POST":
        return JsonResponse({"error": "Método inválido"}, status=405)

    request_id = request.POST.get('request_id')
    
    if not request_id:
        return JsonResponse({"error": "ID da solicitação é obrigatório"}, status=400)

    try:
        request_obj = Request.objects.get(id=request_id)
        
        # Processando os arquivos enviados
        for file in request.FILES.getlist('files'):
            RequestFile.objects.create(
                request=request_obj,
                file=file
            )
        
        # Atualizando o status para 'aguardando aprovação'
        request_obj.status = 'aguardando aprovação'
        request_obj.save()
        
        return JsonResponse({
            "message": "Arquivos enviados e status atualizado com sucesso",
            "new_status": request_obj.status,
            "file_count": len(request.FILES.getlist('files'))
        })
    except Request.DoesNotExist:
        return JsonResponse({"error": "Solicitação não encontrada"}, status=404)
    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)

@csrf_exempt
def upload_request_file(request, request_id):
    if request.method == 'POST' and request.FILES.get('file'):
        file = request.FILES['file']
        # Salvar o arquivo no servidor
        with open(f'media/uploads/{file.name}', 'wb+') as destination:
            for chunk in file.chunks():
                destination.write(chunk)

        return JsonResponse({"success": True})

    return JsonResponse({"success": False, "error": "Nenhum arquivo enviado"}, status=400)

# cotações

@login_required
def upload_quotation(request):
    if request.method == 'POST' and request.FILES.get('quotation_file'):
        quotation_file = request.FILES['quotation_file']
        request_id = request.POST.get('request_id')
        
        # Criação de uma nova instância do modelo SuprimentosQuotation
        new_quotation = Quotation(
            request_id=request_id,
            file=quotation_file,
            created_by=request.user,
        )
        
        # Salvar a instância no banco de dados
        try:
            new_quotation.save()
            # Retornar a resposta de sucesso
            return JsonResponse({'message': 'Cotação enviada com sucesso!', 'file_url': new_quotation.file.url})
        except Exception as e:
            return JsonResponse({'error': f'Erro ao salvar a cotação: {str(e)}'}, status=500)

    else:
        return JsonResponse({'error': 'Falha ao enviar a cotação'}, status=400)
    
@login_required
def delete_quotation(request, quotation_id):
    try:
        # Encontra a cotação pelo ID
        quotation = Quotation.objects.get(id=quotation_id)
        
        # Verifica se o usuário tem permissão para deletar (opcional)
        if request.user != quotation.created_by and not request.user.is_superuser:
            return JsonResponse({'error': 'Você não tem permissão para excluir esta cotação.'}, status=403)
        
        # Exclui a cotação
        quotation.delete()
        
        return JsonResponse({'message': 'Cotação excluída com sucesso.'}, status=200)
    
    except Quotation.DoesNotExist:
        return JsonResponse({'error': 'Cotação não encontrada.'}, status=404)
    
    except Exception as e:
        return JsonResponse({'error': f'Erro ao excluir a cotação: {str(e)}'}, status=500)

@login_required
def get_quotations(request, request_id):
    try:
        # Forçando o request_id para um inteiro
        request_id = int(request_id)
        print(f"ID recebido na view: {request_id}")  # Confirmação do valor recebido

        # Filtra as cotações pelo request_id
        quotations = Quotation.objects.filter(request_id=request_id).values('file')
        quotation_list = list(quotations)

        # Verifica se encontrou alguma cotação
        if not quotation_list:
            print("Nenhuma cotação encontrada para esse request_id")

        return JsonResponse({'quotations': quotation_list})

    except ValueError:
        print(f"Erro ao converter request_id para inteiro: {request_id}")
        return JsonResponse({'error': 'Request ID inválido'}, status=400)

# produtos

@login_required
def get_products(request):
    products = Product.objects.all().values('id', 'product_name', 'unidade_medida', 'status')
    product_list = list(products)
    return JsonResponse({'products': product_list})

@login_required
def product_list(request):
    # Recupera as unidades de medida distintas
    unidades = Product.objects.values_list('unidade_medida', flat=True).distinct()

    # Filtra e ordena os produtos com base nos parâmetros da URL
    filter_by = request.GET.get('filter_by', '')
    status_filter = request.GET.get('status_filter', '')  # Filtro de status
    order_by = request.GET.get('order_by', '')
    order_direction = request.GET.get('order_direction', 'asc')

    products = Product.objects.all()

    # Aplicar filtro por unidade de medida, se fornecido
    if filter_by:
        products = products.filter(unidade_medida=filter_by)

    # Aplicar filtro por status, se fornecido
    if status_filter:
        if status_filter == 'ativo':
            products = products.filter(status=True)
        elif status_filter == 'inativo':
            products = products.filter(status=False)

    # Aplicar ordenação
    if order_by:
        if order_direction == 'desc':
            products = products.order_by(f'-{order_by}')
        else:
            products = products.order_by(order_by)

    return render(request, 'suprimentos/product/product_list.html', {
        'products': products,
        'unidades': unidades,  # Passa as unidades de medida para o template
        'status_filter': status_filter,  # Passa o filtro de status para o template
    })

@login_required
def edit_product(request, product_id):
    product = get_object_or_404(Product, id=product_id)
    
    if request.method == 'POST':
        form = ProductForm(request.POST, instance=product)
        if form.is_valid():
            form.save()
            return redirect('product_list')  # Redireciona de volta para a lista de produtos
    else:
        form = ProductForm(instance=product)
    
    return render(request, 'suprimentos/product/edit_product.html', {'form': form, 'product': product})

@login_required
def toggle_product_status(request, product_id):
    # Obter o produto com o id fornecido
    product = get_object_or_404(Product, id=product_id)
    
    # Alternar o valor do status
    product.status = not product.status
    product.save()

    # Redirecionar para a página de listagem de produtos ou onde preferir
    return redirect('product_list')  # Substitua 'product_list' pela URL que você deseja redirecionar

@login_required
def get_request_products(request, request_id):
    # Filtra os RequestProduct associados ao request_id, e faz o join com o Product
    request_products = RequestProduct.objects.filter(request_id=request_id).select_related('product')

    # Cria uma lista de dicionários com os dados dos produtos
    products_data = [
        {
            "product_name": rp.product.product_name,  # Acessa o nome do produto através da relação
            "quantity": rp.quantity,  # Quantidade do produto
        }
        for rp in request_products
    ]

    # Retorna a resposta JSON com os dados dos produtos
    return JsonResponse({"products": products_data})

@login_required
def process_product_request(product_id, quantity, request):
    try:
        product = Product.objects.get(id=product_id)
        quantity = int(quantity)
        if quantity <= 0:
            return JsonResponse({
                "error": f"Quantidade do produto {product_id} deve ser maior que 0"
            }, status=400)

        RequestProduct.objects.create(
            request=request,
            product=product,
            quantity=quantity
        )
        return None
    except Product.DoesNotExist:
        return JsonResponse({
            "error": f"Produto com ID {product_id} não encontrado"
        }, status=400)
    except ValueError:
        return JsonResponse({
            "error": f"Quantidade inválida para produto {product_id}"
        }, status=400)

# Centros de Custo

@login_required
def cadastrar_centro_custo(request):
    if request.method == "POST":
        form = CentroCustoForm(request.POST)
        if form.is_valid():
            centro_custo = form.save(commit=False)
            centro_custo.usuario_registrante = request.user  # Atribui o usuário logado
            centro_custo.save()
            return redirect('listar_centros_custo')  # Redireciona após salvar
    else:
        form = CentroCustoForm()
    return render(request, 'suprimentos/centrocusto/centrocusto_form.html', {'form': form})

@login_required
def listar_centros_custo(request):
    centros = CentroCusto.objects.all()

    # Filtro por status
    status_filter = request.GET.get('status_filter')
    if status_filter == 'ativo':
        centros = centros.filter(status=True)
    elif status_filter == 'inativo':
        centros = centros.filter(status=False)

    # Ordenação
    order_by = request.GET.get('order_by')
    order_direction = request.GET.get('order_direction', 'asc')

    if order_by:
        if order_direction == 'asc':
            centros = centros.order_by(order_by)
        else:
            centros = centros.order_by('-' + order_by)

    context = {
        'centros': centros,
        'status_filter': status_filter,
        'order_by': order_by,
        'order_direction': order_direction,
    }
    return render(request, 'suprimentos/centrocusto/centrocusto_list.html', context)

@login_required
def editar_centro_custo(request, centrocusto_id):
    centrocusto = get_object_or_404(CentroCusto, id=centrocusto_id)
    if request.method == 'POST':
        form = CentroCustoForm(request.POST, instance=centrocusto)
        if form.is_valid():
            form.save()
            return redirect('listar_centros_custo')  # Redireciona para a lista de centros de custo
    else:
        form = CentroCustoForm(instance=centrocusto)  # Inicializa o formulário com a instância
    return render(request, 'suprimentos/centrocusto/editar_centrocusto_form.html', {'form': form, 'centrocusto': centrocusto})

@login_required
def toggle_centro_custo_status(request, centro_id):
    centro_custo = get_object_or_404(CentroCusto, id=centro_id)
    
    if centro_custo.status:  # Se o centro de custo está ativo
        centro_custo.status = False  # Desativa o centro de custo
        centro_custo.data_inativacao = timezone.now()  # Define a data de inativação com o horário atual
    else:  # Se o centro de custo já está inativo
        centro_custo.status = True  # Ativa o centro de custo
        centro_custo.data_inativacao = None  # Limpa a data de inativação
    
    centro_custo.save()
    return redirect('listar_centros_custo')  # Redireciona para a lista de centros de custo

# Plano Financeiro

@login_required
def cadastrar_plano_financeiro(request):
    if request.method == "POST":
        form = PlanoFinanceiroForm(request.POST)
        if form.is_valid():
            plano_financeiro = form.save(commit=False)
            plano_financeiro.usuario_registrante = request.user  # Atribui o usuário logado
            plano_financeiro.save()
            return redirect('listar_planos_financeiros')  # Redireciona após salvar
    else:
        form = PlanoFinanceiroForm()
    return render(request, 'suprimentos/planofinanceiro/planofinanceiro_form.html', {'form': form})

@login_required
def listar_planos_financeiros(request):
    planos = PlanoFinanceiro.objects.all()

    # Filtro por status
    status_filter = request.GET.get('status_filter')
    if status_filter == 'ativo':
        planos = planos.filter(status=True)
    elif status_filter == 'inativo':
        planos = planos.filter(status=False)

    # Ordenação
    order_by = request.GET.get('order_by')
    order_direction = request.GET.get('order_direction', 'asc')

    if order_by:
        if order_direction == 'asc':
            planos = planos.order_by(order_by)
        else:
            planos = planos.order_by('-' + order_by)

    context = {
        'planos': planos,
        'status_filter': status_filter,
        'order_by': order_by,
        'order_direction': order_direction,
    }
    return render(request, 'suprimentos/planofinanceiro/planofinanceiro_list.html', context)

@login_required
def editar_plano_financeiro(request, plano_id):
    plano = get_object_or_404(PlanoFinanceiro, id=plano_id)
    
    if request.method == "POST":
        # Salva apenas o nome do plano financeiro
        plano.name = request.POST.get('name')
        plano.save()
        return redirect('listar_planos_financeiros')  # Redireciona após a edição
    
    context = {
        'form_title': 'Editar Plano Financeiro',
        'plano': plano,
    }
    return render(request, 'suprimentos/planofinanceiro/editar_planofinanceiro_form.html', context)

@login_required
def toggle_plano_financeiro_status(request, plano_id):
    plano_financeiro = PlanoFinanceiro.objects.get(id=plano_id)
    plano_financeiro.status = not plano_financeiro.status
    plano_financeiro.save()
    return redirect('listar_planos_financeiros')

# Armazens

@login_required
def cadastrar_armazem(request):
    if request.method == "POST":
        form = ArmazemForm(request.POST)
        if form.is_valid():
            armazem = form.save(commit=False)
            armazem.usuario_registrante = request.user  # Atribui o usuário logado
            armazem.save()
            return redirect('listar_armazens')  # Redireciona após salvar
    else:
        form = ArmazemForm()
    return render(request, 'suprimentos/armazem/armazem_form.html', {'form': form})

@login_required
def listar_armazens(request):
    armazens = Armazem.objects.all()

    # Filtro por status
    status_filter = request.GET.get('status_filter')
    if status_filter == 'ativo':
        armazens = armazens.filter(status=True)
    elif status_filter == 'inativo':
        armazens = armazens.filter(status=False)

    # Ordenação
    order_by = request.GET.get('order_by')
    order_direction = request.GET.get('order_direction', 'asc')

    if order_by:
        if order_direction == 'asc':
            armazens = armazens.order_by(order_by)
        else:
            armazens = armazens.order_by('-' + order_by)

    context = {
        'armazens': armazens,
        'status_filter': status_filter,
        'order_by': order_by,
        'order_direction': order_direction,
    }
    return render(request, 'suprimentos/armazem/armazem_list.html', context)

@login_required
def editar_armazem(request, armazem_id):
    # Obtém o armazém pelo ID ou retorna 404 se não encontrado
    armazem = get_object_or_404(Armazem, id=armazem_id)
    
    if request.method == "POST":
        # Cria o formulário com os dados enviados e associa ao armazém
        form = ArmazemForm(request.POST, instance=armazem)
        if form.is_valid():
            form.save()  # Salva as alterações no banco de dados
            messages.success(request, 'Armazém atualizado com sucesso!')
            return redirect('listar_armazens')  # Redireciona para a lista de armazéns
        else:
            messages.error(request, 'Erro ao atualizar o armazém. Verifique os dados.')
    else:
        # Cria o formulário com os dados do armazém existente
        form = ArmazemForm(instance=armazem)
    
    # Renderiza o template com o formulário
    context = {
        'form': form,
        'armazem': armazem,
        'form_title': 'Editar Armazém',
    }
    return render(request, 'suprimentos/armazem/editar_armazem_form.html', context)

@login_required
def toggle_armazem_status(request, armazem_id):
    armazem = Armazem.objects.get(id=armazem_id)
    armazem.status = not armazem.status
    armazem.save()
    return redirect('listar_armazens')

# Funcionarios

@login_required
def listar_funcionarios(request):
    funcionarios = Funcionario.objects.all()

    # Filtro por status
    status_filter = request.GET.get('status_filter')
    if status_filter == 'ativo':
        funcionarios = funcionarios.filter(status=True)
    elif status_filter == 'inativo':
        funcionarios = funcionarios.filter(status=False)

    # Ordenação
    order_by = request.GET.get('order_by')
    order_direction = request.GET.get('order_direction', 'asc')

    if order_by:
        if order_direction == 'asc':
            funcionarios = funcionarios.order_by(order_by)
        else:
            funcionarios = funcionarios.order_by('-' + order_by)

    context = {
        'funcionarios': funcionarios,
        'status_filter': status_filter,
        'order_by': order_by,
        'order_direction': order_direction,
    }
    return render(request, 'suprimentos/funcionario/funcionario_list.html', context)

@login_required
def cadastrar_funcionario(request):
    if request.method == 'POST':
        form = FuncionarioForm(request.POST)
        if form.is_valid():
            funcionario = form.save(commit=False)
            funcionario.usuario_registrante = request.user  # Define o usuário logado como registrante
            funcionario.save()
            messages.success(request, 'Funcionário cadastrado com sucesso!')
            return redirect('listar_funcionarios')  # Redireciona para a lista de funcionários
        else:
            messages.error(request, 'Erro ao cadastrar funcionário. Verifique os dados.')
    else:
        form = FuncionarioForm()
    return render(request, 'suprimentos/funcionario/cadastrar_funcionario.html', {'form': form})

@login_required
def editar_funcionario(request, funcionario_id):
    funcionario = get_object_or_404(Funcionario, id=funcionario_id)
    
    if request.method == "POST":
        form = FuncionarioForm(request.POST, instance=funcionario)
        if form.is_valid():
            form.save()
            messages.success(request, 'Funcionário atualizado com sucesso!')
            return redirect('listar_funcionarios')  # Redireciona para a lista de funcionários
        else:
            messages.error(request, 'Erro ao atualizar funcionário. Verifique os dados.')
    else:
        form = FuncionarioForm(instance=funcionario)
    
    context = {
        'form': form,
        'funcionario': funcionario,
        'form_title': 'Editar Funcionário',
    }
    return render(request, 'suprimentos/funcionario/editar_funcionario.html', context)

@login_required
def toggle_funcionario_status(request, funcionario_id):
    funcionario = get_object_or_404(Funcionario, id=funcionario_id)
    
    if funcionario.status:  # Se o funcionário está ativo
        funcionario.status = False  # Desativa o funcionário
        funcionario.data_inativacao = timezone.now()  # Define a data de inativação com o horário atual
    else:  # Se o funcionário já está inativo
        funcionario.status = True  # Ativa o funcionário
        funcionario.data_inativacao = None  # Limpa a data de inativação
    
    funcionario.save()
    messages.success(request, f'Status do funcionário "{funcionario.nome_completo}" atualizado com sucesso!')
    return redirect('listar_funcionarios')  # Redireciona para a lista de funcionários

