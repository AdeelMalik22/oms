from django import forms
from .models import Payroll

W = {'class': 'form-control'}


class PayrollForm(forms.ModelForm):
    class Meta:
        model = Payroll
        fields = ['employee', 'month', 'year', 'basic_salary', 'total_allowances', 'total_deductions', 'status']
        widgets = {
            'employee': forms.Select(attrs=W),
            'month': forms.NumberInput(attrs={**W, 'min': 1, 'max': 12}),
            'year': forms.NumberInput(attrs={**W, 'min': 2000, 'max': 2100}),
            'basic_salary': forms.NumberInput(attrs=W),
            'total_allowances': forms.NumberInput(attrs=W),
            'total_deductions': forms.NumberInput(attrs=W),
            'status': forms.Select(attrs=W),
        }


AllowanceFormSet = forms.inlineformset_factory(
    Payroll, Payroll.allowances.rel.related_model,
    fields=['name', 'amount'], extra=1, can_delete=True,
    widgets={'name': forms.TextInput(attrs=W), 'amount': forms.NumberInput(attrs=W)}
)

DeductionFormSet = forms.inlineformset_factory(
    Payroll, Payroll.deductions.rel.related_model,
    fields=['name', 'amount'], extra=1, can_delete=True,
    widgets={'name': forms.TextInput(attrs=W), 'amount': forms.NumberInput(attrs=W)}
)

