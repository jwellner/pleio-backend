from django.utils import timezone
from django.test import override_settings
from mixer.backend.django import mixer

from blog.factories import BlogFactory
from blog.models import Blog
from core.constances import ACCESS_TYPE
from core.models import Group
from core.tests.helpers import ElasticsearchTestCase, override_config
from file.models import FileFolder
from news.models import News
from user.factories import UserFactory
from wiki.models import Wiki


class SearchTestCase(ElasticsearchTestCase):

    @override_config(COLLAB_EDITING_ENABLED=True)
    @override_settings(ENV='test')
    def setUp(self):
        super().setUp()

        self.common_tag1 = "Alles moet weg"
        self.common_tag2 = "Niets blijft staan"
        self.q = "Alles"

        self.group = mixer.blend(Group)
        self.user = UserFactory()
        self.user2 = UserFactory()

        self.query = """
            query Search(
                        $q: String!
                        $subtype: String
                        $subtypes: [String]
                        $filterArchived: Boolean) {
                search( 
                        q: $q,
                        subtype: $subtype
                        subtypes: $subtypes
                        filterArchived: $filterArchived) {
                    edges {
                        guid
                    }
                    total
                    totals {
                        subtype
                        total
                    }
                }
            }
        """

        permission = {
            'owner': self.user,
            'read_access': [ACCESS_TYPE.public],
            'write_access': [ACCESS_TYPE.user.format(self.user.guid)],
        }

        with override_settings(ENV='test'):
            self.pad = FileFolder.objects.create(
                type=FileFolder.Types.PAD,
                title="Test group pad",
                rich_description="padtest",
                read_access=[ACCESS_TYPE.public],
                write_access=[ACCESS_TYPE.user.format(self.user.id)],
                owner=self.user,
                group=self.group
            )
        permission2 = {
            'owner': self.user2,
            'read_access': [ACCESS_TYPE.public],
            'write_access': [ACCESS_TYPE.user.format(self.user2.guid)],
        }

        self.blog1 = mixer.blend(Blog, title=self.common_tag1, **permission)
        self.blog2 = mixer.blend(Blog, title=self.common_tag2, **permission)
        self.wiki1 = mixer.blend(Wiki, title=self.common_tag1, **permission)
        self.wiki2 = mixer.blend(Wiki, title=self.common_tag2, **permission)
        self.news1 = mixer.blend(News, title=self.common_tag1, **permission)
        self.news2 = mixer.blend(News, title=self.common_tag2, **permission)
        self.news3 = mixer.blend(News, title=self.common_tag2, **permission2)

    def tearDown(self):
        super().tearDown()

    def test_invalid_subtype(self):
        with self.assertGraphQlError("invalid_subtype"):
            self.graphql_client.force_login(self.user)
            self.graphql_client.post(self.query, {
                "q": "",
                "subtype": "test"
            })

        with self.assertGraphQlError("invalid_subtype"):
            self.graphql_client.force_login(self.user)
            self.graphql_client.post(self.query, {
                "q": "",
                "subtypes": ["test"]
            })

    @override_config(COLLAB_EDITING_ENABLED=True)
    def test_multiple_subtypes(self):
        variables = {
            "q": self.q,
            "subtypes": ["blog", "wiki", "pad"],
            "subtype": "blog"
        }

        self.initialize_index()

        self.graphql_client.force_login(self.user)
        result = self.graphql_client.post(self.query, variables)

        data = result['data']['search']
        items = [i['guid'] for i in data['edges']]

        self.assertEqual(2, data['total'])
        self.assertEqual(1, len(items))
        self.assertIn(self.blog1.guid, items)
        self.assertNotIn(self.wiki1.guid, items)
        self.assertNotIn(self.news1.guid, items)

    def test_invalid_date(self):
        query = """
            query Search(
                        $q: String!,
                        $dateFrom: String,
                        $dateTo: String) {
                search( 
                        q: $q,
                        dateFrom: $dateFrom,
                        dateTo: $dateTo) {
                    edges {
                        guid
                    }
                }
            }
        """

        variables = {
            "q": "",
            "dateFrom": "2016-33-03T19:00:00",
            "dateTo": "2016-44-03T19:00:00"
        }

        with self.assertGraphQlError("invalid_date"):
            self.graphql_client.post(query, variables)

    @override_config(COLLAB_EDITING_ENABLED=True)
    def test_pad_search(self):
        variables = {
            "q": "padtest",
            "subtype": "pad"
        }

        self.initialize_index()

        self.graphql_client.force_login(self.user)
        result = self.graphql_client.post(self.query, variables)

        data = result['data']['search']
        self.assertEqual(1, data['total'])

        self.assertEqual(self.pad.guid, data["edges"][0]["guid"])

    def test_owner_guids(self):
        query = """
            query Search(
                        $ownerGuids: [String]
                        ) {
                search( 
                        ownerGuids: $ownerGuids
                        ) {
                    edges {
                        guid
                    }
                    total
                    totals {
                        subtype
                        total
                    }
                }
            }
        """

        variables = {
            "ownerGuids": [str(self.user2.id)]
        }

        self.initialize_index()

        self.graphql_client.force_login(self.user)
        result = self.graphql_client.post(query, variables)

        data = result['data']['search']
        items = [i['guid'] for i in data['edges']]

        self.assertEqual(1, data['total'])
        self.assertEqual(1, len(items))
        self.assertIn(self.news3.guid, items)
        self.assertNotIn(self.news1.guid, items)
        self.assertNotIn(self.blog1.guid, items)


