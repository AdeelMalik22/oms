from django import forms
from .models import Project, Task, ProjectMember
from employees.models import Employee

W = {'class': 'form-control'}


class ProjectMemberForm(forms.ModelForm):
    class Meta:
        model = ProjectMember
        fields = ['employee', 'role']
        widgets = {
            'employee': forms.Select(attrs=W),
            'role': forms.TextInput(attrs={**W, 'placeholder': 'e.g. Developer, Designer, Tester'}),
        }


class ProjectForm(forms.ModelForm):
    class Meta:
        model = Project
        fields = ['name', 'description', 'start_date', 'end_date', 'status', 'manager', 'budget']
        widgets = {
            'name': forms.TextInput(attrs=W),
            'description': forms.Textarea(attrs={**W, 'rows': 3}),
            'start_date': forms.DateInput(attrs={**W, 'type': 'date'}),
            'end_date': forms.DateInput(attrs={**W, 'type': 'date'}),
            'status': forms.Select(attrs=W),
            'manager': forms.Select(attrs=W),
            'budget': forms.NumberInput(attrs=W),
        }


class TaskForm(forms.ModelForm):
    class Meta:
        model = Task
        fields = ['title', 'description', 'assigned_to', 'priority', 'status', 'due_date']
        widgets = {
            'title': forms.TextInput(attrs=W),
            'description': forms.Textarea(attrs={**W, 'rows': 2}),
            'assigned_to': forms.Select(attrs=W),
            'priority': forms.Select(attrs=W),
            'status': forms.Select(attrs=W),
            'due_date': forms.DateInput(attrs={**W, 'type': 'date'}),
        }

    def __init__(self, *args, project=None, **kwargs):
        super().__init__(*args, **kwargs)
        if project is not None:
            # Only show employees who are members of this project
            member_ids = project.members.values_list('employee_id', flat=True)
            self.fields['assigned_to'].queryset = Employee.objects.filter(
                id__in=member_ids
            ).select_related('user')
            self.fields['assigned_to'].empty_label = '— Select member —'
        else:
            self.fields['assigned_to'].queryset = Employee.objects.select_related('user').all()

