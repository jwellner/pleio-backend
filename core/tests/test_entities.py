from datetime import timedelta
from core.models import Group
from core.tests.helpers import PleioTenantTestCase
from user.factories import UserFactory
from user.models import User
from blog.models import Blog
from cms.models import Page
from event.models import Event
from news.models import News
from core.constances import ACCESS_TYPE, COULD_NOT_ORDER_BY_START_DATE, COULD_NOT_USE_EVENT_FILTER
from django.contrib.auth.models import AnonymousUser
from mixer.backend.django import mixer
from django.utils import timezone


class EntitiesTestCase(PleioTenantTestCase):

    def setUp(self):
        super().setUp()

        self.user: User = mixer.blend(User)
        self.user2: User = mixer.blend(User)
        self.admin: User = mixer.blend(User, roles=['ADMIN'])
        self.group: Group = mixer.blend(Group, owner=self.user)

        self.blog1: Blog = Blog.objects.create(
            title="Blog1",
            owner=self.user,
            read_access=[ACCESS_TYPE.public],
            write_access=[ACCESS_TYPE.user.format(self.user.id)]
        )

        self.blog2: Blog = Blog.objects.create(
            title="Blog2",
            owner=self.user,
            read_access=[ACCESS_TYPE.public],
            write_access=[ACCESS_TYPE.user.format(self.user.id)],
            tags=["tag_one", "tag_four"]
        )

        self.blog3: Blog = Blog.objects.create(
            title="Blog3",
            owner=self.user,
            read_access=[ACCESS_TYPE.public],
            write_access=[ACCESS_TYPE.user.format(self.user.id)],
            group=self.group,
            tags=["tag_two", "tag_one", "tag_four"]
        )

        self.blog4: Blog = Blog.objects.create(
            title="Blog4",
            owner=self.user,
            read_access=[ACCESS_TYPE.public],
            write_access=[ACCESS_TYPE.user.format(self.user.id)],
            group=self.group,
            tags=["tag_four", "tag_three", "tag_one_extra"],
            is_featured=True
        )

        self.news1: News = News.objects.create(
            title="News1",
            owner=self.user,
            read_access=[ACCESS_TYPE.public],
            write_access=[ACCESS_TYPE.user.format(self.user.id)],
            is_featured=True
        )
        self.page1: Page = mixer.blend(
            Page,
            title="Page1",
            owner=self.admin,
            read_access=[ACCESS_TYPE.public],
            write_access=[ACCESS_TYPE.user.format(self.admin.id)]
        )
        self.page2: Page = mixer.blend(
            Page,
            title="Page2",
            position=0,
            owner=self.admin,
            read_access=[ACCESS_TYPE.public],
            write_access=[ACCESS_TYPE.user.format(self.admin.id)],
            parent=self.page1
        )
        self.page3: Page = mixer.blend(
            Page,
            title="Page3",
            is_pinned=True,
            position=1,
            parent=self.page1,
            owner=self.admin,
            read_access=[ACCESS_TYPE.public],
            write_access=[ACCESS_TYPE.user.format(self.admin.id)]
        )

        self.blog_draft1: Blog = Blog.objects.create(
            title="Blog draft1",
            owner=self.user,
            read_access=[ACCESS_TYPE.public],
            write_access=[ACCESS_TYPE.user.format(self.user.id)],
            group=self.group,
            is_featured=True,
            published=None,
            tags=["tag_four", "tag_three"]
        )

        self.blog_draft2: Blog = Blog.objects.create(
            title="Blog draft2",
            owner=self.user2,
            read_access=[ACCESS_TYPE.public],
            write_access=[ACCESS_TYPE.user.format(self.user.id)],
            group=self.group,
            is_featured=True,
            published=timezone.now() + timedelta(days=5),
            tags=["tag_four", "tag_three"]
        )

        self.archived1: Blog = Blog.objects.create(
            title="Archived 1",
            owner=self.user,
            read_access=[ACCESS_TYPE.public],
            group=self.group,
            is_archived=True,
            published=timezone.now() - timezone.timedelta(days=1)
        )
        self.archived2: Blog = Blog.objects.create(
            title="Archived 2",
            owner=self.user2,
            read_access=[ACCESS_TYPE.public],
            group=self.group,
            is_archived=True,
            published=timezone.now() - timezone.timedelta(days=1)
        )

        self.query = """
            query getEntities(
                    $subtype: String
                    $containerGuid: String
                    $tags: [String!]
                    $matchStrategy: MatchStrategy
                    $tagLists: [[String]]
                    $isFeatured: Boolean
                    $limit: Int
                    $offset: Int
                    $orderBy: OrderBy
                    $orderDirection: OrderDirection
                    $statusPublished: [StatusPublished]
                    $userGuid: String) {
                entities(
                        subtype: $subtype
                        containerGuid: $containerGuid
                        tags: $tags
                        matchStrategy: $matchStrategy
                        tagLists: $tagLists
                        isFeatured: $isFeatured
                        limit: $limit
                        offset: $offset
                        orderBy: $orderBy
                        orderDirection: $orderDirection
                        statusPublished: $statusPublished
                        userGuid: $userGuid) {
                    total
                    edges {
                        guid
                        ...BlogListFragment
                        ...PageListFragment
                        ...NewsListFragment
                        ...EventListFragment
                        __typename
                    }
                }
            }
            fragment BlogListFragment on Blog {
                title
            }
            fragment PageListFragment on Page {
                title
            }
            fragment NewsListFragment on News {
                title
            }
            fragment EventListFragment on Event {
                title
            }
        """

    def tearDown(self):
        self.page1.delete()
        self.page2.delete()
        self.page3.delete()
        self.blog1.delete()
        self.blog2.delete()
        self.blog3.delete()
        self.group.delete()
        self.admin.delete()
        self.user.delete()
        self.user2.delete()

    def test_entities_all(self):
        variables = {
            "containerGuid": None
        }

        self.graphql_client.force_login(self.user)
        result = self.graphql_client.post(self.query, variables)

        data = result["data"]["entities"]
        self.assertEqual(data["total"], 8)

    def test_entities_site(self):
        variables = {
            "containerGuid": "1"
        }
        self.graphql_client.force_login(self.user)
        result = self.graphql_client.post(self.query, variables)

        data = result.get("data")
        self.assertIsNotNone(data, msg=result)
        self.assertIsNotNone(data.get('entities'), msg=result)
        self.assertEqual(data["entities"]["total"], 6)

    def test_tags_match_all(self):
        result = self.graphql_client.post(self.query, {
            'tags': ["tag_one", "tag_two"]
        })
        blogs = [e['title'] for e in result['data']['entities']['edges']]
        self.assertEqual(1, len(blogs))
        self.assertIn(self.blog3.title, blogs)

    def test_tags_match_any(self):
        result = self.graphql_client.post(self.query, {
            'tags': ["tag_one", "tag_two"],
            'matchStrategy': 'any',
        })
        blogs = [e['title'] for e in result['data']['entities']['edges']]
        self.assertEqual(2, len(blogs))
        self.assertIn(self.blog2.title, blogs)
        self.assertIn(self.blog3.title, blogs)

    def test_entities_group(self):
        variables = {
            "containerGuid": self.group.guid
        }

        self.graphql_client.force_login(self.user)
        result = self.graphql_client.post(self.query, variables)

        data = result["data"]
        self.assertEqual(data["entities"]["total"], 2)

    def test_entities_filtered_by_tags_find_one(self):
        variables = {"tags": ["tag_two"]}

        self.graphql_client.force_login(self.user)
        result = self.graphql_client.post(self.query, variables)

        data = result["data"]
        self.assertEqual(data["entities"]["total"], 1)
        self.assertEqual(data["entities"]["edges"][0]["guid"], self.blog3.guid)

    def test_entities_filtered_by_tags_find_two(self):
        variables = {"tags": ["tag_one"]}

        self.graphql_client.force_login(self.user)
        result = self.graphql_client.post(self.query, variables)

        data = result["data"]
        self.assertEqual(data["entities"]["total"], 2)
        self.assertEqual(data["entities"]["edges"][0]["guid"], self.blog3.guid)
        self.assertEqual(data["entities"]["edges"][1]["guid"], self.blog2.guid)

    def test_entities_filtered_by_tags_find_one_with_two_tags(self):
        variables = {"tags": ["tag_one", "tag_two"]}

        self.graphql_client.force_login(self.user)
        result = self.graphql_client.post(self.query, variables)

        data = result.get("data")
        self.assertEqual(data["entities"]["total"], 1, msg=[edge['title'] for edge in data["entities"]["edges"]])
        self.assertEqual(data["entities"]["edges"][0]["guid"], self.blog3.guid)

    def test_entities_all_pages_by_admin(self):
        variables = {
            "subtype": "page"
        }

        self.graphql_client.force_login(self.admin)
        result = self.graphql_client.post(self.query, variables)

        data = result["data"]
        self.assertEqual(data["entities"]["total"], 1)

    def test_entities_filtered_by_tag_lists(self):
        variables = {"tagLists": [["tag_four", "tag_three"], ["tag_one"]]}

        self.graphql_client.force_login(self.user)
        result = self.graphql_client.post(self.query, variables)

        data = result.get("data")
        status_message = "Query resutl: %s" % [d['title'] for d in data["entities"]['edges']]
        self.assertEqual(data["entities"]["total"], 2, msg=status_message)

    def test_entities_filtered_is_featured(self):
        variables = {"isFeatured": True}

        self.graphql_client.force_login(self.user)
        result = self.graphql_client.post(self.query, variables)

        data = result["data"]
        self.assertEqual(data["entities"]["total"], 2)

    def test_entities_single_filtered_is_featured(self):
        variables = {"isFeatured": True, "subtype": "blog"}

        self.graphql_client.force_login(self.user)
        result = self.graphql_client.post(self.query, variables)

        data = result["data"]
        self.assertEqual(data["entities"]["total"], 1)

    def test_entities_multiple_filtered_is_featured(self):
        variables = {"isFeatured": True, "subtypes": ["blog", "news"]}

        self.graphql_client.force_login(self.user)
        result = self.graphql_client.post(self.query, variables)

        data = result["data"]
        self.assertEqual(data["entities"]["total"], 2)

    def test_entities_limit(self):
        variables = {"limit": 5}

        self.graphql_client.force_login(self.user)
        result = self.graphql_client.post(self.query, variables)

        data = result["data"]
        self.assertEqual(len(data["entities"]["edges"]), 5)
        self.assertEqual(data["entities"]["total"], 8)

    def test_entities_all_order_by_title_asc(self):
        variables = {
            "containerGuid": None,
            "orderBy": "title",
            "orderDirection": "asc"
        }

        self.graphql_client.force_login(self.user)
        result = self.graphql_client.post(self.query, variables)

        titles = [e['title'] for e in result['data']['entities']['edges']]
        self.assertEqual([self.blog1.title,
                          self.blog2.title,
                          self.blog3.title,
                          self.blog4.title,
                          self.news1.title,
                          self.page1.title,
                          self.page2.title,
                          self.page3.title], titles)

    def test_entities_blogs_order_by_title_desc(self):
        variables = {
            "containerGuid": None,
            "orderBy": "title",
            "orderDirection": "desc",
            "subtype": "blog"
        }

        self.graphql_client.force_login(self.user)
        result = self.graphql_client.post(self.query, variables)

        titles = [e['title'] for e in result['data']['entities']['edges']]
        self.assertEqual([self.blog4.title,
                          self.blog3.title,
                          self.blog2.title,
                          self.blog1.title], titles)

    def test_entities_show_pinned(self):
        variables = {
            "containerGuid": None,
            "showPinned": True
        }

        self.graphql_client.force_login(self.user)
        result = self.graphql_client.post(self.query, variables)

        data = result["data"]
        self.assertEqual(data["entities"]["edges"][0]["guid"], self.page3.guid)

    def test_entities_all_draft(self):
        variables = {
            "containerGuid": None,
            "statusPublished": 'draft'
        }

        self.graphql_client.force_login(self.user)
        result = self.graphql_client.post(self.query, variables)

        data = result["data"]
        self.assertEqual(data["entities"]["total"], 1)

    def test_entities_all_draft_admin(self):
        variables = {
            "containerGuid": None,
            "statusPublished": 'draft'
        }

        self.graphql_client.force_login(self.admin)
        result = self.graphql_client.post(self.query, variables)

        data = result["data"]
        self.assertIsNotNone(data, msg=result)
        self.assertIsNotNone(data.get('entities'), msg=result)

        self.assertEqual(data["entities"]["total"], 2)

    def test_entities_all_draft_anon(self):
        variables = {
            "containerGuid": None,
            "statusPublished": 'draft'
        }

        result = self.graphql_client.post(self.query, variables)

        data = result.get("data")
        self.assertIsNotNone(data, msg=result)
        self.assertIsNotNone(data.get('entities'), msg=result)
        self.assertEqual(data["entities"]["total"], 0)

    def test_entities_all_draft_other(self):
        variables = {
            "containerGuid": None,
            "statusPublished": ['draft']
        }

        self.graphql_client.force_login(self.user2)
        result = self.graphql_client.post(self.query, variables)

        data = result["data"]
        self.assertIsNotNone(data, msg=result)
        self.assertIsNotNone(data.get('entities'), msg=result)

        result_guids = {e["guid"] for e in data['entities']['edges']}
        result_msg = "Result is %s" % [e["title"] for e in data['entities']['edges']]
        self.assertEqual(data["entities"]["total"], 1, msg=result_msg)
        self.assertNotIn(self.blog_draft1.guid, result_guids, msg=result_msg)
        self.assertIn(self.blog_draft2.guid, result_guids, msg=result_msg)

    def test_entities_all_for_user(self):
        variables = {
            "containerGuid": None,
            "userGuid": self.user.guid
        }

        self.graphql_client.force_login(self.user)
        result = self.graphql_client.post(self.query, variables)

        data = result["data"]
        result_guids = {e["guid"] for e in data['entities']['edges']}
        result_msg = "Result is %s" % [e["title"] for e in data['entities']['edges']]
        self.assertEqual(data["entities"]["total"], 5)
        self.assertIn(self.blog1.guid, result_guids, msg=result_msg)
        self.assertIn(self.blog2.guid, result_guids, msg=result_msg)
        self.assertIn(self.blog3.guid, result_guids, msg=result_msg)
        self.assertIn(self.blog4.guid, result_guids, msg=result_msg)
        self.assertIn(self.news1.guid, result_guids, msg=result_msg)

    def test_entities_archived_filter(self):
        for while_testing_with_user, user in [("while testing admin", self.admin),
                                              ("while testing anonymous user", AnonymousUser()),
                                              ("while testing authenticated user", self.user)]:
            variables = {
                "containerGuid": None,
                "statusPublished": 'archived',
            }

            self.graphql_client.force_login(user)
            result = self.graphql_client.post(self.query, variables)

            self.assertIsNotNone(result, msg="No result %s" % while_testing_with_user)
            self.assertIsNotNone(result.get('data'), msg="Data is empty %s" % while_testing_with_user)

            data = result.get("data")
            self.assertEqual(data["entities"]["total"], 2,
                             msg="Unexpected number of results %s" % while_testing_with_user)
            result_guids = {e["guid"] for e in data['entities']['edges']}
            self.assertIn(self.archived1.guid, result_guids)
            self.assertIn(self.archived2.guid, result_guids)

    def test_enities_filter_my_draft_archived_articles(self):
        variables = {
            "containerGuid": None,
            "userGuid": self.user.guid,
            "statusPublished": ['archived', 'draft'],
        }

        self.graphql_client.force_login(self.user)
        result = self.graphql_client.post(self.query, variables)

        data = result["data"]
        self.assertEqual(data["entities"]["total"], 2)
        result_guids = {e["guid"] for e in data['entities']['edges']}
        self.assertIn(self.blog_draft1.guid, result_guids)
        self.assertIn(self.archived1.guid, result_guids)

    def test_entities_all_for_admin_by_user(self):
        variables = {
            "containerGuid": None,
            "userGuid": self.admin.guid
        }

        self.graphql_client.force_login(self.user)
        result = self.graphql_client.post(self.query, variables)

        data = result["data"]
        self.assertEqual(data["entities"]["total"], 3)

    def test_entities_all_for_admin(self):
        variables = {
            "containerGuid": None,
            "userGuid": self.admin.guid
        }

        self.graphql_client.force_login(self.admin)
        result = self.graphql_client.post(self.query, variables)

        data = result["data"]
        self.assertEqual(data["entities"]["total"], 3)

    def test_blog_draft_owner(self):
        query = """
            fragment BlogParts on Blog {
                title
            }
            query GetBlog($guid: String!) {
                entity(guid: $guid) {
                    guid
                    status
                    ...BlogParts
                }
            }
        """

        variables = {
            "guid": self.blog_draft1.guid
        }

        self.graphql_client.force_login(self.user)
        result = self.graphql_client.post(query, variables)

        data = result.get("data")
        self.assertIsNotNone(data, msg=result)
        self.assertIsNotNone(data.get('entity'), msg=result)

        self.assertEqual(data["entity"]["guid"], self.blog_draft1.guid)
        self.assertEqual(data["entity"]["title"], self.blog_draft1.title)

    def test_blog_draft_other(self):
        query = """
            fragment BlogParts on Blog {
                title
            }
            query GetBlog($guid: String!) {
                entity(guid: $guid) {
                    guid
                    status
                    ...BlogParts
                }
            }
        """

        variables = {
            "guid": self.blog_draft1.guid
        }

        self.graphql_client.force_login(self.user2)
        result = self.graphql_client.post(query, variables)

        data = result["data"]
        self.assertIsNone(data["entity"])

    def test_entities_no_subevents(self):
        event = Event.objects.create(
            title="Event1",
            owner=self.user,
            read_access=[ACCESS_TYPE.public],
            write_access=[ACCESS_TYPE.user.format(self.user.id)]
        )
        Event.objects.create(
            title="Subevent1",
            owner=self.user,
            read_access=[ACCESS_TYPE.public],
            write_access=[ACCESS_TYPE.user.format(self.user.id)],
            parent=event
        )

        variables = {
            "containerGuid": None,
            "orderBy": "timeCreated"
        }

        self.graphql_client.force_login(self.user)
        result = self.graphql_client.post(self.query, variables)

        data = result["data"]
        self.assertEqual(data["entities"]["edges"][0]["guid"], event.guid)


