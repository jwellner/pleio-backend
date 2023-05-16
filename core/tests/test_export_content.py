from django.core.cache import cache
from django.db import connection
from django.urls import reverse
from mixer.backend.django import mixer

from activity.models import StatusUpdate
from blog.models import Blog
from cms.models import Page
from core.models import Comment
from core.tests.helpers import PleioTenantTestCase, override_config
from discussion.models import Discussion
from file.models import FileFolder
from news.models import News
from poll.models import Poll
from question.models import Question
from task.models import Task
from user.factories import UserFactory, AdminFactory
from wiki.models import Wiki


class TestExportContentTestCase(PleioTenantTestCase):
    def setUp(self):
        super().setUp()

        self.user = UserFactory()
        self.admin = AdminFactory()

        self.update = mixer.blend(StatusUpdate)
        self.blog = mixer.blend(Blog)
        self.blog2 = mixer.blend(Blog)
        self.discussion = mixer.blend(Discussion)
        self.page = mixer.blend(Page)
        self.news = mixer.blend(News)
        self.file = mixer.blend(FileFolder)
        self.poll = mixer.blend(Poll)
        self.question = mixer.blend(Question)
        self.task = mixer.blend(Task)
        self.wiki = mixer.blend(Wiki)
        self.comment = Comment.objects.create(
            owner=self.user,
            container=self.blog
        )

    def tearDown(self):
        super().tearDown()

    @override_config(IS_CLOSED=False)
    def test_export_content_blog_not_logged_in(self):

        response = self.client.get("/exporting/content/blog")
        content = response.getvalue().decode()

        self.assertEqual(response.status_code, 401)
        self.assertNotIn(self.blog.title, content)
        self.assertTemplateUsed("react.html")

    @override_config(IS_CLOSED=False)
    def test_export_content_blog_not_admin(self):
        self.client.force_login(self.user)

        response = self.client.get(reverse("content_export_type", args=["blog"]))
        content = response.getvalue().decode()

        self.assertEqual(response.status_code, 403)
        self.assertNotIn(self.blog.title, content)
        self.assertTemplateUsed("react.html")

    @override_config(IS_CLOSED=False)
    def test_not_enabled_for_export_content_type(self):
        invalid_content_type = "Taumatawhakatangihangakoauauotamateaturipukakapikimaungahoronukupokaiwhenuakitanatahu"
        self.client.force_login(self.admin)

        response = self.client.get(reverse("content_export_type", args=[invalid_content_type]))

        self.assertEqual(response.status_code, 404)
        self.assertTemplateUsed("react.html")

    @override_config(IS_CLOSED=False)
    def test_export_content_activity(self):
        self.client.force_login(self.admin)
        response = self.client.get(reverse("content_export_type", args=["statusupdate"]))
        self.assertEqual(len(list(response.streaming_content)), 2)

    @override_config(IS_CLOSED=False)
    def test_export_content_blog(self):
        self.client.force_login(self.admin)
        response = self.client.get(reverse("content_export_type", args=["blog"]))
        self.assertEqual(len(list(response.streaming_content)), 3)

    @override_config(IS_CLOSED=False)
    def test_export_content_page(self):
        self.client.force_login(self.admin)
        response = self.client.get(reverse("content_export_type", args=["page"]))
        self.assertEqual(len(list(response.streaming_content)), 2)

    @override_config(IS_CLOSED=False)
    def test_export_content_discussion(self):
        self.client.force_login(self.admin)
        response = self.client.get(reverse("content_export_type", args=["discussion"]))
        self.assertEqual(len(list(response.streaming_content)), 2)

    @override_config(IS_CLOSED=False)
    def test_export_content_file(self):
        self.client.force_login(self.admin)
        response = self.client.get(reverse("content_export_type", args=["file"]))
        self.assertEqual(len(list(response.streaming_content)), 2)

    @override_config(IS_CLOSED=False)
    def test_export_content_news(self):
        self.client.force_login(self.admin)
        response = self.client.get(reverse("content_export_type", args=["news"]))
        self.assertEqual(len(list(response.streaming_content)), 2)
    
    @override_config(IS_CLOSED=False)
    def test_export_content_poll(self):
        self.client.force_login(self.admin)
        response = self.client.get(reverse("content_export_type", args=["poll"]))
        self.assertEqual(len(list(response.streaming_content)), 2)

    @override_config(IS_CLOSED=False)
    def test_export_content_question(self):
        self.client.force_login(self.admin)
        response = self.client.get(reverse("content_export_type", args=["question"]))
        self.assertEqual(len(list(response.streaming_content)), 2)

    @override_config(IS_CLOSED=False)
    def test_export_content_wiki(self):
        self.client.force_login(self.admin)
        response = self.client.get(reverse("content_export_type", args=["wiki"]))
        self.assertEqual(len(list(response.streaming_content)), 2)

    @override_config(IS_CLOSED=False)
    def test_export_content_task(self):
        self.client.force_login(self.admin)
        response = self.client.get(reverse("content_export_type", args=["task"]))
        self.assertEqual(len(list(response.streaming_content)), 2)

    @override_config(IS_CLOSED=False)
    def test_export_content_comment(self):
        self.client.force_login(self.admin)
        response = self.client.get(reverse("content_export_type", args=["comment"]))
        self.assertEqual(len(list(response.streaming_content)), 2)
