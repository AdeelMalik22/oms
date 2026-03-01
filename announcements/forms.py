from django import forms
from .models import Announcement

W = {'class': 'form-control'}


class AnnouncementForm(forms.ModelForm):
    class Meta:
        model = Announcement
        fields = ['title', 'content', 'target_department', 'is_pinned']
        widgets = {
            'title': forms.TextInput(attrs=W),
            'content': forms.Textarea(attrs={**W, 'rows': 5}),
            'target_department': forms.Select(attrs=W),
        }

