from django import forms
from .models import Attendance, LeaveRequest, ResignationRequest

W = {'class': 'form-control'}


class AttendanceForm(forms.ModelForm):
    class Meta:
        model = Attendance
        fields = ['employee', 'date', 'check_in', 'check_out', 'status', 'notes']
        widgets = {
            'employee': forms.Select(attrs=W),
            'date': forms.DateInput(attrs={**W, 'type': 'date'}),
            'check_in': forms.TimeInput(attrs={**W, 'type': 'time'}),
            'check_out': forms.TimeInput(attrs={**W, 'type': 'time'}),
            'status': forms.Select(attrs=W),
            'notes': forms.Textarea(attrs={**W, 'rows': 2}),
        }


class LeaveRequestForm(forms.ModelForm):
    class Meta:
        model = LeaveRequest
        fields = ['leave_type', 'start_date', 'end_date', 'reason']
        widgets = {
            'leave_type': forms.Select(attrs=W),
            'start_date': forms.DateInput(attrs={**W, 'type': 'date'}),
            'end_date': forms.DateInput(attrs={**W, 'type': 'date'}),
            'reason': forms.Textarea(attrs={**W, 'rows': 3}),
        }


class ResignationRequestForm(forms.ModelForm):
    class Meta:
        model = ResignationRequest
        fields = ['requested_last_working_date', 'reason']
        widgets = {
            'requested_last_working_date': forms.DateInput(attrs={**W, 'type': 'date'}),
            'reason': forms.Textarea(attrs={**W, 'rows': 4}),
        }
        labels = {
            'requested_last_working_date': 'Last Working Date',
            'reason': 'Reason for Resignation',
        }
