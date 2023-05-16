from unittest import mock

from django.contrib.auth.models import AnonymousUser
from django.core.exceptions import ValidationError

from core.models import Entity
from core.tests.helpers import PleioTenantTestCase, override_config
from external_content.api_handlers.default import ApiHandler as DefaultHandler
from external_content.factories import ExternalContentFactory, ExternalContentSourceFactory
from external_content.models import ExternalContent, ExternalContentSource
from external_content.utils import get_or_create_default_author
from user.factories import UserFactory


class TestCleanExternalContentSourceTestCase(PleioTenantTestCase):

    def setUp(self):
        super().setUp()
        self.source = ExternalContentSource.objects.create(name="Demo",
                                                           handler_id=DefaultHandler.ID)

    def tearDown(self):
        super().tearDown()

    @mock.patch("external_content.api_handlers.default.ApiHandler.pull")
    def test_pull_method(self, mocked_pull):
        self.source.pull()
        self.assertTrue(mocked_pull.called)


class TestCleanExternalContentTestCase(PleioTenantTestCase):

    def setUp(self):
        super().setUp()
        self.default_owner = get_or_create_default_author()
        self.owner = UserFactory()
        self.other_user = UserFactory()
        self.source = ExternalContentSource.objects.create(name="Demo",
                                                           handler_id=DefaultHandler.ID)
        self.required_params = {
            "source": self.source,
            "title": "Demo",
            "remote_id": "1",
            "canonical_url": "https://www.pleio.nl",
            "owner": self.owner,
        }

    def tearDown(self):
        super().tearDown()

    def test_required_params_complete(self):
        ExternalContent.objects.create(**self.required_params)

    def test_required_params_are_mandatory(self):
        for key, value in self.required_params.items():
            params = {**self.required_params}
            params.pop(key)
            try:
                ExternalContent.objects.create(**params)
                self.fail("Expected %s to be mandatory" % key)  # pragma: no cover
            except (ValidationError,
                    Entity.owner.RelatedObjectDoesNotExist):
                pass

    @override_config(IS_CLOSED=True)
    def test_access_on_closed_site(self):
        article = ExternalContent.objects.create(**self.required_params)

        self.assertFalse(article.can_read(AnonymousUser()))
        self.assertTrue(article.can_read(self.owner))
        self.assertTrue(article.can_read(self.other_user))

    @override_config(IS_CLOSED=False)
    def test_access_on_public_site(self):
        article = ExternalContent.objects.create(**self.required_params)

        self.assertTrue(article.can_read(AnonymousUser()))
        self.assertTrue(article.can_read(self.owner))
        self.assertTrue(article.can_read(self.other_user))

    def test_factory_works(self):
        with self.assertRaisesRegex(AssertionError, 'Source is mandatory.*'):
            ExternalContentFactory()

        content = ExternalContentFactory(source=self.source)
        self.assertEqual(content.owner, self.default_owner)

        content = ExternalContentFactory(source=self.source,
                                         owner=self.owner)
        self.assertEqual(content.owner, self.owner)


class TestCleanExternalContentQueryTestCase(PleioTenantTestCase):
    def setUp(self):
        super().setUp()

        self.authenticated_user = UserFactory()

        self.EXPECTED_TAGS = ['Alpha', 'Beta', 'Delta']
        self.EXPECTED_TAG_CATEGORIES = [{"name": "Category", "values": ['First', 'Last']}]

        self.source = ExternalContentSourceFactory()
        self.article = ExternalContentFactory(source=self.source,
                                              tags=self.EXPECTED_TAGS,
                                              category_tags=self.EXPECTED_TAG_CATEGORIES)

        self.query = """
        query Entity($guid: String!) {
            entity(guid: $guid) {
                ... on ExternalContent {
                    guid
                    status
                    title
                    tags
                    tagCategories {
                        name
                        values
                    }
                    description
                    timeCreated
                    timeUpdated
                    timePublished
                    canEdit
                    accessId
                    writeAccessId
                    owner { guid }
                    source { key }
                    remoteId
                    url
                }
            }
        }
        """
        self.variables = {
            'guid': self.article.guid,
        }

    def tearDown(self):
        super().tearDown()

    def test_clean_content(self):
        self.graphql_client.force_login(self.authenticated_user)
        result = self.graphql_client.post(self.query, self.variables)

        self.maxDiff = None
        self.assertDictEqual(result['data']['entity'], {
            "guid": self.article.guid,
            "owner": {"guid": self.article.owner.guid},
            "remoteId": self.article.remote_id,
            "source": {"key": self.source.guid},
            "status": 200,
            "tagCategories": self.EXPECTED_TAG_CATEGORIES,
            "tags": self.EXPECTED_TAGS,
            "timeCreated": self.article.created_at.isoformat(),
            "timeUpdated": self.article.updated_at.isoformat(),
            "timePublished": self.article.published.isoformat(),
            "title": self.article.title,
            "description": self.article.description,
            "url": self.article.canonical_url,
            "accessId": 1,
            "canEdit": False,
            "writeAccessId": 0,
        })
