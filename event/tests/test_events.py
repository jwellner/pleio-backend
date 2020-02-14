from django.db import connection
from django_tenants.test.cases import FastTenantTestCase
from backend2.schema import schema
from ariadne import graphql_sync
import json
from django.contrib.auth.models import AnonymousUser
from django.http import HttpRequest
from django.utils import timezone
from core.models import Group
from user.models import User
from event.models import Event
from mixer.backend.django import mixer
from core.constances import ACCESS_TYPE
from core.lib import get_acl, access_id_to_acl
from django.utils.text import slugify


class EventsTestCase(FastTenantTestCase):

    def setUp(self):
        tomorrow = timezone.now() + timezone.timedelta(days=1)
        yesterday = timezone.now() - timezone.timedelta(days=1)
        hours_ago_1 = timezone.now() - timezone.timedelta(hours=1)
        self.anonymousUser = AnonymousUser()
        self.user1 = mixer.blend(User)
        self.user2 = mixer.blend(User)

        self.eventFuture1 = Event.objects.create(
            title="Test future event 1",
            description="Description",
            rich_description="JSON to string",
            read_access=[ACCESS_TYPE.logged_in],
            write_access=[ACCESS_TYPE.user.format(self.user1.id)],
            owner=self.user1,
            start_date=tomorrow,
            location="Utrecht",
            external_link="https://www.pleio.nl",
            rsvp=True,
            max_attendees=None
        )

        self.eventFuture2 = Event.objects.create(
            title="Test future event 2",
            description="Description",
            rich_description="JSON to string",
            read_access=[ACCESS_TYPE.public],
            write_access=[ACCESS_TYPE.user.format(self.user1.id)],
            owner=self.user1,
            start_date=tomorrow,
            location="Utrecht",
            external_link="https://www.pleio.nl",
            rsvp=True,
            max_attendees=None
        )

        self.eventPast1 = Event.objects.create(
            title="Test past event 1",
            description="Description",
            rich_description="JSON to string",
            read_access=[ACCESS_TYPE.public],
            write_access=[ACCESS_TYPE.user.format(self.user1.id)],
            owner=self.user1,
            start_date=yesterday,
            location="Utrecht",
            external_link="https://www.pleio.nl",
            rsvp=True,
            max_attendees=None
        )
        self.eventOneHourAgo = Event.objects.create(
            title="Test past event 1",
            description="Description",
            rich_description="JSON to string",
            read_access=[ACCESS_TYPE.public],
            write_access=[ACCESS_TYPE.user.format(self.user1.id)],
            owner=self.user1,
            start_date=hours_ago_1,
            location="Utrecht",
            external_link="https://www.pleio.nl",
            rsvp=True,
            max_attendees=None
        )

        self.query = """
            query EventsList($filter: EventFilter, $offset: Int, $limit: Int) {
                events(filter: $filter, offset: $offset, limit: $limit) {
                        total
                        edges {
                        guid
                        ...EventListFragment
                        __typename
                        }
                        __typename
                    }
                }

                fragment EventListFragment on Event {
                    guid
                    title
                    excerpt
                    url
                    votes
                    hasVoted
                    isBookmarked
                    inGroup
                    canBookmark
                    tags
                    rsvp
                    isFeatured
                    featured {
                        image
                        video
                        positionY
                        __typename
                    }
                    startDate
                    endDate
                    location
                    timeCreated
                    commentCount
                    comments {
                        guid
                        description
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
                    owner {
                        guid
                        username
                        name
                        url
                        icon
                        __typename
                    }
                    attendees(limit: 5) {
                        total
                        edges {
                        guid
                        username
                        name
                        icon
                        __typename
                        }
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
        self.eventFuture1.delete()
        self.eventFuture2.delete()
        self.eventPast1.delete()
        self.eventOneHourAgo.delete()
        self.user1.delete()
        self.user2.delete()

    def test_events_anonymous(self):

        request = HttpRequest()
        request.user = self.anonymousUser

        variables = {
            "limit": 20,
            "offset": 0,
            "filter": "upcoming"
        }

        result = graphql_sync(schema, { "query": self.query , "variables": variables}, context_value=request)

        self.assertTrue(result[0])

        data = result[1]["data"]
        self.assertEqual(data["events"]["total"], 2)

    def test_events_upcoming(self):

        request = HttpRequest()
        request.user = self.user2

        variables = {
            "limit": 20,
            "offset": 0,
            "filter": "upcoming"
        }

        result = graphql_sync(schema, { "query": self.query , "variables": variables}, context_value=request)

        self.assertTrue(result[0])

        data = result[1]["data"]
        self.assertEqual(data["events"]["total"], 3)

    def test_events_previous(self):

        request = HttpRequest()
        request.user = self.user2

        variables = {
            "limit": 20,
            "offset": 0,
            "filter": "previous"
        }

        result = graphql_sync(schema, { "query": self.query , "variables": variables}, context_value=request)

        self.assertTrue(result[0])

        data = result[1]["data"]
        self.assertEqual(data["events"]["total"], 1)

    def test_events_no_filter(self):

        request = HttpRequest()
        request.user = self.user2

        variables = {
            "limit": 20,
            "offset": 0,
            "filter": ""
        }

        result = graphql_sync(schema, { "query": self.query , "variables": variables}, context_value=request)

        self.assertTrue(result[0])

        errors = result[1]["errors"]

        self.assertEqual(errors[0]["message"], "Variable '$filter' got invalid value ''; Expected type EventFilter.")
