from cms.models import Page
from core.models import Group, Comment
from core.tests.helpers import PleioTenantTestCase
from user.factories import UserFactory
from blog.models import Blog
from event.models import Event
from core.constances import ACCESS_TYPE
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
        self.blog1.tags = ["tag_one", "tag_two"]
        self.blog1.save()
        self.blog2 = Blog.objects.create(
            title="Blog2",
            owner=self.user1,
            read_access=[ACCESS_TYPE.public],
            write_access=[ACCESS_TYPE.user.format(self.user1.id)],
            group=self.group2
        )
        self.blog2.tags = ["tag_two", "tag_three"]
        self.blog2.save()
        self.blog3 = Blog.objects.create(
            title="Blog3",
            owner=self.user1,
            read_access=[ACCESS_TYPE.public],
            write_access=[ACCESS_TYPE.user.format(self.user1.id)],
            group=self.group1
        )
        self.blog3.tags = ["tag_three"]
        self.blog3.save()
        self.blog4 = Blog.objects.create(
            title="Blog4",
            owner=self.user2,
            read_access=[ACCESS_TYPE.group.format(self.group2.id)],
            write_access=[ACCESS_TYPE.user.format(self.user1.id)],
            group=self.group2,
        )
        self.blog4.tags = ["tag_four"]
        self.blog4.save()
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
            query ActivityList($offset: Int!, $limit: Int!, $subtypes: [String!], $groupFilter: [String!], $tags: [String!], $tagLists: [[String]], $orderBy: OrderBy, $orderDirection: OrderDirection, $sortPinned: Boolean) {
                activities(offset: $offset, limit: $limit, tags: $tags, tagLists: $tagLists, subtypes: $subtypes, groupFilter: $groupFilter, orderBy: $orderBy, orderDirection: $orderDirection, sortPinned: $sortPinned) {
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
                url
                excerpt
                richDescription
                isHighlighted
                featured {
                    image
                    video
                    videoTitle
                    positionY
                    __typename
                }
                subtype
                tags
                timeCreated
                isBookmarked
                canBookmark
                canEdit
                commentCount
                comments {
                    guid
                    richDescription
                    timeCreated
                    canEdit
                    hasVoted
                    votes
                    owner {
                    guid
                    username
                    name
                    icon
                    url
                    __typename
                    }
                    __typename
                }
                hasVoted
                votes
                owner {
                    guid
                    username
                    name
                    icon
                    url
                    __typename
                }
                group {
                    guid
                    ... on Group {
                    name
                    url
                    membership
                    __typename
                    }
                    __typename
                }
                __typename
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

    def test_activities_group_filter_all(self):
        variables = {
            "groupFilter": ["all"],
            "limit": 20,
            "offset": 0,
            "subtypes": [],
            "tags": []
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
            "tags": []
        }

        self.graphql_client.force_login(self.user1)
        result = self.graphql_client.post(self.query, variables)

        self.assertEqual(result["data"]["activities"]["total"], 1)

    def test_activities_taglists_filter(self):
        variables = {
            "limit": 20,
            "offset": 0,
            "subtypes": [],
            "tags": [],
            "tagLists": [["tag_one", "tag_three"], ["tag_two"]]
        }

        self.graphql_client.force_login(self.user2)
        result = self.graphql_client.post(self.query, variables)

        self.assertEqual(result["data"]["activities"]["total"], 2)

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

    def test_activities_no_subevents(self):
        event = Event.objects.create(
            title="event",
            owner=self.user1,
            read_access=[ACCESS_TYPE.public],
            write_access=[ACCESS_TYPE.user.format(self.user1.id)]
        )
        event.tags = ["tag_one", "tag_two"]
        event.save()

        subevent = Event.objects.create(
            title="subevent",
            owner=self.user1,
            read_access=[ACCESS_TYPE.public],
            write_access=[ACCESS_TYPE.user.format(self.user1.id)],
            parent=event
        )
        subevent.tags = ["tag_one", "tag_two"]
        subevent.save()

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
