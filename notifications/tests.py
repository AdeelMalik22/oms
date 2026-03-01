from django.test import TestCase
from django.urls import reverse
from accounts.tests import make_user
from notifications.models import Notification
from notifications.services import create_notification


# ─── Model & Service Tests ───────────────────────────────────────────────────

class NotificationModelTest(TestCase):
    def test_notification_str(self):
        user = make_user('notif_str_user')
        n = Notification.objects.create(recipient=user, title='Hello', message='World')
        self.assertIn('Hello', str(n))

    def test_notification_defaults_to_unread(self):
        user = make_user('notif_def_user')
        n = Notification.objects.create(recipient=user, title='T', message='M')
        self.assertFalse(n.is_read)

    def test_create_notification_service(self):
        user = make_user('svc_user')
        before = Notification.objects.count()
        create_notification(user, 'Test', 'Body', notif_type='warning', link='/test/')
        self.assertEqual(Notification.objects.count(), before + 1)
        n = Notification.objects.get(recipient=user)
        self.assertEqual(n.type, 'warning')
        self.assertEqual(n.link, '/test/')


# ─── View Tests ─────────────────────────────────────────────────────────────

class NotificationListViewTest(TestCase):
    def setUp(self):
        self.user = make_user('notif_list_user')
        self.client.force_login(self.user)
        Notification.objects.create(recipient=self.user, title='N1', message='M1')
        Notification.objects.create(recipient=self.user, title='N2', message='M2')

    def test_list_loads(self):
        r = self.client.get(reverse('notifications:list'))
        self.assertEqual(r.status_code, 200)

    def test_list_requires_login(self):
        self.client.logout()
        r = self.client.get(reverse('notifications:list'))
        self.assertEqual(r.status_code, 302)


class MarkReadViewTest(TestCase):
    def setUp(self):
        self.user = make_user('mark_read_user')
        self.client.force_login(self.user)
        self.notif = Notification.objects.create(recipient=self.user, title='Unread', message='Msg')

    def test_mark_single_read(self):
        self.client.get(reverse('notifications:mark_read', kwargs={'pk': self.notif.pk}))
        self.notif.refresh_from_db()
        self.assertTrue(self.notif.is_read)

    def test_mark_read_redirects(self):
        r = self.client.get(reverse('notifications:mark_read', kwargs={'pk': self.notif.pk}))
        self.assertEqual(r.status_code, 302)

    def test_cannot_mark_other_users_notification(self):
        other = make_user('other_notif_user2')
        notif2 = Notification.objects.create(recipient=other, title='Other', message='X')
        r = self.client.get(reverse('notifications:mark_read', kwargs={'pk': notif2.pk}))
        self.assertEqual(r.status_code, 404)


class MarkAllReadViewTest(TestCase):
    def setUp(self):
        self.user = make_user('mark_all_user')
        self.client.force_login(self.user)
        for i in range(4):
            Notification.objects.create(recipient=self.user, title=f'N{i}', message='M')

    def test_mark_all_read_marks_all(self):
        self.client.get(reverse('notifications:mark_all_read'))
        unread = Notification.objects.filter(recipient=self.user, is_read=False).count()
        self.assertEqual(unread, 0)

    def test_mark_all_read_redirects(self):
        r = self.client.get(reverse('notifications:mark_all_read'))
        self.assertEqual(r.status_code, 302)
