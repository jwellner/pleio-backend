import faker
from mixer.backend.django import mixer
from unittest import mock

from django.apps import apps
from django.utils.timezone import localtime, timedelta
from django_tenants.test.cases import FastTenantTestCase

from core import override_local_config
from core.constances import ACCESS_TYPE
from core.factories import GroupFactory
from core.lib import get_acl
from core.mail_builders.frequent_overview import FrequentOverviewMailer, EntityCollection
from core.tasks import send_overview
from user.factories import UserFactory, EditorFactory


def create_user(interval='never', factory=UserFactory, **kwargs):
    user = factory(**kwargs)
    user.profile.overview_email_interval = interval
    user.profile.save()
    return user


def create_article(model_label, **kwargs):
    model = apps.get_model(model_label)
    assert model
    assert kwargs.get('owner')

    owner = kwargs['owner']
    kwargs.setdefault('read_access', [ACCESS_TYPE.public])
    kwargs.setdefault('write_access', [ACCESS_TYPE.user.format(owner.guid)])
    kwargs.setdefault('published', localtime())

    assert list(filter(lambda x: x in get_acl(owner), kwargs['read_access']))
    assert list(filter(lambda x: x in get_acl(owner), kwargs['write_access']))

    return mixer.blend(model, **kwargs)


class TestFrequentOverviewMailerTestCase(FastTenantTestCase):

    def setUp(self):
        super().setUp()

        self.user = create_user(email="user@localhost")
        self.author = create_user(email="author@localhost",
                                  factory=EditorFactory)

        generic = {'owner': self.author,
                   'rich_description': "Content!"}

        self.group = GroupFactory(owner=self.user,
                                  name=faker.Faker().sentence())

        self.content = [
            create_article('news.News', **generic,
                           title="Ordinary news"),
            create_article('news.News', **generic,
                           title="Bombshell news!",
                           group=self.group,
                           is_featured=True),
        ]

        self.mailer = FrequentOverviewMailer(user=self.user.guid,
                                             interval='weekly')

        self.daily_user = create_user('daily', email='daily@localhost')
        self.weekly_user = create_user('weekly', email="weekly@localhost")
        self.monthly_user = create_user('monthly', email="monthly@localhost")

    @override_local_config(EMAIL_OVERVIEW_SUBJECT='Overview email subject',
                           EMAIL_OVERVIEW_INTRO="Overview intro",
                           EMAIL_OVERVIEW_TITLE="Overview email title",
                           EMAIL_OVERVIEW_ENABLE_FEATURED=True,
                           EMAIL_OVERVIEW_FEATURED_TITLE="Featured content")
    @mock.patch('core.mail_builders.base.MailerBase.build_context')
    @mock.patch('core.mail_builders.frequent_overview.FrequentOverviewMailer.serialize_entities')
    def test_mailer_context(self, mocked_serialize_entities, mocked_build_context):
        mocked_build_context.return_value = {}
        mocked_serialize_entities.return_value = ["Entities"]

        context = self.mailer.get_context()

        self.assertEqual(mocked_build_context.call_args[1], {"user": self.user})
        self.assertEqual(7, len(context))

        self.assertEqual("Overview intro", context['intro_text'])
        self.assertEqual("Overview email title", context['title'])
        self.assertEqual(True, context['featured_enabled'])
        self.assertEqual("Featured content", context['featured_title'])
        self.assertEqual("Overview email subject", context['subject'])
        self.assertEqual(["Entities"], context['entities'])
        self.assertEqual(["Entities"], context['featured'])

    def test_mailer_properties(self):
        self.assertEqual(self.user.get_language(), self.mailer.get_language())
        self.assertEqual("email/send_overview_emails.html", self.mailer.get_template())
        self.assertEqual(self.user, self.mailer.get_receiver())
        self.assertEqual(self.user.email, self.mailer.get_receiver_email())
        self.assertEqual(None, self.mailer.get_sender())

    def test_mailer_subject(self):
        with override_local_config(NAME='Overridden sitename',
                                   EMAIL_OVERVIEW_SUBJECT=None):
            self.assertIn("Overridden sitename", self.mailer.get_subject())

        with override_local_config(NAME="Overridden sitename",
                                   EMAIL_OVERVIEW_SUBJECT='Overridden overview subject'):
            self.assertNotIn("Overridden sitename", self.mailer.get_subject())
            self.assertEqual("Overridden overview subject", self.mailer.get_subject())

    @mock.patch("core.tasks.cronjobs.schedule_frequent_overview_mail")
    def test_executed_at_the_right_spot(self, mocked_schedule_mail):
        for interval, expected_user in [('daily', self.daily_user),
                                        ('weekly', self.weekly_user),
                                        ('monthly', self.monthly_user)]:
            send_overview(self.tenant.schema_name, interval)
            self.assertEqual(1, mocked_schedule_mail.call_count)
            self.assertEqual((expected_user, interval), mocked_schedule_mail.call_args.args)
            mocked_schedule_mail.reset_mock()

    def test_serialize_entities(self):
        subset = [self.content[0],
                  self.content[1]]
        expected_result = [
            {"type_to_string": 'news',
             "featured_image_url": None,
             "title": subset[0].title,
             "description": subset[0].description,
             "owner_name": subset[0].owner.name,
             "url": subset[0].url,
             "group": False,
             "group_name": '',
             "group_url": '',
             "published": subset[0].published.strftime("%e-%m-%Y")},
            {"type_to_string": 'news',
             "featured_image_url": None,
             "title": subset[1].title,
             "description": subset[1].description,
             "owner_name": subset[1].owner.name,
             "url": subset[1].url,
             "group": True,
             "group_name": self.group.name,
             "group_url": self.group.url,
             "published": subset[1].published.strftime("%e-%m-%Y")},
        ]
        self.assertEqual(expected_result, FrequentOverviewMailer.serialize_entities(subset))


