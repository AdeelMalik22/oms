from django import forms
from .models import Asset

W = {'class': 'form-control'}


class AssetForm(forms.ModelForm):
    class Meta:
        model = Asset
        fields = ['name', 'category', 'serial_number', 'purchase_date', 'status', 'condition', 'value']
        widgets = {
            'name': forms.TextInput(attrs=W),
            'category': forms.Select(attrs=W),
            'serial_number': forms.TextInput(attrs=W),
            'purchase_date': forms.DateInput(attrs={**W, 'type': 'date'}),
            'status': forms.Select(attrs=W),
            'condition': forms.TextInput(attrs=W),
            'value': forms.NumberInput(attrs=W),
        }

