from cms.models import Page
from core.models import Group, Comment
from core.tests.helpers import PleioTenantTestCase
from django.utils import timezone
from user.factories import UserFactory
from blog.models import Blog
from event.models import Event
from core.constances import ACCESS_TYPE, COULD_NOT_ORDER_BY_START_DATE, COULD_NOT_USE_EVENT_FILTER
from mixer.backend.django import mixer


class ActivitiesTestCase(PleioTenantTestCase):

    def setUp(self):
        super(ActivitiesTestCase, self).setUp()

        self.user1 = UserFactory()
        self.user2 = UserFactory()
        self.group1 = mixer.blend(Group, owner=self.user1)
        self.group2 = mixer.blend(Group, owner=self.user2, is_closed=True)
        self.group1.join(self.user1, 'owner')
        self.group1.join(self.user2, 'member')

        self.blog1 = Blog.objects.create(
            title="Blog1",
            owner=self.user1,
            read_access=[ACCESS_TYPE.public],
            write_access=[ACCESS_TYPE.user.format(self.user1.id)]
        )
        self.blog2 = Blog.objects.create(
            title="Blog2",
            owner=self.user1,
            read_access=[ACCESS_TYPE.public],
            write_access=[ACCESS_TYPE.user.format(self.user1.id)],
            group=self.group2
        )
        self.blog3 = Blog.objects.create(
            title="Blog3",
            owner=self.user1,
            read_access=[ACCESS_TYPE.public],
            write_access=[ACCESS_TYPE.user.format(self.user1.id)],
            group=self.group1
        )
        self.blog4 = Blog.objects.create(
            title="Blog4",
            owner=self.user2,
            read_access=[ACCESS_TYPE.group.format(self.group2.id)],
            write_access=[ACCESS_TYPE.user.format(self.user1.id)],
            group=self.group2
        )
        self.blog5 = Blog.objects.create(
            title="Blog5",
            owner=self.user1,
            read_access=[ACCESS_TYPE.public],
            write_access=[ACCESS_TYPE.user.format(self.user1.id)],
            is_pinned=True
        )

        self.comment = Comment.objects.create(
            owner=self.user2,
            container=self.blog1,
            rich_description="Just testing"
        )
        self.textPage = Page.objects.create(
            title="Textpage",
            page_type='text',
            owner=self.user1,
            read_access=[ACCESS_TYPE.user.format(self.user1.id)]
        )
        self.campagnePage = Page.objects.create(
            title="Campagne",
            page_type='campagne',
            owner=self.user1,
            read_access=[ACCESS_TYPE.user.format(self.user1.id)]
        )

        self.query = """
            query ActivityList(
                    $offset: Int
                    $limit: Int
                    $subtypes: [String!]
                    $groupFilter: [String!]
                    $orderBy: OrderBy
                    $orderDirection: OrderDirection
                    $sortPinned: Boolean) {
                activities(
                        offset: $offset
                        limit: $limit
                        subtypes: $subtypes
                        groupFilter: $groupFilter
                        orderBy: $orderBy
                        orderDirection: $orderDirection
                        sortPinned: $sortPinned) {
                    total
                    edges {
                        guid
                        type
                        entity {
                            guid
                            ...BlogListFragment
                            __typename
                        }
                        __typename
                    }
                    __typename
                }
            }

            fragment BlogListFragment on Blog {
                title
            }

        """

    def tearDown(self):
        self.comment.delete()
        self.blog1.delete()
        self.blog2.delete()
        self.blog3.delete()
        self.blog4.delete()
        self.group1.delete()
        self.group2.delete()
        super().tearDown()

    def test_activities_group_filter_all(self):
        variables = {
            "groupFilter": ["all"],
            "limit": 20,
            "offset": 0,
            "subtypes": [],
        }
        mixer.cycle(45).blend(
            Blog,
            owner=self.user2,
            read_access=[ACCESS_TYPE.public],
            write_access=[ACCESS_TYPE.user.format(self.user2.id)],
            group=self.group2
        )
        self.graphql_client.force_login(self.user1)
        result = self.graphql_client.post(self.query, variables)

        self.assertEqual(result["data"]["activities"]["total"], 47)

    def test_activities_group_filter_mine(self):
        variables = {
            "groupFilter": ["mine"],
            "limit": 20,
            "offset": 0,
            "subtypes": [],
        }

        self.graphql_client.force_login(self.user1)
        result = self.graphql_client.post(self.query, variables)

        self.assertEqual(result["data"]["activities"]["total"], 1)

    def test_activities_show_pinned(self):
        variables = {
            "limit": 20,
            "offset": 0,
            "subtypes": [],
            "containerGuid": None,
            "sortPinned": True
        }

        self.graphql_client.force_login(self.user2)
        result = self.graphql_client.post(self.query, variables)

        self.assertEqual(result["data"]["activities"]["edges"][0]["entity"]["guid"], self.blog5.guid)

    def test_activities_last_action(self):
        variables = {
            "limit": 20,
            "offset": 0,
            "subtypes": [],
            "containerGuid": None,
            "orderBy": "lastAction"
        }

        self.graphql_client.force_login(self.user2)
        result = self.graphql_client.post(self.query, variables)

        self.assertEqual(result["data"]["activities"]["edges"][0]["entity"]["guid"], self.blog1.guid)

    def test_activities_order_by_title_asc(self):
        self.first_blog = Blog.objects.create(
            title="1 first blog",
            owner=self.user1,
            read_access=[ACCESS_TYPE.public],
            write_access=[ACCESS_TYPE.user.format(self.user1.id)],
            group=self.group2
        )

        variables = {
            "limit": 20,
            "offset": 0,
            "subtypes": [],
            "containerGuid": None,
            "orderBy": "title",
            "orderDirection": "asc"
        }

        self.graphql_client.force_login(self.user2)
        result = self.graphql_client.post(self.query, variables)
        self.assertEqual(result["data"]["activities"]["edges"][0]["entity"]["guid"], self.first_blog.guid)

    def test_activities_order_by_title_desc(self):
        self.first_blog = Blog.objects.create(
            title="z first blog",
            owner=self.user1,
            read_access=[ACCESS_TYPE.public],
            write_access=[ACCESS_TYPE.user.format(self.user1.id)],
            group=self.group2
        )

        variables = {
            "limit": 20,
            "offset": 0,
            "subtypes": [],
            "containerGuid": None,
            "orderBy": "title",
            "orderDirection": "desc"
        }

        self.graphql_client.force_login(self.user2)
        result = self.graphql_client.post(self.query, variables)
        self.assertEqual(result["data"]["activities"]["edges"][0]["entity"]["guid"], self.first_blog.guid)

    def test_activities_no_subevents(self):
        event = Event.objects.create(
            title="event",
            owner=self.user1,
            read_access=[ACCESS_TYPE.public],
            write_access=[ACCESS_TYPE.user.format(self.user1.id)]
        )

        subevent = Event.objects.create(
            title="subevent",
            owner=self.user1,
            read_access=[ACCESS_TYPE.public],
            write_access=[ACCESS_TYPE.user.format(self.user1.id)],
            parent=event
        )

        variables = {
            "limit": 20,
            "offset": 0,
            "subtypes": [],
            "containerGuid": None,
            "orderBy": "timeCreated"
        }

        self.graphql_client.force_login(self.user2)
        result = self.graphql_client.post(self.query, variables)

        self.assertEqual(result["data"]["activities"]["edges"][0]["entity"]["guid"], event.guid)

    def test_query_cms_textpages_explicit_subtypes(self):
        query = """
        query ExpectTextPagesOnly($subtypes: [String]) {
            activities(subtypes: $subtypes) {
                edges {
                    entity {
                        ... on Page {
                           title
                        }
                    }
                }
            }
        }
        """

        variables = {
            "subtypes": ['page'],
        }

        self.graphql_client.force_login(self.user1)
        result = self.graphql_client.post(query, variables)

        titles = [e['entity']['title'] for e in result['data']['activities']['edges']]
        self.assertIn(self.textPage.title, titles, msg="Should contain textpage cms pages")
        self.assertNotIn(self.campagnePage.title, titles, msg="Should contain only textpage cms pages")

    def test_query_cms_textpages_implicit_subtypes(self):
        query = """
        query ExpectTextPagesOnly {
            activities {
                edges {
                    entity {
                        ... on Page {
                           title
                        }
                    }
                }
            }
        }
        """

        self.graphql_client.force_login(self.user1)
        result = self.graphql_client.post(query, {})

        titles = [e['entity'].get('title') for e in result['data']['activities']['edges']]
        self.assertIn(self.textPage.title, titles, msg="Should contain textpage cms pages")
        self.assertNotIn(self.campagnePage.title, titles, msg="Should contain only textpage cms pages")


