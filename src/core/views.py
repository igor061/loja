# coding: utf-8
from src.core.nfedjango import NFe2ProdutoTable
from src.core.parseNFeSite import ParseNFeHtml, NFe2
from django.views.generic.simple import direct_to_template
from src.core.forms import UploadFileForm
from django.http import HttpResponse, HttpResponseRedirect
from django.shortcuts import render_to_response, render
from django.template.context import RequestContext

def index(request):
    context = RequestContext(request)
    return render_to_response('index.html', context)

def nfe_upload(request):
    form = UploadFileForm()
    return direct_to_template(request, 'core/upload.html', {'form': form})


def handle_uploaded_file(request):
    if request.method == 'POST':
        form = UploadFileForm(request.POST, request.FILES)
        if form.is_valid():
            f = request.FILES['arquivo']
            buf = f.read()

            parser = ParseNFeHtml()
            mapNfe2 = parser.doParser(buf)


            markup = float(request.POST['markup'])
            prodDict = mapNfe2['produtos']

            totalVenda = 0


            for p in prodDict:
                p['custo'] = p['valor'] + p['frete'] + p['seguro'] + p['ipi'] - p['desconto']
                p['preco'] = p['custo'] * markup / p['qtd']
                totalVenda += p['preco'] * p['qtd']


            tableProd = NFe2ProdutoTable(prodDict)

            markupReal = (totalVenda / mapNfe2['valores']['total'])
            if abs(markupReal - markup) > 0.005:
                msgError = "Atenção o markup sobre o preço de custo esta diferente!!!! O markup está %.3f e foi pedido %.3f" %(
                    markupReal, markup
                )
            else:
                msgError = ""

            return render(request, 'core/detalhesnfe.html', {
                        'table': tableProd,
                        'nfe': mapNfe2,
                        'totalVenda': totalVenda,
                        'msgError': msgError})
        else:
            return direct_to_template(request, 'core/upload.html', {'form': form})
    else:
        context = RequestContext(request)
        print request.POST
        tableProd = context.get('table')
        if not(tableProd):
            form = UploadFileForm()
            return direct_to_template(request, 'core/upload.html', {'form': form})

    return render(request, 'core/detalhesnfe.html', {'table': tableProd})