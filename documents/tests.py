from django.test import TestCase
from django.urls import reverse
from django.core.files.uploadedfile import SimpleUploadedFile
from accounts.tests import make_user, make_dept
from documents.models import Document, DocumentCategory, DocumentVersion
from audit.models import AuditLog
from audit.services import log_action


def make_doc_category(name='HR Policy'):
    cat, _ = DocumentCategory.objects.get_or_create(name=name)
    return cat


def make_pdf_file(name='test.pdf'):
    return SimpleUploadedFile(name, b'%PDF-1.4 fake pdf content', content_type='application/pdf')


# ─── Document Model Tests ─────────────────────────────────────────────────────

class DocumentModelTest(TestCase):
    def test_document_str(self):
        user = make_user('doc_str_user')
        cat = make_doc_category()
        f = make_pdf_file()
        doc = Document.objects.create(title='Policy v1', file=f, uploaded_by=user, category=cat)
        self.assertIn('Policy v1', str(doc))

    def test_document_category_str(self):
        cat = make_doc_category('Contract')
        self.assertEqual(str(cat), 'Contract')

    def test_document_version_str(self):
        user = make_user('doc_ver_user')
        cat = make_doc_category()
        doc = Document.objects.create(title='SOP', file=make_pdf_file('v1.pdf'), uploaded_by=user, category=cat)
        ver = DocumentVersion.objects.create(document=doc, file=make_pdf_file('v2.pdf'), version=2, uploaded_by=user)
        self.assertIn('SOP', str(ver))


# ─── Document View Tests ──────────────────────────────────────────────────────

class DocumentListViewTest(TestCase):
    def setUp(self):
        self.admin = make_user('doc_admin', role_name='Admin')
        self.client.force_login(self.admin)

    def test_list_loads(self):
        r = self.client.get(reverse('documents:list'))
        self.assertEqual(r.status_code, 200)

    def test_list_requires_login(self):
        self.client.logout()
        r = self.client.get(reverse('documents:list'))
        self.assertEqual(r.status_code, 302)

    def test_list_search(self):
        r = self.client.get(reverse('documents:list') + '?q=Policy')
        self.assertEqual(r.status_code, 200)


class DocumentUploadViewTest(TestCase):
    def setUp(self):
        self.admin = make_user('doc_upload_admin', role_name='Admin')
        self.client.force_login(self.admin)
        self.cat = make_doc_category()

    def test_upload_page_loads(self):
        r = self.client.get(reverse('documents:upload'))
        self.assertEqual(r.status_code, 200)

    def test_upload_valid_pdf_creates_document(self):
        before = Document.objects.count()
        self.client.post(reverse('documents:upload'), {
            'title': 'Leave Policy',
            'file': make_pdf_file(),
            'category': self.cat.pk,
        })
        self.assertEqual(Document.objects.count(), before + 1)

    def test_upload_also_creates_version_1(self):
        self.client.post(reverse('documents:upload'), {
            'title': 'Onboarding Doc',
            'file': make_pdf_file(),
            'category': self.cat.pk,
        })
        doc = Document.objects.get(title='Onboarding Doc')
        self.assertTrue(DocumentVersion.objects.filter(document=doc, version=1).exists())

    def test_upload_invalid_file_type_rejected(self):
        bad_file = SimpleUploadedFile('virus.exe', b'MZ bad content', content_type='application/octet-stream')
        before = Document.objects.count()
        self.client.post(reverse('documents:upload'), {
            'title': 'Bad File',
            'file': bad_file,
            'category': self.cat.pk,
        })
        self.assertEqual(Document.objects.count(), before)


class DocumentDetailViewTest(TestCase):
    def setUp(self):
        self.admin = make_user('doc_det_admin', role_name='Admin')
        self.client.force_login(self.admin)
        cat = make_doc_category()
        self.doc = Document.objects.create(
            title='Detail Doc', file=make_pdf_file('det.pdf'),
            uploaded_by=self.admin, category=cat
        )

    def test_detail_loads(self):
        r = self.client.get(reverse('documents:detail', kwargs={'pk': self.doc.pk}))
        self.assertEqual(r.status_code, 200)

    def test_detail_404_invalid_pk(self):
        r = self.client.get(reverse('documents:detail', kwargs={'pk': 99999}))
        self.assertEqual(r.status_code, 404)

    def test_upload_new_version(self):
        self.client.post(reverse('documents:detail', kwargs={'pk': self.doc.pk}), {
            'file': make_pdf_file('v2.pdf'),
            'notes': 'Updated policy',
        })
        self.doc.refresh_from_db()
        self.assertEqual(self.doc.version, 2)


# ─── Audit Log Tests ──────────────────────────────────────────────────────────

class AuditLogModelTest(TestCase):
    def test_audit_log_str(self):
        user = make_user('audit_user')
        log = AuditLog.objects.create(user=user, action='Created', model_name='Employee', object_id='5')
        self.assertIn('Created', str(log))
        self.assertIn('Employee', str(log))

    def test_log_action_service_creates_record(self):
        user = make_user('log_svc_user')
        before = AuditLog.objects.count()
        log_action(user, 'Deleted', 'Asset', '42')
        self.assertEqual(AuditLog.objects.count(), before + 1)

    def test_log_action_captures_ip_from_request(self):
        user = make_user('log_ip_user')
        from django.test import RequestFactory
        factory = RequestFactory()
        request = factory.get('/')
        request.META['REMOTE_ADDR'] = '192.168.1.100'
        log_action(user, 'Updated', 'Project', '7', request)
        log = AuditLog.objects.get(user=user, model_name='Project')
        self.assertEqual(log.ip_address, '192.168.1.100')

    def test_log_action_with_forwarded_ip(self):
        user = make_user('log_fwd_user')
        from django.test import RequestFactory
        factory = RequestFactory()
        request = factory.get('/')
        request.META['HTTP_X_FORWARDED_FOR'] = '10.0.0.1, 192.168.0.1'
        log_action(user, 'Viewed', 'Document', '3', request)
        log = AuditLog.objects.get(user=user, model_name='Document')
        self.assertEqual(log.ip_address, '10.0.0.1')