class ActivitiesEventsTestCase(PleioTenantTestCase):

    def setUp(self):
        super(ActivitiesEventsTestCase, self).setUp()

        self.user1 = UserFactory()
        self.user2 = UserFactory()
        self.event_in_4_days = Event.objects.create(
            owner=self.user1,
            read_access=[ACCESS_TYPE.public],
            write_access=[ACCESS_TYPE.user.format(self.user1.id)],
            start_date=timezone.now() + timezone.timedelta(days=4),
            end_date = timezone.now() + timezone.timedelta(days=4)
        )
        self.event_5_days_ago = Event.objects.create(
            owner=self.user1,
            read_access=[ACCESS_TYPE.public],
            write_access=[ACCESS_TYPE.user.format(self.user1.id)],
            start_date=timezone.now() - timezone.timedelta(days=5),
            end_date=timezone.now() - timezone.timedelta(days=5),
        )
        self.event_ongoing = Event.objects.create(
            owner=self.user1,
            read_access=[ACCESS_TYPE.public],
            write_access=[ACCESS_TYPE.user.format(self.user1.id)],
            start_date=timezone.now() - timezone.timedelta(days=5),
            end_date=timezone.now() + timezone.timedelta(days=5),
        )
        self.event_in_6_days = Event.objects.create(
            owner=self.user1,
            read_access=[ACCESS_TYPE.public],
            write_access=[ACCESS_TYPE.user.format(self.user1.id)],
            start_date=timezone.now() + timezone.timedelta(days=6),
            end_date=timezone.now() + timezone.timedelta(days=6),
        )
        self.event_3_days_ago = Event.objects.create(
            owner=self.user1,
            read_access=[ACCESS_TYPE.public],
            write_access=[ACCESS_TYPE.user.format(self.user1.id)],
            start_date=timezone.now() - timezone.timedelta(days=3),
            end_date=timezone.now() - timezone.timedelta(days=3)
        )

        self.query = """
            query ActivityList(
                $offset: Int!,
                $limit: Int!,
                $subtypes: [String!],
                $orderBy: OrderBy,
                $orderDirection: OrderDirection,
                $eventFilter: EventFilter
            ) {
                activities(
                    offset: $offset,
                    limit: $limit,
                    subtypes: $subtypes,
                    orderBy: $orderBy,
                    orderDirection: $orderDirection,
                    eventFilter: $eventFilter) 
                {
                    total
                    edges {
                        guid
                        type
                        entity {
                            guid
                            ...EventListFragment
                        }
                    }
                }
            }
            fragment EventListFragment on Event {
                guid
                title
                url
                startDate
            }

        """

    def test_activities_order_by_title_asc(self):
        variables = {
            "limit": 20,
            "offset": 0,
            "subtypes": ['event'],
            "orderBy": "startDate",
            "orderDirection": "asc"
        }

        self.graphql_client.force_login(self.user2)
        result = self.graphql_client.post(self.query, variables)
        self.assertEqual(result["data"]["activities"]["edges"][0]["entity"]["guid"], self.event_5_days_ago.guid)

    def test_activities_order_by_start_date_desc(self):
        variables = {
            "limit": 20,
            "offset": 0,
            "subtypes": ['event'],
            "orderBy": "startDate",
            "orderDirection": "desc"
        }

        self.graphql_client.force_login(self.user2)
        result = self.graphql_client.post(self.query, variables)
        self.assertEqual(result["data"]["activities"]["edges"][0]["entity"]["guid"], self.event_in_6_days.guid)

    def test_activities_order_by_start_asc(self):
        variables = {
            "limit": 20,
            "offset": 0,
            "subtypes": ['event'],
            "orderBy": "startDate",
            "orderDirection": "asc"
        }

        self.graphql_client.force_login(self.user2)
        result = self.graphql_client.post(self.query, variables)
        self.assertEqual(result["data"]["activities"]["edges"][0]["entity"]["guid"], self.event_5_days_ago.guid)

    def test_entities_blog_event_order_by_start_date_desc(self):
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
        self.assertEqual(len(result["data"]["activities"]["edges"]), 3)
        self.assertEqual(result["data"]["activities"]["edges"][0]["entity"]["guid"], self.event_in_6_days.guid)


    def test_entities_filter_by_previous(self):
        variables = {
            "limit": 20,
            "offset": 0,
            "subtypes": ['event'],
            "eventFilter": 'previous'
        }

        self.graphql_client.force_login(self.user2)
        result = self.graphql_client.post(self.query, variables)
        self.assertEqual(len(result["data"]["activities"]["edges"]), 2)
        self.assertEqual(result["data"]["activities"]["edges"][0]["entity"]["guid"], self.event_3_days_ago.guid)


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
