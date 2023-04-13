import datetime

from django.utils import timezone
from django.utils.translation import ugettext_lazy
from mixer.backend.django import mixer

from core.constances import ACCESS_TYPE, USER_ROLES
from core.constances import ENTITY_STATUS
from core.lib import datetime_isoformat
from core.models import Group
from core.tests.helpers import PleioTenantTestCase
from core.views import attachment
from event.models import Event
from file.models import FileFolder
from user.models import User


class CopyEventTestCase(PleioTenantTestCase):

    def setUp(self):
        super().setUp()

        self.now = datetime.datetime.now(tz=timezone.utc)
        self.authenticatedUser = mixer.blend(User)
        self.admin = mixer.blend(User, roles=[USER_ROLES.ADMIN])
        self.user2 = mixer.blend(User)
        self.group = mixer.blend(Group, owner=self.authenticatedUser, is_membership_on_request=False)
        self.group.join(self.authenticatedUser, 'owner')

        self.eventPublic = mixer.blend(Event,
                                       owner=self.authenticatedUser,
                                       read_access=[ACCESS_TYPE.public],
                                       write_access=[ACCESS_TYPE.user.format(self.authenticatedUser.id)],
                                       start_date="2020-09-15 09:20:51.15+00",
                                       end_date="2020-09-16 07:20:51.15+00"
                                       )

        self.eventGroup = mixer.blend(Event,
                                      owner=self.authenticatedUser,
                                      read_access=[ACCESS_TYPE.public],
                                      write_access=[ACCESS_TYPE.user.format(self.authenticatedUser.id)],
                                      group=self.group
                                      )

        self.eventAttachment = mixer.blend(Event,
                                           owner=self.authenticatedUser,
                                           read_access=[ACCESS_TYPE.public],
                                           write_access=[ACCESS_TYPE.user.format(self.authenticatedUser.id)]
                                           )

        self.attachment = self.file_factory(self.relative_path(__file__, ['assets', 'landscape.jpeg']))
        self.eventAttachment.rich_description = self.tiptap_attachment(self.attachment)
        self.eventAttachment.save()

        self.data = {
            "input": {
                "guid": self.eventPublic.guid,
                "ownerGuid": self.authenticatedUser.guid,
                "subtype": "event",
                "copySubevents": True
            }
        }
        self.data2 = {
            "input": {
                "guid": self.eventAttachment.guid,
                "ownerGuid": self.authenticatedUser.guid,
                "subtype": "event"
            }
        }
        self.data3 = {
            "input": {
                "guid": self.eventGroup.guid,
                "ownerGuid": self.authenticatedUser.guid,
                "subtype": "event"
            }
        }

        self.mutation = """
            fragment EventParts on Event {
                title
                richDescription
                timeCreated
                timeUpdated
                hasChildren
                accessId
                writeAccessId
                canEdit
                tags
                url
                inGroup
                group {
                    guid
                }
                owner {
                    guid
                }
                rsvp
                source
                attendEventWithoutAccount
                startDate
                endDate
                location
                maxAttendees
                isFeatured
                isPinned
            }
            mutation ($input: copyEntityInput!) {
                copyEntity(input: $input) {
                    entity {
                        guid
                        ...EventParts
                    }
                }
            }
        """

    def test_copy_event(self):
        self.graphql_client.force_login(self.authenticatedUser)
        result = self.graphql_client.post(self.mutation, self.data)

        data = result["data"]
        self.assertEqual(data["copyEntity"]["entity"]["title"], ugettext_lazy("Copy %s") % self.eventPublic.title)
        self.assertEqual(data["copyEntity"]["entity"]["richDescription"], self.eventPublic.rich_description)
        start_date = self.eventPublic.start_date.replace(year=self.now.year, month=self.now.month, day=self.now.day, microsecond=0, tzinfo=timezone.utc)
        self.assertEqual(data["copyEntity"]["entity"]["startDate"], str(datetime_isoformat(start_date)))
        end_date = start_date + (self.eventPublic.end_date - self.eventPublic.start_date)
        self.assertEqual(data["copyEntity"]["entity"]["endDate"], str(datetime_isoformat(end_date)))
        self.assertEqual(data["copyEntity"]["entity"]["maxAttendees"], self.eventPublic.max_attendees)
        self.assertEqual(data["copyEntity"]["entity"]["location"], self.eventPublic.location)
        self.assertEqual(data["copyEntity"]["entity"]["source"], self.eventPublic.external_link)
        self.assertEqual(data["copyEntity"]["entity"]["attendEventWithoutAccount"], self.eventPublic.attend_event_without_account)
        self.assertEqual(data["copyEntity"]["entity"]["rsvp"], self.eventPublic.rsvp)
        self.assertEqual(data["copyEntity"]["entity"]["group"], None)
        self.assertEqual(data["copyEntity"]["entity"]["owner"]["guid"], self.authenticatedUser.guid)

        self.assertFalse(data["copyEntity"]["entity"]["isFeatured"])
        self.assertFalse(data["copyEntity"]["entity"]["isPinned"])

    def test_copy_event_not_logged_in(self):
        with self.assertGraphQlError("not_logged_in"):
            self.graphql_client.post(self.mutation, self.data)

    def test_copy_event_unauthorized(self):
        with self.assertGraphQlError("could_not_save"):
            self.graphql_client.force_login(self.user2)
            self.graphql_client.post(self.mutation, self.data)

    def test_copy_with_attachment(self):
        self.graphql_client.force_login(self.admin)
        result = self.graphql_client.post(self.mutation, self.data2)

        data = result["data"]
        event = Event.objects.get(id=data["copyEntity"]["entity"]["guid"])

        attachments = FileFolder.objects.filter(pk__in=[*event.lookup_attachments()])

        access = [ACCESS_TYPE.user.format(self.admin.id)]
        self.assertEqual(event.read_access[0], access[0])
        self.assertEqual(event.write_access[0], access[0])

        for x in attachments:
            self.assertTrue(event.attachments.filter(file_id=x.id).exists())
            self.assertTrue(x.can_read(self.admin))
            response = attachment(self.graphql_client.request, x.id)
            self.assertEqual(response.status_code, 200)

        self.assertEqual(data["copyEntity"]["entity"]["richDescription"], self.eventAttachment.rich_description)

    def test_copy_with_attachment_delete(self):
        self.graphql_client.force_login(self.admin)
        result = self.graphql_client.post(self.mutation, self.data2)

        data = result["data"]
        event = Event.objects.get(id=data["copyEntity"]["entity"]["guid"])

        attachments = FileFolder.objects.filter(pk__in=[*event.lookup_attachments()])

        mutation = """
            mutation deleteEntity($input: deleteEntityInput!) {
                deleteEntity(input: $input) {
                    success
                }
            }
        """
        variables = {
            "input": {
                "guid": self.eventAttachment.guid
            }
        }

        self.graphql_client.post(mutation, variables)

        for x in attachments:
            self.assertTrue(event.attachments.filter(file_id=x.id).exists())
            self.assertTrue(x.can_read(self.admin))
            response = attachment(self.graphql_client.request, x.id)
            self.assertEqual(response.status_code, 200)

    def test_copy_with_children(self):
        subevent = mixer.blend(Event,
                               parent=self.eventPublic)
        mixer.blend(Event,
                    parent=self.eventPublic)
        self.eventPublic.refresh_from_db()

        self.graphql_client.force_login(self.authenticatedUser)
        result = self.graphql_client.post(self.mutation, self.data)

        data = result["data"]
        event = Event.objects.get(id=data["copyEntity"]["entity"]["guid"])

        event.refresh_from_db()

        self.assertEqual(event.status_published, ENTITY_STATUS.DRAFT)
        self.assertTrue(event.has_children())
        self.assertNotEqual(subevent.guid, event.children.first().guid)
        self.assertEqual(event.children.count(), 2)
        for child in event.children.all():
            self.assertEqual(child.status_published, ENTITY_STATUS.DRAFT)

        event.published = timezone.now()
        event.save()
        self.assertEqual(event.status_published, ENTITY_STATUS.PUBLISHED)
        for child in event.children.all():
            self.assertEqual(child.status_published, ENTITY_STATUS.PUBLISHED)

    def test_copy_in_group(self):
        self.graphql_client.force_login(self.authenticatedUser)
        result = self.graphql_client.post(self.mutation, self.data3)

        data = result["data"]
        event = Event.objects.get(id=data["copyEntity"]["entity"]["guid"])
        self.assertEqual(event.group.guid, self.group.guid)
        self.assertEqual(data["copyEntity"]["entity"]["group"]["guid"], self.group.guid)
        self.assertEqual(data["copyEntity"]["entity"]["owner"]["guid"], self.authenticatedUser.guid)

    def test_copy_with_children_in_group(self):
        subevent = mixer.blend(Event,
                               parent=self.eventGroup)
        mixer.blend(Event,
                    parent=self.eventGroup)
        self.assertEqual(subevent.group.guid, self.group.guid)
        self.eventPublic.refresh_from_db()

        self.graphql_client.force_login(self.authenticatedUser)
        result = self.graphql_client.post(self.mutation, self.data3)

        data = result["data"]
        event = Event.objects.get(id=data["copyEntity"]["entity"]["guid"])
        event.refresh_from_db()
        self.assertEqual(event.status_published, ENTITY_STATUS.DRAFT)
        self.assertTrue(event.has_children())
        self.assertNotEqual(subevent.guid, event.children.first().guid)
        self.assertEqual(event.children.count(), 2)
        self.assertEqual(self.eventGroup.children.count(), 2)
        for child in event.children.all():
            self.assertEqual(child.group.guid, self.group.guid)
            self.assertEqual(child.status_published, ENTITY_STATUS.DRAFT)

        event.published = timezone.now()
        event.save()
        self.assertEqual(event.status_published, ENTITY_STATUS.PUBLISHED)
        for child in event.children.all():
            self.assertEqual(child.status_published, ENTITY_STATUS.PUBLISHED)