class EntitiesEventsTestCase(PleioTenantTestCase):

    def setUp(self):
        super(EntitiesEventsTestCase, self).setUp()

        self.user1 = UserFactory()
        self.user2 = UserFactory()
        self.event_in_4_days = Event.objects.create(
            owner=self.user1,
            read_access=[ACCESS_TYPE.public],
            write_access=[ACCESS_TYPE.user.format(self.user1.id)],
            start_date=timezone.now() + timezone.timedelta(days=4)
        )
        self.event_5_days_ago = Event.objects.create(
            owner=self.user1,
            read_access=[ACCESS_TYPE.public],
            write_access=[ACCESS_TYPE.user.format(self.user1.id)],
            start_date=timezone.now() - timezone.timedelta(days=5)
        )
        self.event_in_6_days = Event.objects.create(
            owner=self.user1,
            read_access=[ACCESS_TYPE.public],
            write_access=[ACCESS_TYPE.user.format(self.user1.id)],
            start_date=timezone.now() + timezone.timedelta(days=6)
        )
        self.event_3_days_ago = Event.objects.create(
            owner=self.user1,
            read_access=[ACCESS_TYPE.public],
            write_access=[ACCESS_TYPE.user.format(self.user1.id)],
            start_date=timezone.now() - timezone.timedelta(days=3)
        )

        self.query = """
            query getEntities(
                    $subtype: String
                    $containerGuid: String
                    $tags: [String!]
                    $tagLists: [[String]]
                    $isFeatured: Boolean
                    $limit: Int
                    $offset: Int
                    $subtypes: [String!]
                    $eventFilter: EventFilter
                    $orderBy: OrderBy
                    $orderDirection: OrderDirection
                    $statusPublished: [StatusPublished]
                    $userGuid: String) {
                entities(
                        subtype: $subtype
                        containerGuid: $containerGuid
                        tags: $tags
                        tagLists: $tagLists
                        isFeatured: $isFeatured
                        limit: $limit
                        offset: $offset
                        subtypes: $subtypes,
                        eventFilter: $eventFilter
                        orderBy: $orderBy
                        orderDirection: $orderDirection
                        statusPublished: $statusPublished
                        userGuid: $userGuid) {
                    total
                    edges {
                        guid
                        ...EventListFragment
                        __typename
                    }
                }
            }
            fragment EventListFragment on Event {
                title
            }
        """

    def test_entities_order_events_by_start_date_asc(self):
        variables = {
            "limit": 20,
            "offset": 0,
            "subtypes": ['event'],
            "orderBy": "startDate",
            "orderDirection": "asc"
        }

        self.graphql_client.force_login(self.user2)
        result = self.graphql_client.post(self.query, variables)

        self.assertEqual(result["data"]["entities"]["edges"][0]["guid"], self.event_5_days_ago.guid)

    def test_entities_order_events_by_start_date_desc(self):
        variables = {
            "limit": 20,
            "offset": 0,
            "subtypes": ['event'],
            "orderBy": "startDate",
            "orderDirection": "desc"
        }

        self.graphql_client.force_login(self.user2)
        result = self.graphql_client.post(self.query, variables)
        self.assertEqual(result["data"]["entities"]["edges"][0]["guid"], self.event_in_6_days.guid)

    def test_entities_order_blog_events_by_start_date_desc(self):
        variables = {
            "limit": 20,
            "offset": 0,
            "subtypes": ['event', 'blog'],
            "orderBy": "startDate",
            "orderDirection": "desc"
        }

        with self.assertGraphQlError(COULD_NOT_ORDER_BY_START_DATE):
            self.graphql_client.force_login(self.user2)
            self.graphql_client.post(self.query, variables)


    def test_entities_filter_by_upcoming(self):
        variables = {
            "limit": 20,
            "offset": 0,
            "subtypes": ['event'],
            "eventFilter": 'upcoming'
        }

        self.graphql_client.force_login(self.user2)
        result = self.graphql_client.post(self.query, variables)
        self.assertEqual(len(result["data"]["entities"]["edges"]), 2)
        self.assertEqual(result["data"]["entities"]["edges"][0]["guid"], self.event_in_6_days.guid)


    def test_entities_filter_by_previous(self):
        variables = {
            "limit": 20,
            "offset": 0,
            "subtypes": ['event'],
            "eventFilter": 'previous'
        }

        self.graphql_client.force_login(self.user2)
        result = self.graphql_client.post(self.query, variables)
        self.assertEqual(len(result["data"]["entities"]["edges"]), 2)
        self.assertEqual(result["data"]["entities"]["edges"][0]["guid"], self.event_3_days_ago.guid)


    def test_entities_blog_event_filter_by_previous(self):
        variables = {
            "limit": 20,
            "offset": 0,
            "subtypes": ['event', 'blog'],
            "eventFilter": 'previous'
        }

        with self.assertGraphQlError(COULD_NOT_USE_EVENT_FILTER):
            self.graphql_client.force_login(self.user2)
            self.graphql_client.post(self.query, variables)
