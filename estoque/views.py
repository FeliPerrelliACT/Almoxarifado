from django.contrib.auth.decorators import login_required
from .models import EntradaEstoque, Estoque, SaidaEstoque
from .forms import EntradaEstoqueForm, SaidaEstoqueForm
from django.http import HttpResponse, JsonResponse
from django.shortcuts import render, redirect
from reportlab.lib.utils import ImageReader
from reportlab.lib.pagesizes import A4
from suprimentos.models import Product
from reportlab.pdfgen import canvas
from django.db.models import Q
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

    return render(request, 'estoque/forms/entrada_estoque.html', {'form': form})

@login_required
def saida_estoque(request):
    locais_estoque = Estoque.objects.values('local').distinct()

    if request.method == 'POST':
        local = request.POST.get('local')
        produtos = []

        # Coletar todos os produtos e quantidades do formulário
        for key, value in request.POST.items():
            if key.startswith('produto-'):
                produto_id = value
                quantidade = int(request.POST.get(f'quantidade-{key.split("-")[1]}'))
                produtos.append((produto_id, quantidade))

        for produto_id, quantidade in produtos:
            estoque = Estoque.objects.filter(product_id=produto_id, local=local).first()
            if estoque and estoque.quantidade >= quantidade:
                produto = Product.objects.get(id=produto_id)

                # Registrar a saída
                SaidaEstoque.objects.create(
                    product=produto,
                    local=local,
                    quantidade=quantidade,
                    usuario_registrante=request.user
                )

                # Atualizar a quantidade no estoque
                estoque.quantidade -= quantidade
                estoque.save()

        return redirect('lista_estoque')

    return render(request, 'estoque/forms/saida_estoque.html', {
        'locais_estoque': locais_estoque
    })

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

def get_produtos_por_local(request, local):
    produtos = Estoque.objects.filter(local=local)
    produtos_info = []

    for estoque in produtos:
        produtos_info.append({
            'id': estoque.product.id,
            'product_name': estoque.product.product_name,
            'quantidade': estoque.quantidade
        })

    return JsonResponse({'produtos': produtos_info})
