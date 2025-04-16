from .models import Estoque, EntradaEstoque, SaidaEstoque, TransferenciaEstoque
from suprimentos.models import Product, Armazem, Funcionario
from django.contrib.auth.decorators import login_required
from .forms import EntradaEstoqueForm, SaidaEstoqueForm
from django.http import HttpResponse, JsonResponse
from django.shortcuts import render, redirect
from reportlab.lib.utils import ImageReader
from reportlab.lib.pagesizes import A4
from django.utils.timezone import now
from django.db.models import Q, Sum
from reportlab.pdfgen import canvas
from django.contrib import messages
from django.db import transaction
from datetime import datetime
from io import BytesIO
import pandas as pd

@login_required
def entrada_estoque(request):
    if request.method == 'POST':
        form = EntradaEstoqueForm(request.POST)
        if form.is_valid():
            local = form.cleaned_data['local']
            usuario = request.user  # Captura o usuário autenticado

            for i in range(len(request.POST.getlist('produto'))):
                produto_id = request.POST.getlist('produto')[i]
                produto = Product.objects.get(id=produto_id)
                quantidade = int(request.POST.getlist('quantidade')[i])

                # Atualiza ou cria o estoque
                estoque, created = Estoque.objects.get_or_create(
                    product=produto, local=local, defaults={'quantidade': 0}
                )
                estoque.quantidade += quantidade
                estoque.save()

                # Registra a entrada no log
                EntradaEstoque.objects.create(
                    product=produto,
                    local=local,
                    quantidade=quantidade,
                    usuario_registrante=usuario  # Salva quem registrou
                )

            return redirect('lista_estoque')

    else:
        form = EntradaEstoqueForm()

    # Buscar apenas os nomes dos armazéns
    locais_entrada = Armazem.objects.values_list('name', flat=True)

    return render(request, 'estoque/forms/entrada_estoque.html', {
        'form': form,
        'locais_entrada': locais_entrada  # Passa os locais de entrada para o template
    })

@login_required
def saida_estoque(request):
    if request.method == 'POST':
        try:
            local = request.POST.get('local')
            responsavel_id = request.POST.get('responsavel')
            usuario = request.user

            # Captura todos os produtos e quantidades dinamicamente
            produtos = []
            quantidades = []
            for key, value in request.POST.items():
                if key.startswith('produto-'):
                    produtos.append(value)
                if key.startswith('quantidade-'):
                    quantidades.append(value)

            # Verifica se os campos obrigatórios estão preenchidos
            if not local:
                messages.error(request, "O campo 'Local' é obrigatório.")
                return redirect('saida_estoque')
            if not produtos or not quantidades:
                messages.error(request, "Os campos 'Produto' e 'Quantidade' são obrigatórios.")
                return redirect('saida_estoque')

            with transaction.atomic():
                for i in range(len(produtos)):
                    produto_id = produtos[i]
                    try:
                        quantidade = int(quantidades[i])
                        if quantidade <= 0:
                            raise ValueError("A quantidade deve ser maior que zero.")
                    except ValueError as ve:
                        messages.error(request, f"Quantidade inválida para o produto {produto_id}: {ve}")
                        return redirect('saida_estoque')

                    try:
                        produto = Product.objects.get(id=produto_id)
                    except Product.DoesNotExist:
                        messages.error(request, f"Produto com ID {produto_id} não encontrado.")
                        return redirect('saida_estoque')

                    try:
                        estoque = Estoque.objects.get(product=produto, local=local)
                    except Estoque.DoesNotExist:
                        messages.error(request, f"Estoque para o produto {produto.product_name} no local {local} não encontrado.")
                        return redirect('saida_estoque')

                    if estoque.quantidade < quantidade:
                        messages.error(request, f"Estoque insuficiente para {produto.product_name}.")
                        return redirect('saida_estoque')

                    # Atualiza o estoque
                    estoque.quantidade -= quantidade
                    estoque.save()

                    # Registra a saída no log
                    SaidaEstoque.objects.create(
                        product=produto,
                        local=local,
                        quantidade=quantidade,
                        usuario_registrante=usuario,
                        responsavel_id=responsavel_id
                    )

            messages.success(request, "Saída registrada com sucesso.")
            return redirect('lista_estoque')

        except Exception as e:
            messages.error(request, f"Ocorreu um erro inesperado: {e}")
            return redirect('saida_estoque')

    # Obter os locais de saída disponíveis
    locais_estoque = Estoque.objects.values_list('local', flat=True).distinct()
    funcionarios = Funcionario.objects.filter(status=True)

    return render(request, 'estoque/forms/saida_estoque.html', {
        'locais_estoque': locais_estoque,
        'funcionarios': funcionarios,
    })

