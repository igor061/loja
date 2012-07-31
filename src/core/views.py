# coding: utf-8
from src.core.parseNFeSite import ParseNFeHtml, NFe2
from django.views.generic.simple import direct_to_template
from src.core.forms import UploadFileForm
from django.http import HttpResponse, HttpResponseRedirect
from django.shortcuts import render_to_response
from django.template.context import RequestContext

def index(request):
    context = RequestContext(request)
    return render_to_response('index.html', context)

def nfe_upload(request):

    if request.method == 'POST':
        form = UploadFileForm(request.POST, request.FILES)
        if form.is_valid():
            return handle_uploaded_file(request)

    else:
        form = UploadFileForm()
    return direct_to_template(request, 'core/upload.html', {'form': form})


def handle_uploaded_file(request):

    f = request.FILES['file']
    buf = f.read()

    parser = ParseNFeHtml()
    mapNfe2 = parser.doParser(buf)


    nfe2 = NFe2(mapNfe2)

    return direct_to_template(request, 'core/detalhesnfe.html', { 'nfe': nfe2})