class TestSearchArchivedTestCase(ElasticsearchTestCase):

    def setUp(self):
        super().setUp()
        self.user = UserFactory()
        self.archived_blog = BlogFactory(owner=self.user,
                                         is_archived=True,
                                         published=timezone.localtime())
        self.not_archived_blog = BlogFactory(owner=self.user,
                                             is_archived=False,
                                             published=timezone.localtime())

        self.query = """
        query Search($q: String! $enabled: Boolean, $disabled: Boolean) {
                onlyArchived: search(q: $q, filterArchived: $enabled) {
                    edges {
                        guid
                    }
                }
                allContent: search(q: $q, filterArchived: $disabled) {
                    edges {
                        guid
                    }
                }
            }
        """
        self.variables = {
            'q': '',
            'enabled': True,
            'disabled': False
        }

    def test_filter_archived(self):

        self.initialize_index()

        self.graphql_client.force_login(self.user)
        result = self.graphql_client.post(self.query, self.variables)

        only_archived = [e['guid'] for e in result['data']['onlyArchived']['edges']]
        all_content = [e['guid'] for e in result['data']['allContent']['edges']]

        self.assertIn(self.archived_blog.guid, only_archived)
        self.assertNotIn(self.archived_blog.guid, all_content)

        self.assertNotIn(self.not_archived_blog.guid, only_archived)
        self.assertIn(self.not_archived_blog.guid, all_content)


class TestCaseSensitivityTitleSortingSearchTestCase(ElasticsearchTestCase):

    def setUp(self):
        super().setUp()
        self.owner = UserFactory()
        self.lowercase = BlogFactory(owner=self.owner,
                                     title="the quick brown fox")
        self.uppercase = BlogFactory(owner=self.owner,
                                     title="The Quick Fox is brown")
        self.lowercase2 = BlogFactory(owner=self.owner,
                                      title="i'm quick but that's ok")
        self.uppercase2 = BlogFactory(owner=self.owner,
                                      title="I'm Quick if that's OK with you")
        self.uppercase3 = BlogFactory(owner=self.owner,
                                      title="That's Quick!")

        self.expected_order = sorted([self.lowercase,
                                      self.lowercase2,
                                      self.uppercase,
                                      self.uppercase2,
                                      self.uppercase3], key=lambda b: b.title.lower())

    def tearDown(self):
        super().tearDown()

    def test_search_query(self):
        query = """
            query Search($query: String!, $orderBy: SearchOrderBy) {
                search(q: $query, orderBy: $orderBy) {
                    edges {
                        guid
                        ... on Blog {
                            title
                        }
                    }
                }
            }
        """
        variables = {
            "query": '',
            "orderBy": 'title'
        }

        self.initialize_index()

        self.graphql_client.force_login(self.owner)
        response = self.graphql_client.post(query, variables)

        expected_titles = [b.title for b in self.expected_order]
        actual_titles = [edge['title'] for edge in response['data']['search']['edges']]

        self.assertEqual(expected_titles, actual_titles)

    def test_entities_query(self):
        query = """
            query Search($orderBy: OrderBy, $orderDirection: OrderDirection) {
                entities(orderBy: $orderBy, orderDirection: $orderDirection) {
                    edges {
                        guid
                        ... on Blog {
                            title
                        }
                    }
                }
            }
        """
        variables = {
            "orderBy": "title",
            "orderDirection": "asc",
        }
        self.graphql_client.force_login(self.owner)
        response = self.graphql_client.post(query, variables)

        expected_titles = [b.title for b in self.expected_order]
        actual_titles = [edge['title'] for edge in response['data']['entities']['edges']]

        self.assertEqual(expected_titles, actual_titles)
