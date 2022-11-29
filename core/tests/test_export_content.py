from django.core.cache import cache
from django.db import connection
from mixer.backend.django import mixer

from activity.models import StatusUpdate
from blog.models import Blog
from cms.models import Page
from core.models import Comment
from discussion.models import Discussion
from file.models import FileFolder
from news.models import News
from poll.models import Poll
from question.models import Question
from task.models import Task
from tenants.helpers import FastTenantTestCase
from user.models import User
from wiki.models import Wiki


class TestExportContentTestCase(FastTenantTestCase):
    def setUp(self):
        super().setUp()

        self.user = mixer.blend(User)
        self.admin = mixer.blend(User, roles=['ADMIN'])

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

        cache.set("%s%s" % (connection.schema_name, 'IS_CLOSED'), False)

    def tearDown(self):
        cache.clear()
        super().tearDown()

    def test_export_content_blog_not_logged_in(self):
        response = self.client.get("/exporting/content/blog")
        self.assertEqual(response.streaming, False)

    def test_export_content_blog_not_admin(self):
        self.client.force_login(self.user)
        response = self.client.get("/exporting/content/blog")
        self.assertEqual(response.streaming, False)

    def test_export_content_activity(self):
        self.client.force_login(self.admin)
        response = self.client.get("/exporting/content/statusupdate")
        self.assertEqual(response.streaming, True)
        self.assertEqual(len(list(response.streaming_content)), 2)

    def test_export_content_blog(self):
        self.client.force_login(self.admin)
        response = self.client.get("/exporting/content/blog")
        self.assertEqual(response.streaming, True)
        self.assertEqual(len(list(response.streaming_content)), 3)

    def test_export_content_page(self):
        self.client.force_login(self.admin)
        response = self.client.get("/exporting/content/page")
        self.assertEqual(response.streaming, True)
        self.assertEqual(len(list(response.streaming_content)), 2)

    def test_export_content_discussion(self):
        self.client.force_login(self.admin)
        response = self.client.get("/exporting/content/discussion")
        self.assertEqual(response.streaming, True)
        self.assertEqual(len(list(response.streaming_content)), 2)

    def test_export_content_file(self):
        self.client.force_login(self.admin)
        response = self.client.get("/exporting/content/file")
        self.assertEqual(response.streaming, True)
        self.assertEqual(len(list(response.streaming_content)), 2)

    def test_export_content_news(self):
        self.client.force_login(self.admin)
        response = self.client.get("/exporting/content/news")
        self.assertEqual(response.streaming, True)
        self.assertEqual(len(list(response.streaming_content)), 2)

    def test_export_content_poll(self):
        self.client.force_login(self.admin)
        response = self.client.get("/exporting/content/poll")
        self.assertEqual(response.streaming, True)
        self.assertEqual(len(list(response.streaming_content)), 2)

    def test_export_content_question(self):
        self.client.force_login(self.admin)
        response = self.client.get("/exporting/content/question")
        self.assertEqual(response.streaming, True)
        self.assertEqual(len(list(response.streaming_content)), 2)

    def test_export_content_wiki(self):
        self.client.force_login(self.admin)
        response = self.client.get("/exporting/content/wiki")
        self.assertEqual(response.streaming, True)
        self.assertEqual(len(list(response.streaming_content)), 2)

    def test_export_content_task(self):
        self.client.force_login(self.admin)
        response = self.client.get("/exporting/content/task")
        self.assertEqual(response.streaming, True)
        self.assertEqual(len(list(response.streaming_content)), 2)

    def test_export_content_comment(self):
        self.client.force_login(self.admin)
        response = self.client.get("/exporting/content/comment")
        self.assertEqual(response.streaming, True)
        self.assertEqual(len(list(response.streaming_content)), 2)
