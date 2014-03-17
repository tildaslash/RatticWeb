from django import forms


class ExportForm(forms.Form):
    password = forms.CharField(widget=forms.PasswordInput())
