from django import forms
from .models import Document, DocumentVersion

W = {'class': 'form-control'}


class DocumentForm(forms.ModelForm):
    class Meta:
        model = Document
        fields = ['title', 'file', 'department', 'category']
        widgets = {
            'title': forms.TextInput(attrs=W),
            'department': forms.Select(attrs=W),
            'category': forms.Select(attrs=W),
        }


class DocumentVersionForm(forms.Form):
    file = forms.FileField(widget=forms.ClearableFileInput(attrs=W))
    notes = forms.CharField(required=False, widget=forms.Textarea(attrs={**W, 'rows': 2}))

