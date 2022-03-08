from django.db import connection
from django_tenants.test.cases import FastTenantTestCase
from core.models import Group, Comment
from user.models import User
from blog.models import Blog
from event.models import Event
from core.constances import ACCESS_TYPE
from backend2.schema import schema
from ariadne import graphql_sync
import json
from django.contrib.auth.models import AnonymousUser
from django.http import HttpRequest
from mixer.backend.django import mixer

class ActivitiesTestCase(FastTenantTestCase):

    def setUp(self):
        self.user1 = mixer.blend(User)
        self.user2 = mixer.blend(User)
        self.group1 = mixer.blend(Group, owner=self.user1)
        self.group2 = mixer.blend(Group, owner=self.user2, is_closed=True)
        self.group1.join(self.user1, 'owner')
        self.group1.join(self.user2, 'member')

        self.blog1 = Blog.objects.create(
            title="Blog1",
            owner=self.user1,
            read_access=[ACCESS_TYPE.public],
            write_access=[ACCESS_TYPE.user.format(self.user1.id)],
            tags=["tag_one", "tag_two"]
        )
        self.blog2 = Blog.objects.create(
            title="Blog2",
            owner=self.user1,
            read_access=[ACCESS_TYPE.public],
            write_access=[ACCESS_TYPE.user.format(self.user1.id)],
            group=self.group2,
            tags=["tag_two", "tag_three"]
        )
        self.blog3 = Blog.objects.create(
            title="Blog3",
            owner=self.user1,
            read_access=[ACCESS_TYPE.public],
            write_access=[ACCESS_TYPE.user.format(self.user1.id)],
            group=self.group1,
            tags=["tag_three"]
        )
        self.blog4 = Blog.objects.create(
            title="Blog4",
            owner=self.user2,
            read_access=[ACCESS_TYPE.group.format(self.group2.id)],
            write_access=[ACCESS_TYPE.user.format(self.user1.id)],
            group=self.group2,
            tags=["tag_four"]
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
        self.user1.delete()
        self.user2.delete()

    def test_activities_group_filter_all(self):
        request = HttpRequest()
        request.user = self.user1

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
        result = graphql_sync(schema, { "query": self.query, "variables": variables }, context_value={ "request": request })

        self.assertTrue(result[0])

        data = result[1]["data"]

        self.assertEqual(data["activities"]["total"], 47)

    def test_activities_group_filter_mine(self):
        request = HttpRequest()
        request.user = self.user1

        variables = {
            "groupFilter": ["mine"],
            "limit": 20,
            "offset": 0,
            "subtypes": [],
            "tags": []
        }

        result = graphql_sync(schema, { "query": self.query, "variables": variables }, context_value={ "request": request })

        self.assertTrue(result[0])

        data = result[1]["data"]

        self.assertEqual(data["activities"]["total"], 1)

    def test_activities_taglists_filter(self):
        request = HttpRequest()
        request.user = self.user2

        variables = {
            "limit": 20,
            "offset": 0,
            "subtypes": [],
            "tags": [],
            "tagLists": [["tag_one", "tag_three"], ["tag_two"]]
        }

        result = graphql_sync(schema, { "query": self.query, "variables": variables }, context_value={ "request": request })

        self.assertTrue(result[0])

        data = result[1]["data"]

        self.assertEqual(data["activities"]["total"], 2)


    def test_activities_show_pinned(self):
        request = HttpRequest()
        request.user = self.user2

        variables = {
            "limit": 20,
            "offset": 0,
            "subtypes": [],
            "containerGuid": None,
            "sortPinned": True
        }

        result = graphql_sync(schema, { "query": self.query, "variables": variables }, context_value={ "request": request })

        self.assertTrue(result[0])

        data = result[1]["data"]

        self.assertEqual(data["activities"]["edges"][0]["entity"]["guid"], self.blog5.guid)

    def test_activities_last_action(self):
        request = HttpRequest()
        request.user = self.user2

        variables = {
            "limit": 20,
            "offset": 0,
            "subtypes": [],
            "containerGuid": None,
            "orderBy": "lastAction"
        }

        result = graphql_sync(schema, { "query": self.query, "variables": variables }, context_value={ "request": request })

        self.assertTrue(result[0])

        data = result[1]["data"]

        self.assertEqual(data["activities"]["edges"][0]["entity"]["guid"], self.blog1.guid)

    def test_activities_no_subevents(self):
        
        event = Event.objects.create(
            title="event",
            owner=self.user1,
            read_access=[ACCESS_TYPE.public],
            write_access=[ACCESS_TYPE.user.format(self.user1.id)],
            tags=["tag_one", "tag_two"]
        )
       
        subevent = Event.objects.create(
            title="subevent",
            owner=self.user1,
            read_access=[ACCESS_TYPE.public],
            write_access=[ACCESS_TYPE.user.format(self.user1.id)],
            tags=["tag_one", "tag_two"],
            parent = event
        )

        variables = {
            "limit": 20,
            "offset": 0,
            "subtypes": [],
            "containerGuid": None,
            "orderBy": "timeCreated"
        }      
        request = HttpRequest()
        request.user = self.user2

        
        result = graphql_sync(schema, { "query": self.query, "variables": variables }, context_value={ "request": request })

        self.assertTrue(result[0])

        data = result[1]["data"]

        self.assertEqual(data["activities"]["edges"][0]["entity"]["guid"], event.guid)