class TestFrequentOverviewMailerContentTestCase(FastTenantTestCase):

    def setUp(self) -> None:
        super().setUp()

        self.user = create_user(email="user@localhost")
        self.author = create_user(email="author@localhost",
                                  factory=EditorFactory)

        self.TODAY = localtime()
        self.YESTERDAY = localtime() - timedelta(days=1)
        self.LAST_WEEK = localtime() - timedelta(days=5)
        self.LAST_MONTH = localtime() - timedelta(days=20)
        self.PREVIOUS_MONTH = localtime() - timedelta(days=40)

    def build_collection(self, interval='weekly'):
        return EntityCollection(user=self.user, interval=interval)

    @mock.patch('core.mail_builders.frequent_overview.EntityCollection.get_entities')
    @mock.patch('core.mail_builders.frequent_overview.EntityCollection.get_featured')
    def test_has_content(self, mocked_featured, mocked_entities):
        mocked_entities.return_value = []
        mocked_featured.return_value = []
        collection = self.build_collection()
        self.assertFalse(collection.has_content())

        mocked_entities.return_value = [create_article('blog.Blog', owner=self.author)]
        mocked_featured.return_value = []
        self.assertTrue(collection.has_content())

        mocked_entities.return_value = []
        mocked_featured.return_value = [create_article('blog.Blog', owner=self.author)]
        self.assertTrue(collection.has_content())

        mocked_entities.return_value = [create_article('blog.Blog', owner=self.author)]
        mocked_featured.return_value = [create_article('blog.Blog', owner=self.author)]
        self.assertTrue(collection.has_content())

    @override_local_config(EMAIL_OVERVIEW_ENABLE_FEATURED=True)
    def test_with_featured(self):
        f1 = create_article("blog.Blog", owner=self.author, title="Featured1", is_featured=True)
        f2 = create_article("blog.Blog", owner=self.author, title="Featured2", is_featured=True)
        e1 = create_article("blog.Blog", owner=self.author, title="Entity1", is_featured=False)
        e2 = create_article("blog.Blog", owner=self.author, title="Entity2", is_featured=False)
        collection = self.build_collection()

        featured = collection.get_featured()
        entities = collection.get_entities()

        # Featured result ok?
        self.assertIn(f1, featured)
        self.assertIn(f2, featured)
        self.assertNotIn(e1, featured)
        self.assertNotIn(e2, featured)

        # Entities result ok?
        self.assertIn(e1, entities)
        self.assertIn(e2, entities)
        self.assertNotIn(f1, entities)
        self.assertNotIn(f2, entities)

    @override_local_config(EMAIL_OVERVIEW_ENABLE_FEATURED=True)
    def test_featured_limited_number_of_entities(self):
        create_article("blog.Blog", owner=self.author, title="Featured1", is_featured=True)
        create_article("blog.Blog", owner=self.author, title="Featured2", is_featured=True)
        create_article("blog.Blog", owner=self.author, title="Featured3", is_featured=True)
        create_article("blog.Blog", owner=self.author, title="Entity1")
        create_article("blog.Blog", owner=self.author, title="Entity2")
        create_article("blog.Blog", owner=self.author, title="Entity3")
        create_article("blog.Blog", owner=self.author, title="Entity4")
        create_article("blog.Blog", owner=self.author, title="Entity5")

        collection = self.build_collection()

        # Number of items ok?
        self.assertEqual(3, collection.MAX_FEATURED)
        self.assertEqual(5, collection.MAX_ENTITIES)

        # Number of items collected ok?
        self.assertEqual(3, len(collection.get_featured()))
        self.assertEqual(5, len(collection.get_entities()))

        # Will read from MAX constants?
        collection = self.build_collection()
        collection.MAX_ENTITIES = 2
        collection.MAX_FEATURED = 2
        self.assertEqual(2, len(collection.get_featured()))
        self.assertEqual(2, len(collection.get_entities()))

    @override_local_config(EMAIL_OVERVIEW_ENABLE_FEATURED=False)
    def test_without_featured(self):
        # Given
        f1 = create_article("blog.Blog", owner=self.author, title="Featured1", is_featured=True)
        f2 = create_article("blog.Blog", owner=self.author, title="Featured2", is_featured=True)
        e1 = create_article("blog.Blog", owner=self.author, title="Entity1", is_featured=False)
        e2 = create_article("blog.Blog", owner=self.author, title="Entity2", is_featured=False)
        collection = self.build_collection()

        # When
        featured = collection.get_featured()
        entities = collection.get_entities()

        # Then
        self.assertEqual(0, len(featured))
        self.assertIn(f1, entities)
        self.assertIn(f2, entities)
        self.assertIn(e1, entities)
        self.assertIn(e2, entities)

    def test_with_tags(self):
        # Given.
        e1 = create_article("blog.Blog", owner=self.author, title="Entity1")
        e2 = create_article("blog.Blog", owner=self.author, title="Entity2",
                            published=self.LAST_WEEK,
                            tags=["Test"])
        e3 = create_article("blog.Blog", owner=self.author, title="Entity3",
                            published=self.LAST_WEEK,
                            tags=["Other test"])
        self.user.profile.overview_email_tags = ['Test']
        self.user.profile.save()
        collection = self.build_collection()

        # When.
        entities = collection.get_entities()

        # Then should start with tagged content
        self.assertEqual(e2, entities[0])

        # Followed by the other expected content, regardless of the order of the other content.
        self.assertEqual(3, len(entities))
        self.assertIn(e1, entities)
        self.assertIn(e2, entities)
        self.assertIn(e3, entities)

    def test_with_viewed_content(self):
        # Given.
        e1 = create_article("blog.Blog", owner=self.author, title="Entity1")
        e2 = create_article("blog.Blog", owner=self.author, title="Entity2")
        self.user.viewed_entities.create(entity=e2)
        collection = self.build_collection()

        # When.
        entities = collection.get_entities()

        # Then: should give all but viewed content.
        self.assertIn(e1, entities)
        self.assertNotIn(e2, entities)

    def test_content_types(self):
        # Given.
        valid_entities = [
            create_article("event.Event", owner=self.author, title="Content of type [event.Event]"),
            create_article("blog.Blog", owner=self.author, title="Content of type [blog.Blog]"),
            create_article("news.News", owner=self.author, title="Content of type [news.News]"),
            create_article("question.Question", owner=self.author, title="Content of type [question.Question]"),
            create_article("wiki.Wiki", owner=self.author, title="Content of type [wiki.Wiki]"),
        ]
        invalid_entities = [
            create_article("activity.StatusUpdate", owner=self.author, title="Content of type [activity.StatusUpdate]"),
            create_article("cms.Page", owner=self.author, title="Content of type [cms.Page]"),
            create_article("discussion.Discussion", owner=self.author, title="Content of type [discussion.Discussion]"),
            create_article("file.FileFolder", owner=self.author, title="Content of type [file.FileFolder]"),
            create_article("poll.Poll", owner=self.author, title="Content of type [poll.Poll]"),
            create_article("task.Task", owner=self.author, title="Content of type [task.Task]"),
        ]
        collection = self.build_collection()
        collection.MAX_ENTITIES = len(valid_entities) + len(invalid_entities)

        # When.
        entities = collection.get_entities()

        # Then valid types are found in the result.
        for valid in valid_entities:
            self.assertIn(valid, entities, msg="%s not found in result." % valid.title)

        # And invalid types are excluded from the result.
        for invalid in invalid_entities:
            self.assertNotIn(invalid, entities, msg="%s unexpectedly found in result." % invalid.title)

    def test_ordered_by_published_date(self):
        # Given.
        a_yesterday = create_article("blog.Blog", owner=self.author, title="Yesterday", published=self.YESTERDAY)
        a_lastweek = create_article("blog.Blog", owner=self.author, title="Last week", published=self.LAST_WEEK)
        a_today = create_article("blog.Blog", owner=self.author, title="This day", published=self.TODAY)
        collection = self.build_collection()
        # allow all created content to be in the result.
        collection.MAX_ENTITIES = 3

        # When
        entities = collection.get_entities()

        # Then the result should be content in published order, recent on top
        self.assertEqual([a_today, a_yesterday, a_lastweek], entities)

    def test_exclude_outside_of_interval(self):
        # Given.
        yesterday = create_article("blog.Blog", owner=self.author, title="Yesterday", published=self.YESTERDAY)
        last_month = create_article("blog.Blog", owner=self.author, title="Last month", published=self.LAST_MONTH)
        previous_month = create_article("blog.Blog", owner=self.author, title="Previous month", published=self.PREVIOUS_MONTH)
        not_published = create_article("blog.Blog", owner=self.author, title="Not published", published=None)
        collection = self.build_collection()
        # allow all created content to be in the result. (not to mention 'expected')
        collection.MAX_ENTITIES = 3

        # When
        entities = collection.get_entities()

        # Then the result consists of articles inside interval.
        self.assertIn(yesterday, entities)

        # Not outside interval, or not-published
        self.assertNotIn(last_month, entities)
        self.assertNotIn(previous_month, entities)
        self.assertNotIn(not_published, entities)
