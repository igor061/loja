# coding: utf-8
from django.http import HttpResponse
from django.shortcuts import render_to_response
from django.template.context import RequestContext

def index(request):
    context = RequestContext(request)
    return render_to_response('index.html', context)

def nfe_upload(request):
    return HttpResponse("nfe upload")