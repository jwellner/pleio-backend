from datetime import timedelta
from django_tenants.test.cases import FastTenantTestCase
from core.models import Group
from core.tests.helpers import PleioTenantTestCase
from user.factories import UserFactory
from user.models import User
from blog.models import Blog
from cms.models import Page
from event.models import Event
from news.models import News
from core.constances import ACCESS_TYPE, COULD_NOT_ORDER_BY_START_DATE
from backend2.schema import schema
from ariadne import graphql_sync
from django.contrib.auth.models import AnonymousUser
from django.http import HttpRequest
from mixer.backend.django import mixer
from django.utils import timezone


class EntitiesTestCase(FastTenantTestCase):

    def setUp(self):
        self.anonymousUser = AnonymousUser()
        self.authenticatedUser = mixer.blend(User)
        self.user2 = mixer.blend(User)
        self.admin = mixer.blend(User, roles=['ADMIN'])
        self.group = mixer.blend(Group, owner=self.authenticatedUser)

        self.blog1 = Blog.objects.create(
            title="Blog1",
            owner=self.authenticatedUser,
            read_access=[ACCESS_TYPE.public],
            write_access=[ACCESS_TYPE.user.format(self.authenticatedUser.id)]
        )

        self.blog2 = Blog.objects.create(
            title="Blog2",
            owner=self.authenticatedUser,
            read_access=[ACCESS_TYPE.public],
            write_access=[ACCESS_TYPE.user.format(self.authenticatedUser.id)],

        )
        self.blog2.tags = ["tag_one", "tag_four"]
        self.blog2.save()

        self.blog3 = Blog.objects.create(
            title="Blog4",
            owner=self.authenticatedUser,
            read_access=[ACCESS_TYPE.public],
            write_access=[ACCESS_TYPE.user.format(self.authenticatedUser.id)],
            group=self.group,
        )
        self.blog3.tags = ["tag_two", "tag_one", "tag_four"]
        self.blog3.save()

        self.blog4 = Blog.objects.create(
            title="Blog3",
            owner=self.authenticatedUser,
            read_access=[ACCESS_TYPE.public],
            write_access=[ACCESS_TYPE.user.format(self.authenticatedUser.id)],
            group=self.group,
            is_featured=True
        )
        self.blog4.tags = ["tag_four", "tag_three", "tag_one_extra"]
        self.blog4.save()

        self.news1 = News.objects.create(
            title="News1",
            owner=self.authenticatedUser,
            read_access=[ACCESS_TYPE.public],
            write_access=[ACCESS_TYPE.user.format(self.authenticatedUser.id)],
            is_featured=True
        )
        self.page1 = mixer.blend(
            Page,
            title="Page1",
            owner=self.admin,
            read_access=[ACCESS_TYPE.public],
            write_access=[ACCESS_TYPE.user.format(self.admin.id)]
        )
        self.page2 = mixer.blend(
            Page,
            title="Page2",
            position=0,
            owner=self.admin,
            read_access=[ACCESS_TYPE.public],
            write_access=[ACCESS_TYPE.user.format(self.admin.id)],
            parent=self.page1
        )
        self.page3 = mixer.blend(
            Page,
            title="Page3",
            is_pinned=True,
            position=1,
            parent=self.page1,
            owner=self.admin,
            read_access=[ACCESS_TYPE.public],
            write_access=[ACCESS_TYPE.user.format(self.admin.id)]
        )

        self.blog_draft1 = Blog.objects.create(
            title="Blog draft1",
            owner=self.authenticatedUser,
            read_access=[ACCESS_TYPE.public],
            write_access=[ACCESS_TYPE.user.format(self.authenticatedUser.id)],
            group=self.group,
            is_featured=True,
            published=None
        )
        self.blog_draft1.tags = ["tag_four", "tag_three"]
        self.blog_draft1.save()

        self.blog_draft2 = Blog.objects.create(
            title="Blog draft2",
            owner=self.user2,
            read_access=[ACCESS_TYPE.public],
            write_access=[ACCESS_TYPE.user.format(self.authenticatedUser.id)],
            group=self.group,
            is_featured=True,
            published=timezone.now() + timedelta(days=5)
        )
        self.blog_draft2.tags = ["tag_four", "tag_three"]
        self.blog_draft2.save()

        self.archived1 = Blog.objects.create(
            title="Archived 1",
            owner=self.authenticatedUser,
            read_access=[ACCESS_TYPE.public],
            group=self.group,
            is_archived=True,
            published=timezone.now() - timezone.timedelta(days=1)
        )
        self.archived2 = Blog.objects.create(
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
        self.authenticatedUser.delete()

    def test_entities_all(self):
        request = HttpRequest()
        request.user = self.authenticatedUser

        variables = {
            "containerGuid": None
        }

        result = graphql_sync(schema, {"query": self.query, "variables": variables}, context_value={"request": request})

        self.assertTrue(result[0])

        data = result[1]["data"]

        self.assertEqual(data["entities"]["total"], 8)

    def test_entities_site(self):
        request = HttpRequest()
        request.user = self.authenticatedUser

        variables = {
            "containerGuid": "1"
        }

        success, result = graphql_sync(schema, {"query": self.query, "variables": variables},
                                       context_value={"request": request})

        self.assertTrue(success)

        data = result.get("data")
        self.assertIsNotNone(data, msg=result)
        self.assertIsNotNone(data.get('entities'), msg=result)
        self.assertEqual(data["entities"]["total"], 6)

    def test_entities_group(self):
        request = HttpRequest()
        request.user = self.authenticatedUser

        variables = {
            "containerGuid": self.group.guid
        }

        result = graphql_sync(schema, {"query": self.query, "variables": variables}, context_value={"request": request})

        self.assertTrue(result[0])

        data = result[1]["data"]

        self.assertEqual(data["entities"]["total"], 2)

    def test_entities_filtered_by_tags_find_one(self):
        request = HttpRequest()
        request.user = self.authenticatedUser

        variables = {"tags": ["tag_two"]}

        result = graphql_sync(schema, {"query": self.query, "variables": variables}, context_value={"request": request})

        self.assertTrue(result[0])

        data = result[1]["data"]

        self.assertEqual(data["entities"]["total"], 1)
        self.assertEqual(data["entities"]["edges"][0]["guid"], self.blog3.guid)

    def test_entities_filtered_by_tags_find_two(self):
        request = HttpRequest()
        request.user = self.authenticatedUser

        variables = {"tags": ["tag_one"]}

        result = graphql_sync(schema, {"query": self.query, "variables": variables}, context_value={"request": request})

        self.assertTrue(result[0])

        data = result[1]["data"]

        self.assertEqual(data["entities"]["total"], 2)
        self.assertEqual(data["entities"]["edges"][0]["guid"], self.blog3.guid)
        self.assertEqual(data["entities"]["edges"][1]["guid"], self.blog2.guid)

    def test_entities_filtered_by_tags_find_one_with_two_tags(self):
        request = HttpRequest()
        request.user = self.authenticatedUser

        variables = {"tags": ["tag_one", "tag_two"]}

        success, result = graphql_sync(schema, {"query": self.query, "variables": variables}, context_value={"request": request})

        self.assertIsNone(result.get('errors'), msg=result.get('errors'))

        data = result.get("data")
        self.assertEqual(data["entities"]["total"], 1, msg=[edge['title'] for edge in data["entities"]["edges"]])
        self.assertEqual(data["entities"]["edges"][0]["guid"], self.blog3.guid)

    def test_entities_all_pages_by_admin(self):
        request = HttpRequest()
        request.user = self.admin

        variables = {
            "subtype": "page"
        }

        result = graphql_sync(schema, {"query": self.query, "variables": variables}, context_value={"request": request})

        self.assertTrue(result[0])

        data = result[1]["data"]

        self.assertEqual(data["entities"]["total"], 1)

    def test_entities_filtered_by_tag_lists(self):
        request = HttpRequest()
        request.user = self.authenticatedUser

        variables = {"tagLists": [["tag_four", "tag_three"], ["tag_one"]]}

        success, result = graphql_sync(schema, {"query": self.query, "variables": variables},
                                       context_value={"request": request})

        self.assertIsNone(result.get('errors'), msg=[result.get('errors'), self.query])

        data = result.get("data")
        status_message = "Query resutl: %s" % [d['title'] for d in data["entities"]['edges']]
        self.assertEqual(data["entities"]["total"], 2, msg=status_message)

    def test_entities_filtered_is_featured(self):
        request = HttpRequest()
        request.user = self.authenticatedUser

        variables = {"isFeatured": True}

        result = graphql_sync(schema, {"query": self.query, "variables": variables}, context_value={"request": request})

        self.assertTrue(result[0])

        data = result[1]["data"]
        self.assertEqual(data["entities"]["total"], 2)

    def test_entities_single_filtered_is_featured(self):
        request = HttpRequest()
        request.user = self.authenticatedUser

        variables = {"isFeatured": True, "subtype": "blog"}

        result = graphql_sync(schema, {"query": self.query, "variables": variables}, context_value={"request": request})

        self.assertTrue(result[0])

        data = result[1]["data"]
        self.assertEqual(data["entities"]["total"], 1)

    def test_entities_multiple_filtered_is_featured(self):
        request = HttpRequest()
        request.user = self.authenticatedUser

        variables = {"isFeatured": True, "subtypes": ["blog", "news"]}

        result = graphql_sync(schema, {"query": self.query, "variables": variables}, context_value={"request": request})

        self.assertTrue(result[0])

        data = result[1]["data"]
        self.assertEqual(data["entities"]["total"], 2)

    def test_entities_limit(self):
        request = HttpRequest()
        request.user = self.authenticatedUser

        variables = {"limit": 5}

        result = graphql_sync(schema, {"query": self.query, "variables": variables}, context_value={"request": request})

        self.assertTrue(result[0])

        data = result[1]["data"]

        self.assertEqual(len(data["entities"]["edges"]), 5)
        self.assertEqual(data["entities"]["total"], 8)

    def test_entities_all_order_by_title_asc(self):
        request = HttpRequest()
        request.user = self.authenticatedUser

        variables = {
            "containerGuid": None,
            "orderBy": "title",
            "orderDirection": "asc"
        }

        result = graphql_sync(schema, {"query": self.query, "variables": variables}, context_value={"request": request})

        self.assertTrue(result[0])

        data = result[1]["data"]

        self.assertEqual(data["entities"]["edges"][2]["guid"], self.blog4.guid)

    def test_entities_blogs_order_by_title_desc(self):
        request = HttpRequest()
        request.user = self.authenticatedUser

        variables = {
            "containerGuid": None,
            "orderBy": "title",
            "orderDirection": "desc",
            "subtype": "blog"
        }

        result = graphql_sync(schema, {"query": self.query, "variables": variables}, context_value={"request": request})

        self.assertTrue(result[0])

        data = result[1]["data"]

        self.assertEqual(data["entities"]["edges"][0]["guid"], self.blog3.guid)

    def test_entities_show_pinned(self):
        request = HttpRequest()
        request.user = self.authenticatedUser

        variables = {
            "containerGuid": None,
            "showPinned": True
        }

        result = graphql_sync(schema, {"query": self.query, "variables": variables}, context_value={"request": request})

        self.assertTrue(result[0])

        data = result[1]["data"]

        self.assertEqual(data["entities"]["edges"][0]["guid"], self.page3.guid)

    def test_entities_all_draft(self):
        request = HttpRequest()
        request.user = self.authenticatedUser

        variables = {
            "containerGuid": None,
            "statusPublished": 'draft'
        }

        result = graphql_sync(schema, {"query": self.query, "variables": variables}, context_value={"request": request})

        self.assertTrue(result[0])

        data = result[1]["data"]

        self.assertEqual(data["entities"]["total"], 1)

    def test_entities_all_draft_admin(self):
        request = HttpRequest()
        request.user = self.admin

        variables = {
            "containerGuid": None,
            "statusPublished": 'draft'
        }

        success, result = graphql_sync(schema, {"query": self.query, "variables": variables},
                                       context_value={"request": request})

        self.assertTrue(success, msg=result)

        data = result["data"]

        self.assertIsNotNone(data, msg=result)
        self.assertIsNotNone(data.get('entities'), msg=result)

        self.assertEqual(data["entities"]["total"], 2)

    def test_entities_all_draft_anon(self):
        request = HttpRequest()
        request.user = self.anonymousUser

        variables = {
            "containerGuid": None,
            "statusPublished": 'draft'
        }

        success, result = graphql_sync(schema, {"query": self.query, "variables": variables},
                                       context_value={"request": request})

        self.assertTrue(success, msg=result)

        data = result.get("data")

        self.assertIsNotNone(data, msg=result)
        self.assertIsNotNone(data.get('entities'), msg=result)
        self.assertEqual(data["entities"]["total"], 0)

    def test_entities_all_draft_other(self):
        request = HttpRequest()
        request.user = self.user2

        variables = {
            "containerGuid": None,
            "statusPublished": ['draft']
        }

        success, result = graphql_sync(schema, {"query": self.query, "variables": variables},
                                       context_value={"request": request})

        self.assertTrue(success, msg=result)

        data = result["data"]
        self.assertIsNotNone(data, msg=result)
        self.assertIsNotNone(data.get('entities'), msg=result)

        result_guids = {e["guid"] for e in data['entities']['edges']}
        result_msg = "Result is %s" % [e["title"] for e in data['entities']['edges']]
        self.assertEqual(data["entities"]["total"], 1, msg=result_msg)
        self.assertNotIn(self.blog_draft1.guid, result_guids, msg=result_msg)
        self.assertIn(self.blog_draft2.guid, result_guids, msg=result_msg)

    def test_entities_all_for_user(self):
        request = HttpRequest()
        request.user = self.authenticatedUser

        variables = {
            "containerGuid": None,
            "userGuid": self.authenticatedUser.guid
        }

        result = graphql_sync(schema, {"query": self.query, "variables": variables}, context_value={"request": request})

        self.assertTrue(result[0])

        data = result[1]["data"]

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
                                              ("while testing anonymous user", self.anonymousUser),
                                              ("while testing authenticated user", self.authenticatedUser)]:
            request = HttpRequest()
            request.user = user

            variables = {
                "containerGuid": None,
                "statusPublished": 'archived',
            }

            success, result = graphql_sync(schema, {"query": self.query, "variables": variables},
                                           context_value={"request": request})
            self.assertIsNone(result.get('errors'),
                              msg="Errors %s %s" % (while_testing_with_user, result.get('errors')))
            self.assertIsNotNone(result, msg="No result %s" % while_testing_with_user)
            self.assertIsNotNone(result.get('data'), msg="Data is empty %s" % while_testing_with_user)

            data = result.get("data")
            self.assertEqual(data["entities"]["total"], 2,
                             msg="Unexpected number of results %s" % while_testing_with_user)
            result_guids = {e["guid"] for e in data['entities']['edges']}
            self.assertIn(self.archived1.guid, result_guids)
            self.assertIn(self.archived2.guid, result_guids)

    def test_enities_filter_my_draft_archived_articles(self):
        request = HttpRequest()
        request.user = self.authenticatedUser

        variables = {
            "containerGuid": None,
            "userGuid": self.authenticatedUser.guid,
            "statusPublished": ['archived', 'draft'],
        }

        result = graphql_sync(schema, {"query": self.query, "variables": variables}, context_value={"request": request})

        self.assertTrue(result[0])
        data = result[1]["data"]
        self.assertEqual(data["entities"]["total"], 2)
        result_guids = {e["guid"] for e in data['entities']['edges']}
        self.assertIn(self.blog_draft1.guid, result_guids)
        self.assertIn(self.archived1.guid, result_guids)

    def test_entities_all_for_admin_by_user(self):
        request = HttpRequest()
        request.user = self.authenticatedUser

        variables = {
            "containerGuid": None,
            "userGuid": self.admin.guid
        }

        result = graphql_sync(schema, {"query": self.query, "variables": variables}, context_value={"request": request})

        self.assertTrue(result[0])

        data = result[1]["data"]

        self.assertEqual(data["entities"]["total"], 3)

    def test_entities_all_for_admin(self):
        request = HttpRequest()
        request.user = self.admin

        variables = {
            "containerGuid": None,
            "userGuid": self.admin.guid
        }

        result = graphql_sync(schema, {"query": self.query, "variables": variables}, context_value={"request": request})

        self.assertTrue(result[0])

        data = result[1]["data"]

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
        request = HttpRequest()
        request.user = self.authenticatedUser

        variables = {
            "guid": self.blog_draft1.guid
        }

        success, result = graphql_sync(schema, {"query": query, "variables": variables},
                                       context_value={"request": request})

        self.assertTrue(success, msg=result)

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
        request = HttpRequest()
        request.user = self.user2

        variables = {
            "guid": self.blog_draft1.guid
        }

        result = graphql_sync(schema, {"query": query, "variables": variables}, context_value={"request": request})

        self.assertTrue(result[0])

        data = result[1]["data"]
        self.assertIsNone(data["entity"])

    def test_entities_no_subevents(self):
        event = Event.objects.create(
            title="Event1",
            owner=self.authenticatedUser,
            read_access=[ACCESS_TYPE.public],
            write_access=[ACCESS_TYPE.user.format(self.authenticatedUser.id)]
        )
        subevent = Event.objects.create(
            title="Subevent1",
            owner=self.authenticatedUser,
            read_access=[ACCESS_TYPE.public],
            write_access=[ACCESS_TYPE.user.format(self.authenticatedUser.id)],
            parent=event
        )

        request = HttpRequest()
        request.user = self.authenticatedUser

        variables = {
            "containerGuid": None,
            "orderBy": "timeCreated"
        }

        result = graphql_sync(schema, {"query": self.query, "variables": variables}, context_value={"request": request})

        self.assertTrue(result[0])

        data = result[1]["data"]

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