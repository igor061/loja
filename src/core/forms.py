# encoding: utf-8

from django import forms

class UploadFileForm(forms.Form):
    markup = forms.DecimalField()
    arquivo  = forms.FileField()