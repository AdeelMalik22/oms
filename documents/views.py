import mimetypes
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.db.models import Q
from .models import Document, DocumentVersion, DocumentCategory
from .forms import DocumentForm, DocumentVersionForm

ALLOWED_MIMES = {
    'application/pdf', 'application/msword',
    'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
    'application/vnd.ms-excel',
    'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
    'image/png', 'image/jpeg',
}


def _validate_file(f):
    mime, _ = mimetypes.guess_type(f.name)
    if mime not in ALLOWED_MIMES:
        return False
    if f.size > 10 * 1024 * 1024:
        return False
    return True


@login_required
def document_list(request):
    qs = Document.objects.select_related('uploaded_by', 'department', 'category')
    if not (request.user.is_admin or request.user.is_hr):
        qs = qs.filter(Q(department=request.user.department) | Q(department__isnull=True))
    q = request.GET.get('q', '')
    if q:
        qs = qs.filter(Q(title__icontains=q) | Q(category__name__icontains=q))
    return render(request, 'documents/list.html', {'documents': qs, 'q': q})


@login_required
def document_upload(request):
    form = DocumentForm(request.POST or None, request.FILES or None)
    if form.is_valid():
        f = request.FILES.get('file')
        if not _validate_file(f):
            messages.error(request, 'Invalid file type or file exceeds 10MB.')
        else:
            doc = form.save(commit=False)
            doc.uploaded_by = request.user
            doc.save()
            DocumentVersion.objects.create(
                document=doc, file=doc.file, version=1, uploaded_by=request.user
            )
            messages.success(request, 'Document uploaded.')
            return redirect('documents:list')
    return render(request, 'documents/upload.html', {'form': form})


@login_required
def document_detail(request, pk):
    doc = get_object_or_404(Document, pk=pk)
    versions = doc.versions.all()
    version_form = DocumentVersionForm(request.POST or None, request.FILES or None)
    if request.method == 'POST' and version_form.is_valid():
        f = request.FILES.get('file')
        if not _validate_file(f):
            messages.error(request, 'Invalid file type or exceeds 10MB.')
        else:
            new_version = doc.version + 1
            DocumentVersion.objects.create(
                document=doc, file=f, version=new_version,
                uploaded_by=request.user, notes=version_form.cleaned_data.get('notes', '')
            )
            doc.version = new_version
            doc.file = f
            doc.save()
            messages.success(request, f'Version {new_version} uploaded.')
            return redirect('documents:detail', pk=pk)
    return render(request, 'documents/detail.html', {'doc': doc, 'versions': versions, 'version_form': version_form})
