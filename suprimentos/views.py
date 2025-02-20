from .models import Request, Product, RequestProduct, RequestFile, Quotation
from django.shortcuts import render, redirect, get_object_or_404
from django.views.generic.edit import CreateView, UpdateView
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.exceptions import ObjectDoesNotExist
from django.views.decorators.csrf import csrf_exempt
from .forms import RequestForm, ProductForm
from django.http import JsonResponse
from django.urls import reverse_lazy
from django.contrib import messages
from django.utils import timezone
from .models import PollRequest
import json
import os

class RequestCreateView(LoginRequiredMixin, CreateView):
    model = Request
    fields = ['request_text']
    template_name = 'suprimentos/forms/request_form.html'

    def form_valid(self, form):
        form.instance.created_by = self.request.user
        form.instance.status = 'criada'
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
    template_name = 'suprimentos/forms/products_form.html'
    success_url = reverse_lazy('all_requests')
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

    if request.GET.get('titulo') == "Todas as Compras":
        requests = Request.objects.filter(status="esperando cotação")
    else:
        requests = Request.objects.all()  # Retorna todas as requests, sem exceção

    return render(request, 'suprimentos/all_requests.html', {
        'all_requests': requests, 
        'titulo': "Todas as Compras",
        'user_groups': user_groups,
        })

@login_required
def admin_requests(request):
    user_groups = request.user.groups.values_list('name', flat=True)

    # Filter requests based on the 'titulo' parameter
    if request.GET.get('titulo') == "Todas as Compras":
        requests = Request.objects.filter(status="esperando cotação")
    else:
        requests = Request.objects.all()

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
        context = {"form_title": 'Solicitação de Compra'}
        return render(request, "suprimentos/forms/request_form.html", context)

    if request.method == "POST":
        return handle_request_creation(request)
    
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

def request_revisao(request, request_id):
    # Recupera a solicitação com o id fornecido
    request_obj = get_object_or_404(Request, id=request_id)
    
    # Altera o status para "revisao"
    request_obj.status = "revisao"
    request_obj.save()

    # Adiciona a mensagem de sucesso
    messages.success(request, 'Solicitação movida para revisão com sucesso.')

    # Redireciona para a página com todas as solicitações
    return redirect('all_requests')

def request_approve(request, request_id):
    # Obtém o objeto de solicitação com base no ID
    request_obj = get_object_or_404(Request, id=request_id)

    # Atualiza o status para 'Aprovada'
    request_obj.status = 'Aprovada'  # Substitua 'Aprovada' pelo status que sua aplicação usa
    request_obj.save()

    # Retorna uma resposta JSON de sucesso
    return JsonResponse({'status': 'success', 'message': 'Solicitação aprovada com sucesso!'})

def request_disapprove(request, request_id):
    # Obtém o objeto de solicitação com base no ID
    request_obj = get_object_or_404(Request, id=request_id)

    # Atualiza o status para 'Desaprovada'
    request_obj.status = 'Desaprovada'  # Substitua 'Desaprovada' pelo status que sua aplicação usa
    request_obj.save()

    # Retorna uma resposta JSON de sucesso
    return JsonResponse({'status': 'success', 'message': 'Solicitação desaprovada com sucesso!'})

def request_standby(request, request_id):
    # Obtém o objeto de solicitação com base no ID
    request_obj = get_object_or_404(Request, id=request_id)

    # Atualiza o status para 'Em Standby'
    request_obj.status = 'Standby'  # Substitua 'Standby' pelo status que sua aplicação usa
    request_obj.save()

    # Retorna uma resposta JSON de sucesso
    return JsonResponse({'status': 'success', 'message': 'Solicitação colocada em standby com sucesso!'})

def request_to_evaluate(request, request_id):
    # Recupera a solicitação com o ID fornecido
    request_obj = get_object_or_404(Request, id=request_id)

    # Altera o status para "A Avaliar" e limpa o campo comment
    request_obj.status = "a avaliar"
    request_obj.comment = None
    request_obj.save()

    # Adiciona uma mensagem de sucesso
    messages.success(request, 'Solicitação enviada para avaliação do gestor.')

    # Redireciona para a página das solicitações
    return redirect('all_requests')

def requests_view(request):
    all_requests = PollRequest.objects.all().prefetch_related('quotations')
    return render(request, 'your_template.html', {'all_requests': all_requests})

