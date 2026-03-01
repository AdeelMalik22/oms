from django import forms
from django.contrib.auth import get_user_model
from django.utils.crypto import get_random_string
from accounts.models import Department
from .models import Employee, Designation

User = get_user_model()

WIDGET = {'class': 'form-control'}


class EmployeeForm(forms.ModelForm):
    first_name = forms.CharField(widget=forms.TextInput(attrs=WIDGET))
    last_name = forms.CharField(widget=forms.TextInput(attrs=WIDGET))
    email = forms.EmailField(widget=forms.EmailInput(attrs=WIDGET))

    class Meta:
        model = Employee
        fields = ['department', 'designation', 'hire_date', 'salary', 'address', 'nic',
                  'emergency_contact_name', 'emergency_contact_phone']
        widgets = {
            'department': forms.Select(attrs=WIDGET),
            'designation': forms.Select(attrs=WIDGET),
            'hire_date': forms.DateInput(attrs={**WIDGET, 'type': 'date'}),
            'salary': forms.NumberInput(attrs=WIDGET),
            'address': forms.Textarea(attrs={**WIDGET, 'rows': 2}),
            'nic': forms.TextInput(attrs=WIDGET),
            'emergency_contact_name': forms.TextInput(attrs=WIDGET),
            'emergency_contact_phone': forms.TextInput(attrs=WIDGET),
        }

    def save(self, commit=True):
        employee = super().save(commit=False)
        if not employee.pk:
            user = User.objects.create_user(
                username=self.cleaned_data['email'],
                email=self.cleaned_data['email'],
                first_name=self.cleaned_data['first_name'],
                last_name=self.cleaned_data['last_name'],
                password=get_random_string(12),
            )
            employee.user = user
        if commit:
            employee.save()
        return employee


class DesignationForm(forms.ModelForm):
    class Meta:
        model = Designation
        fields = '__all__'
        widgets = {'title': forms.TextInput(attrs=WIDGET), 'department': forms.Select(attrs=WIDGET), 'level': forms.NumberInput(attrs=WIDGET)}


class DepartmentForm(forms.ModelForm):
    class Meta:
        model = Department
        fields = ['name']
        widgets = {'name': forms.TextInput(attrs=WIDGET)}

