import datetime
from django.test import TestCase
from django.urls import reverse
from accounts.tests import make_user
from employees.tests import make_employee
from projects.models import Project, Task, ProjectMember
from notifications.models import Notification


def make_project(name='Test Project', manager=None, status='Active'):
    return Project.objects.create(
        name=name, description='A test project',
        start_date=datetime.date(2026, 1, 1),
        end_date=datetime.date(2026, 12, 31),
        status=status, manager=manager, budget=100000
    )


# ─── Model Tests ─────────────────────────────────────────────────────────────

class ProjectModelTest(TestCase):
    def test_project_str(self):
        p = make_project('Alpha Project')
        self.assertEqual(str(p), 'Alpha Project')

    def test_progress_zero_with_no_tasks(self):
        p = make_project()
        self.assertEqual(p.progress, 0)

    def test_progress_calculation(self):
        emp = make_employee('prog_emp')
        p = make_project(manager=emp)
        Task.objects.create(project=p, title='T1', status='Done')
        Task.objects.create(project=p, title='T2', status='Done')
        Task.objects.create(project=p, title='T3', status='In Progress')
        Task.objects.create(project=p, title='T4', status='To-Do')
        self.assertEqual(p.progress, 50)

    def test_progress_100_when_all_done(self):
        p = make_project()
        for i in range(3):
            Task.objects.create(project=p, title=f'Task{i}', status='Done')
        self.assertEqual(p.progress, 100)

    def test_task_str(self):
        p = make_project()
        t = Task.objects.create(project=p, title='Fix bug', status='To-Do')
        self.assertIn('Fix bug', str(t))

    def test_project_member_unique(self):
        emp = make_employee('mem_emp')
        p = make_project(manager=emp)
        ProjectMember.objects.create(project=p, employee=emp, role='Dev')
        with self.assertRaises(Exception):
            ProjectMember.objects.create(project=p, employee=emp, role='Lead')


# ─── View Tests ───────────────────────────────────────────────────────────────

class ProjectListViewTest(TestCase):
    def setUp(self):
        self.mgr = make_user('mgr_proj', role_name='Manager')
        self.client.force_login(self.mgr)

    def test_list_loads(self):
        r = self.client.get(reverse('projects:list'))
        self.assertEqual(r.status_code, 200)

    def test_list_requires_login(self):
        self.client.logout()
        r = self.client.get(reverse('projects:list'))
        self.assertEqual(r.status_code, 302)


class ProjectAddViewTest(TestCase):
    def setUp(self):
        self.mgr = make_user('mgr_add', role_name='Manager')
        self.client.force_login(self.mgr)

    def test_add_page_loads(self):
        r = self.client.get(reverse('projects:add'))
        self.assertEqual(r.status_code, 200)

    def test_add_creates_project(self):
        before = Project.objects.count()
        self.client.post(reverse('projects:add'), {
            'name': 'New Project X',
            'description': 'Desc',
            'status': 'Planning',
            'budget': 5000,
        })
        self.assertEqual(Project.objects.count(), before + 1)

    def test_add_invalid_data_rerenders_form(self):
        r = self.client.post(reverse('projects:add'), {})
        self.assertEqual(r.status_code, 200)


class ProjectDetailViewTest(TestCase):
    def setUp(self):
        self.mgr = make_user('mgr_det', role_name='Manager')
        self.client.force_login(self.mgr)
        self.project = make_project()

    def test_detail_loads(self):
        r = self.client.get(reverse('projects:detail', kwargs={'pk': self.project.pk}))
        self.assertEqual(r.status_code, 200)

    def test_detail_404_for_invalid_pk(self):
        r = self.client.get(reverse('projects:detail', kwargs={'pk': 99999}))
        self.assertEqual(r.status_code, 404)


class TaskAddViewTest(TestCase):
    def setUp(self):
        self.mgr = make_user('mgr_task', role_name='Manager')
        self.client.force_login(self.mgr)
        self.project = make_project()

    def test_task_form_loads(self):
        r = self.client.get(reverse('projects:task_add', kwargs={'project_pk': self.project.pk}))
        self.assertEqual(r.status_code, 200)

    def test_task_add_creates_task(self):
        before = Task.objects.count()
        self.client.post(
            reverse('projects:task_add', kwargs={'project_pk': self.project.pk}),
            {'title': 'Test Task', 'priority': 'Medium', 'status': 'To-Do'}
        )
        self.assertEqual(Task.objects.count(), before + 1)

    def test_task_assigned_creates_notification(self):
        emp = make_employee('notif_emp')
        self.client.post(
            reverse('projects:task_add', kwargs={'project_pk': self.project.pk}),
            {'title': 'Notif Task', 'priority': 'High', 'status': 'To-Do', 'assigned_to': emp.pk}
        )
        self.assertTrue(Notification.objects.filter(recipient=emp.user).exists())


class TaskStatusUpdateViewTest(TestCase):
    def setUp(self):
        self.mgr = make_user('mgr_status', role_name='Manager')
        self.client.force_login(self.mgr)
        self.project = make_project()
        self.task = Task.objects.create(project=self.project, title='Status Task', status='To-Do')

    def test_status_update_changes_status(self):
        self.client.post(
            reverse('projects:task_status', kwargs={'pk': self.task.pk}),
            {'status': 'In Progress'}
        )
        self.task.refresh_from_db()
        self.assertEqual(self.task.status, 'In Progress')

    def test_done_status_sets_completed_at(self):
        self.client.post(
            reverse('projects:task_status', kwargs={'pk': self.task.pk}),
            {'status': 'Done'}
        )
        self.task.refresh_from_db()
        self.assertIsNotNone(self.task.completed_at)