def request_list(request):
    all_requests = Request.objects.exclude(status="excluida")
    print("🔍 QuerySet:", all_requests)  # Mostra a QuerySet no terminal
    print("🔍 Total de registros:", all_requests.count())  # Conta quantos registros existem
    return render(request, 'sua_template.html', {'all_requests': all_requests})

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
            status="criada"
        )

        total_value = 0
        for key in product_fields:
            index = key.split("_")[1]
            product_id = request.POST.get(f"product_{index}")
            quantity = request.POST.get(f"quantity_{index}")

            if not product_id or not quantity:
                return JsonResponse({
                    "error": f"Produto {index}: campos obrigatórios não preenchidos"
                }, status=400)

            total_value, error_response = process_product_request(product_id, quantity, new_request, total_value)
            if error_response:
                return error_response

        new_request.total_value = total_value
        new_request.save()

        # Mensagem de sucesso
        messages.success(request, 'Solicitação criada com sucesso!')
        return redirect('solicitante')

    except Exception as e:
        return JsonResponse({
            "error": "Erro ao criar solicitação",
            "details": str(e)
        }, status=500)

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


@login_required
def request_list_view(request):
    all_requests = Request.objects.all()

    for req in all_requests:
        req.user = req.created_by_id

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

@login_required
def get_products(request):
    produtos = Product.objects.all().values("id", "product_name")
    return JsonResponse({"products": list(produtos)})

@login_required
def get_request_products(request, request_id):
    request_products = RequestProduct.objects.filter(request_id=request_id).select_related('product')
    products_data = [
        {
            "product_name": rp.product.product_name,
            "quantity": rp.quantity,
        }
        for rp in request_products
    ]
    return JsonResponse({"products": products_data})

@csrf_exempt
def add_comment(request, request_id):
    if request.method == 'POST':
        # Obter o comentário e a solicitação
        comment_data = json.loads(request.body)
        comment = comment_data.get('comment', '')

        try:
            # Atualizar o campo comment
            req = Request.objects.get(id=request_id)
            req.comment = comment
            req.status = 'revisão'  # Atualizar o status da solicitação para revisão
            req.save()

            # Retornar uma resposta de sucesso
            return JsonResponse({'message': 'Comentário adicionado com sucesso!'})

        except Request.DoesNotExist:
            return JsonResponse({'message': 'Solicitação não encontrada.'}, status=404)

@csrf_exempt
def add_files(request, request_id):
    if request.method == 'POST':
        try:
            req = Request.objects.get(id=request_id)
        except Request.DoesNotExist:
            return JsonResponse({'message': 'Solicitação não encontrada.'}, status=404)
        
        if 'files' in request.FILES:
            uploaded_files = request.FILES.getlist('files')
            for f in uploaded_files:
                # Certifique-se que o campo 'imagem' em RequestFile está configurado corretamente,
                # por exemplo, com null=True, blank=True se for opcional.
                RequestFile.objects.create(request=req, imagem=f)
            return JsonResponse({'message': 'Arquivos enviados com sucesso!'}, status=200)
        else:
            return JsonResponse({'message': 'Nenhum arquivo enviado.'}, status=400)
    else:
        return JsonResponse({'message': 'Método não permitido.'}, status=405)

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

def delete_quotation(request, quotation_id):
    if request.method == "POST":
        quotation = get_object_or_404(Quotation, id=quotation_id)
        quotation.delete()  # Exclui a cotação

        # Retorna um JSON com sucesso
        return JsonResponse({'success': True})
    return JsonResponse({'success': False}, status=400)


from .forms import QuotationForm

def add_quotation(request):
    if request.method == 'POST' and request.is_ajax():
        form = QuotationForm(request.POST, request.FILES)
        if form.is_valid():
            quotation = form.save(commit=False)
            quotation.request = request.POST.get('request_id')  # Recupera o ID da requisição
            quotation.save()

            return JsonResponse({
                'success': True,
                'message': 'Cotação enviada com sucesso!',
            })

        return JsonResponse({
            'success': False,
            'error': 'Erro ao enviar cotação. Verifique os campos.',
        })
    return JsonResponse({
        'success': False,
        'error': 'Método inválido.',
    })

    if request.method == 'POST':
        try:
            # Obter os arquivos do FormData
            files = request.FILES.getlist('files')  # Assumindo que o campo do formulário é 'files'
            for file in files:
                # Aqui você pode salvar o arquivo ou processá-lo como necessário
                # Exemplo de salvar o arquivo no modelo
                Quotation.objects.create(file=file)

            return JsonResponse({"success": True, "message": "Arquivo enviado com sucesso!"})
        except Exception as e:
            return JsonResponse({"success": False, "error": str(e)})
    return JsonResponse({"success": False, "error": "Método inválido"})