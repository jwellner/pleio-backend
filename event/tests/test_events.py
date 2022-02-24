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
from event.models import Event, EventAttendee
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
        self.group = mixer.blend(Group, owner=self.user1)

        self.eventOneHourAgo = Event.objects.create(
            title="Test past event 1 hour ago",
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

        self.eventFuture1 = Event.objects.create(
            title="Test future event 1",
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

        self.eventFutureGroup = Event.objects.create(
            title="Test future event in group",
            rich_description="JSON to string",
            read_access=[ACCESS_TYPE.public],
            write_access=[ACCESS_TYPE.user.format(self.user1.id)],
            owner=self.user1,
            start_date=tomorrow,
            location="Utrecht",
            external_link="https://www.pleio.nl",
            rsvp=True,
            max_attendees=None,
            group=self.group
        )

        self.query = """
            query EventsList($filter: EventFilter, $containerGuid: String, $offset: Int, $limit: Int) {
                events(filter: $filter, containerGuid: $containerGuid, offset: $offset, limit: $limit) {
                        total
                        edges {
                        guid
                        ...EventListFragment
                        }
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
                        videoTitle
                        positionY
                    }
                    startDate
                    endDate
                    location
                    timeCreated
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
                        }
                    }
                    owner {
                        guid
                        username
                        name
                        url
                        icon
                    }
                    attendees(limit: 1) {
                        total
                        edges {
                        email
                        name
                        icon
                        }
                    }
                    group {
                        guid
                        ... on Group {
                        name
                        url
                        membership
                        }
                    }
                    }
        """

    def tearDown(self):
        self.eventFuture1.delete()
        self.eventFuture2.delete()
        self.eventFutureGroup.delete()
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
            "containerGuid": "1", # Only get events on site level
            "filter": "upcoming"
        }

        mixer.blend(EventAttendee, user=self.user2, email=None, event=self.eventFuture1)
        mixer.blend(EventAttendee, user=None, event=self.eventFuture1)
        mixer.blend(EventAttendee, user=self.user2, email=None, event=self.eventFuture2)
        mixer.blend(EventAttendee, user=None, event=self.eventFuture2)

        result = graphql_sync(schema, { "query": self.query , "variables": variables}, context_value={ "request": request })

        self.assertTrue(result[0])

        data = result[1]["data"]
        self.assertEqual(data["events"]["total"], 2)
        self.assertEqual(data["events"]["edges"][0]["attendees"]["total"], 0)
        self.assertEqual(len(data["events"]["edges"][0]["attendees"]["edges"]), 0)

    def test_events_upcoming(self):

        request = HttpRequest()
        request.user = self.user2

        variables = {
            "limit": 1,
            "offset": 0,
            "containerGuid": "1",
            "filter": "upcoming"
        }

        # this is the first in upcoming list because it is still today.
        mixer.cycle(2).blend(EventAttendee, event=self.eventOneHourAgo, state='accept')

        result = graphql_sync(schema, { "query": self.query , "variables": variables}, context_value={ "request": request })

        self.assertTrue(result[0])

        data = result[1]["data"]

        self.assertEqual(data["events"]["total"], 3)
        self.assertEqual(data["events"]["edges"][0]["attendees"]["total"], 2)

    def test_events_previous(self):

        request = HttpRequest()
        request.user = self.user2

        variables = {
            "limit": 20,
            "offset": 0,
            "filter": "previous"
        }

        result = graphql_sync(schema, { "query": self.query , "variables": variables}, context_value={ "request": request })

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

        result = graphql_sync(schema, { "query": self.query , "variables": variables}, context_value={ "request": request })

        self.assertTrue(result[0])

        errors = result[1]["errors"]

        self.assertEqual(errors[0]["message"], "Variable '$filter' got invalid value ''; Value '' does not exist in 'EventFilter' enum.")

    def test_events_in_group(self):

        request = HttpRequest()
        request.user = self.user2

        variables = {
            "limit": 20,
            "offset": 0,
            "containerGuid": self.group.guid
        }

        result = graphql_sync(schema, { "query": self.query , "variables": variables}, context_value={ "request": request })

        self.assertTrue(result[0])

        data = result[1]["data"]
        self.assertEqual(data["events"]["total"], 1)