@login_required
def get_produtos_por_local(request, local):
    produtos = Estoque.objects.filter(local=local, quantidade__gt=0)
    produtos_info = []

    for estoque in produtos:
        produtos_info.append({
            'id': estoque.product_id,
            'quantidade': estoque.quantidade,
            'product': {
                'product_name': estoque.product.product_name
            }
        })

    return JsonResponse({'produtos': produtos_info})

@login_required
def lista_estoque(request):
    estoque = Estoque.objects.select_related('product')

    search = request.GET.get('search', '')
    local = request.GET.get('local', '')
    unidade = request.GET.get('unidade', '')
    tipo = request.GET.get('tipo', '')
    quantidade = request.GET.get('quantidade', '')  # Get the quantidade filter

    # Apply filters based on the received parameters
    if search:
        estoque = estoque.filter(
            Q(product__product_name__icontains=search) |
            Q(local__icontains=search)
        )
    if local:
        estoque = estoque.filter(local=local)
    if unidade:
        estoque = estoque.filter(product__unidade_medida=unidade)
    if tipo:
        estoque = estoque.filter(product__tipo=tipo)
    if quantidade:
        estoque = estoque.filter(quantidade=quantidade)  # Filter by quantity

    # Obtaining unique values for available locations and units
    locais_disponiveis = Estoque.objects.values_list('local', flat=True).distinct()
    unidades_disponiveis = Estoque.objects.values_list('product__unidade_medida', flat=True).distinct()

    context = {
        'estoque': estoque,
        'locais_disponiveis': locais_disponiveis,
        'unidades_disponiveis': unidades_disponiveis,
    }

    return render(request, 'estoque/lista_estoque.html', context)

