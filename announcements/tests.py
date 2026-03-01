from django.test import TestCase
from django.urls import reverse
from accounts.tests import make_user, make_dept
from announcements.models import Announcement


def make_announcement(user, title='Test Announcement', content='Content here', dept=None):
    return Announcement.objects.create(
        title=title, content=content,
        created_by=user, target_department=dept,
        is_active=True, is_pinned=False
    )


# ─── Model Tests ─────────────────────────────────────────────────────────────

class AnnouncementModelTest(TestCase):
    def test_announcement_str(self):
        user = make_user('ann_str_user')
        a = make_announcement(user, 'Big News')
        self.assertEqual(str(a), 'Big News')

    def test_announcement_defaults(self):
        user = make_user('ann_def_user')
        a = make_announcement(user)
        self.assertTrue(a.is_active)
        self.assertFalse(a.is_pinned)

    def test_pinned_ordered_first(self):
        user = make_user('ann_ord_user')
        make_announcement(user, 'Regular', 'C')
        a2 = Announcement.objects.create(title='Pinned', content='C', created_by=user, is_pinned=True)
        qs = list(Announcement.objects.all())
        self.assertEqual(qs[0], a2)


# ─── View Tests ───────────────────────────────────────────────────────────────

class AnnouncementListViewTest(TestCase):
    def setUp(self):
        self.user = make_user('ann_list_user')
        self.client.force_login(self.user)

    def test_list_loads(self):
        r = self.client.get(reverse('announcements:list'))
        self.assertEqual(r.status_code, 200)

    def test_list_requires_login(self):
        self.client.logout()
        r = self.client.get(reverse('announcements:list'))
        self.assertEqual(r.status_code, 302)


class AnnouncementAddViewTest(TestCase):
    def setUp(self):
        self.admin = make_user('ann_add_user', role_name='Admin')
        self.client.force_login(self.admin)

    def test_add_page_loads(self):
        r = self.client.get(reverse('announcements:add'))
        self.assertEqual(r.status_code, 200)

    def test_add_creates_announcement(self):
        before = Announcement.objects.count()
        self.client.post(reverse('announcements:add'), {
            'title': 'Holiday Notice',
            'content': 'Office closed on Friday.',
        })
        self.assertEqual(Announcement.objects.count(), before + 1)

    def test_add_sets_created_by(self):
        self.client.post(reverse('announcements:add'), {
            'title': 'By Check',
            'content': 'Text',
        })
        ann = Announcement.objects.get(title='By Check')
        self.assertEqual(ann.created_by, self.admin)

    def test_add_with_department(self):
        dept = make_dept('Marketing')
        self.client.post(reverse('announcements:add'), {
            'title': 'Dept Notice',
            'content': 'For Marketing only.',
            'target_department': dept.pk,
        })
        ann = Announcement.objects.get(title='Dept Notice')
        self.assertEqual(ann.target_department, dept)


class AnnouncementPinToggleTest(TestCase):
    def setUp(self):
        self.admin = make_user('ann_pin_user', role_name='Admin')
        self.client.force_login(self.admin)
        self.ann = make_announcement(self.admin, 'Pinable')

    def test_pin_toggles_to_true(self):
        self.client.post(reverse('announcements:pin', kwargs={'pk': self.ann.pk}))
        self.ann.refresh_from_db()
        self.assertTrue(self.ann.is_pinned)

    def test_pin_toggles_back_to_false(self):
        self.ann.is_pinned = True
        self.ann.save()
        self.client.post(reverse('announcements:pin', kwargs={'pk': self.ann.pk}))
        self.ann.refresh_from_db()
        self.assertFalse(self.ann.is_pinned)


class AnnouncementDeleteViewTest(TestCase):
    def setUp(self):
        self.admin = make_user('ann_del_user', role_name='Admin')
        self.client.force_login(self.admin)
        self.ann = make_announcement(self.admin, 'To Delete')

    def test_delete_sets_inactive(self):
        self.client.post(reverse('announcements:delete', kwargs={'pk': self.ann.pk}))
        self.ann.refresh_from_db()
        self.assertFalse(self.ann.is_active)

    def test_delete_does_not_remove_from_db(self):
        self.client.post(reverse('announcements:delete', kwargs={'pk': self.ann.pk}))
        self.assertTrue(Announcement.objects.filter(pk=self.ann.pk).exists())