@login_required
def exportar_estoque_excel(request):
    estoque = Estoque.objects.select_related('product')

    search = request.GET.get('search', '')
    local = request.GET.get('local', '')
    unidade = request.GET.get('unidade', '')
    tipo = request.GET.get('tipo', '')

    # Aplicando os filtros conforme os parâmetros recebidos
    if search:
        estoque = estoque.filter(
            Q(product__product_name__icontains=search) |
            Q(local__icontains=search)
        )
    if local:
        estoque = estoque.filter(local=local)
    if unidade:
        estoque = estoque.filter(product__unidade_medida=unidade)
    if tipo:
        estoque = estoque.filter(product__tipo=tipo)

    # Criando um DataFrame com os dados filtrados
    data = []
    for item in estoque:
        data.append([
            item.product.product_name,
            item.quantidade,  # Quantidade agora vem logo após o nome do produto
            item.product.unidade_medida,
            "Uso único" if item.product.tipo == "unico" else "Reutilizável",
            "Ativo" if item.product.status else "Inativo",
            item.local
        ])

    df = pd.DataFrame(data, columns=[
        "Nome do Produto", "Quantidade", "Unidade de Medida", "Tipo", "Status", "Local"
    ])

    # Criando um arquivo Excel na memória
    response = HttpResponse(content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
    response['Content-Disposition'] = 'attachment; filename=estoque.xlsx'

    with pd.ExcelWriter(response, engine='openpyxl') as writer:
        df.to_excel(writer, index=False, sheet_name="Estoque")

    return response

@login_required
def exportar_estoque_pdf(request):
    estoque = Estoque.objects.select_related('product')

    search = request.GET.get('search', '')
    local = request.GET.get('local', '')
    unidade = request.GET.get('unidade', '')
    tipo = request.GET.get('tipo', '')

    # Aplicando filtros conforme os parâmetros recebidos
    if search:
        estoque = estoque.filter(
            Q(product__product_name__icontains=search) |
            Q(local__icontains=search)
        )
    if local:
        estoque = estoque.filter(local=local)
    if unidade:
        estoque = estoque.filter(product__unidade_medida=unidade)
    if tipo:
        estoque = estoque.filter(product__tipo=tipo)

    # Criando o arquivo PDF em memória
    buffer = BytesIO()
    p = canvas.Canvas(buffer, pagesize=A4)
    width, height = A4

    # 📌 Definições de layout
    margem_esquerda = 30
    margem_topo = height - 50
    espacamento_linha = 15
    espacamento_titulo = 30
    rodape_altura = 40

    # 📌 Obtendo a data atual formatada
    data_atual = datetime.now().strftime("%d/%m/%Y")

    # 🖼️ Adicionando papel timbrado (imagem do logotipo)
    try:
        logo_path = "media/icons/LOGO_ACT_LARANJA.png"  # Altere para o caminho correto
        logo = ImageReader(logo_path)
        p.drawImage(logo, margem_esquerda, height - 100, width=100, height=50, mask='auto')
    except:
        print("⚠️ Logo não encontrado. Verifique o caminho!")

    # 📝 Adicionando cabeçalho estilizado
    p.setFont("Helvetica-Bold", 14)
    p.drawString(margem_esquerda + 120, height - 80, "ACT ENGENHARIA - Relatório de Estoque")

    # 📆 Adicionando data do relatório
    p.setFont("Helvetica", 10)
    p.drawString(margem_esquerda + 120, height - 95, f"Data de geração: {data_atual}")

    # 📌 Criando cabeçalho da tabela
    p.setFont("Helvetica-Bold", 9)
    y_position = margem_topo - 120  # Ajustado para não sobrepor o cabeçalho
    colunas = [
        ("Produto", margem_esquerda),
        ("Qtd", 180),
        ("Unidade", 230),
        ("Tipo", 300),
        ("Status", 370),
        ("Local", 450),
    ]
    for titulo, x in colunas:
        p.drawString(x, y_position, titulo)

    # 📝 Adicionando os dados do estoque
    p.setFont("Helvetica", 9)
    y_position -= espacamento_linha
    for item in estoque:
        p.drawString(margem_esquerda, y_position, item.product.product_name[:20])  # Nome limitado
        p.drawString(180, y_position, str(item.quantidade))
        p.drawString(230, y_position, item.product.unidade_medida)
        p.drawString(300, y_position, "Uso único" if item.product.tipo == "unico" else "Reutilizável")
        p.drawString(370, y_position, "Ativo" if item.product.status else "Inativo")
        p.drawString(450, y_position, item.local[:20])  # Local limitado

        y_position -= espacamento_linha
        if y_position < rodape_altura + 20:  # Criar nova página se atingir limite
            p.showPage()

            # Reaplica o cabeçalho na nova página
            try:
                p.drawImage(logo, margem_esquerda, height - 100, width=100, height=50, mask='auto')
            except:
                pass
            p.setFont("Helvetica-Bold", 14)
            p.drawString(margem_esquerda + 120, height - 80, "Empresa XYZ - Relatório de Estoque")
            p.setFont("Helvetica", 10)
            p.drawString(margem_esquerda + 120, height - 95, f"Data de geração: {data_atual}")

            # Reaplica cabeçalho da tabela
            p.setFont("Helvetica-Bold", 9)
            y_position = margem_topo - 120
            for titulo, x in colunas:
                p.drawString(x, y_position, titulo)
            y_position -= espacamento_linha
            p.setFont("Helvetica", 9)

    # ✏️ Adicionando rodapé fixo
    p.setFont("Helvetica", 8)
    p.drawString(margem_esquerda, 30, "Empresa XYZ - Endereço: Rua Exemplo, 123 - Tel: (11) 9999-9999 - Email: contato@empresa.com")

    # 🏁 Finalizando o PDF
    p.showPage()
    p.save()

    # 📄 Enviando o arquivo PDF como resposta HTTP
    buffer.seek(0)
    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename=estoque_{data_atual.replace("/", "-")}.pdf'
    response.write(buffer.getvalue())
    return response

@login_required
def transferencia_produto(usuario, produto_id, local_saida, local_entrada, quantidade):
    # Verificar se o produto existe
    try:
        produto = Product.objects.get(id=produto_id)
    except Product.DoesNotExist:
        raise Exception("Produto não encontrado.")
    
    # Verificar se o produto existe no local de saída
    try:
        estoque_saida = Estoque.objects.get(produto=produto, local=local_saida)
    except Estoque.DoesNotExist:
        raise Exception(f"Produto não encontrado no local de saída: {local_saida}.")
    
    # Verificar se o produto existe no local de entrada
    try:
        estoque_entrada = Estoque.objects.get(produto=produto, local=local_entrada)
    except Estoque.DoesNotExist:
        raise Exception(f"Produto não encontrado no local de entrada: {local_entrada}.")
    
    # Verificar se a quantidade no local de saída é suficiente
    if estoque_saida.quantidade < quantidade:
        raise Exception(f"Quantidade insuficiente no local de saída: {local_saida}.")
    
    # Iniciar uma transação para garantir que tudo seja feito de forma atômica
    with transaction.atomic():
        # Subtrair a quantidade do local de saída
        estoque_saida.quantidade -= quantidade
        estoque_saida.save()
        
        # Adicionar a quantidade ao local de entrada
        estoque_entrada.quantidade += quantidade
        estoque_entrada.save()
        
        # Criar um log de transferência
        log_transferencia = TransferenciaEstoque(
            produto=produto,
            local_saida=local_saida,
            local_entrada=local_entrada,
            quantidade=quantidade,
            usuario=usuario,
            data_transferencia=now()
        )
        log_transferencia.save()
    
    return f"Transferência de {quantidade} unidades de {produto.nome} realizada com sucesso!"

@login_required
def transferencia_view(request):
    if request.method == 'POST':
        local_saida = request.POST.get('local_saida')
        local_entrada = request.POST.get('local_entrada')
        responsavel_id = request.POST.get('responsavel')
        observacao = request.POST.get('observacao')  # Captura o campo de observação
        usuario = request.user
        produtos = request.POST.getlist('produto[]')
        quantidades = request.POST.getlist('quantidade[]')

        try:
            with transaction.atomic():
                for i in range(len(produtos)):
                    produto_id = produtos[i]
                    quantidade = int(quantidades[i])
                    produto = Product.objects.get(id=produto_id)
                    estoque_saida = Estoque.objects.get(product=produto, local=local_saida)

                    if estoque_saida.quantidade < quantidade:
                        messages.error(request, f"Estoque insuficiente para {produto.product_name}.")
                        return redirect('transferencia_estoque')

                    estoque_saida.quantidade -= quantidade
                    estoque_saida.save()

                    estoque_entrada, created = Estoque.objects.get_or_create(
                        product=produto,
                        local=local_entrada,
                        defaults={'quantidade': 0}
                    )
                    estoque_entrada.quantidade += quantidade
                    estoque_entrada.save()

                    TransferenciaEstoque.objects.create(
                        produto=produto,
                        local_saida=local_saida,
                        local_entrada=local_entrada,
                        quantidade=quantidade,
                        usuario=usuario,
                        responsavel_id=responsavel_id,
                        observacao=observacao  # Salva a observação
                    )

            messages.success(request, "Transferência realizada com sucesso.")
            return redirect('lista_estoque')
        except Exception as e:
            messages.error(request, f"Ocorreu um erro: {e}")
            return redirect('transferencia_estoque')

    return render(request, 'estoque/forms/transferencia_estoque.html', {
        'locais_saida': Estoque.objects.values_list('local', flat=True).distinct(),
        'locais_entrada': Armazem.objects.values_list('name', flat=True),
        'funcionarios': Funcionario.objects.filter(status=True),
    })




