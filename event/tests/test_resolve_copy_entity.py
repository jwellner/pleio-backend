from django.db import connection
from core.models.entity import Entity
from django_tenants.test.cases import FastTenantTestCase
from backend2.schema import schema
from ariadne import graphql_sync
import json
import os
from django.contrib.auth.models import AnonymousUser
from django.http import HttpRequest
from django.utils.translation import ugettext_lazy
from core.models import Group, Attachment
from user.models import User
from event.models import Event
from core.constances import ACCESS_TYPE, USER_ROLES
from core.lib import datetime_isoformat
from mixer.backend.django import mixer
from graphql import GraphQLError
from datetime import datetime
from django.utils import timezone
from django.core.files import File
from core.views import attachment

class CopyEventTestCase(FastTenantTestCase):
    basepath = 'test_files/'
    
    def setUp(self):
        self.anonymousUser = AnonymousUser()
        self.authenticatedUser = mixer.blend(User)
        self.admin = mixer.blend(User, roles=[USER_ROLES.ADMIN])
        self.user2 = mixer.blend(User)
        self.group = mixer.blend(Group, owner=self.authenticatedUser, is_membership_on_request=False)
        self.group.join(self.authenticatedUser, 'owner')

        self.eventPublic = mixer.blend(Event, 
            owner=self.authenticatedUser, 
            read_access=[ACCESS_TYPE.public], 
            write_access=[ACCESS_TYPE.user.format(self.authenticatedUser.id)]
        )

        self.eventAttachment = mixer.blend(Event, 
            owner=self.authenticatedUser, 
            read_access=[ACCESS_TYPE.public], 
            write_access=[ACCESS_TYPE.user.format(self.authenticatedUser.id)]
        )

        os.makedirs(self.basepath, exist_ok=True)

        self.attachment = mixer.blend(Attachment, attached=self.eventAttachment)
        path = self.attach_file(self.attachment, 'upload', 'testfile.txt')
        self.assertTrue(os.path.isfile(path)) # assert file exists before starting test

        self.eventAttachment.rich_description = json.dumps({ 'type': 'file', 'attrs': {'url': f"/attachment/{self.attachment.id}" }})
        self.eventAttachment.save()

        self.data = {
            "input": {
                "guid": self.eventPublic.guid,
                "ownerGuid": self.authenticatedUser.guid,
                "subtype": "event"
            }
        }
        self.data2 = {
            "input": {
                "guid": self.eventAttachment.guid,
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

    def tearDown(self):
        os.system(f"rm -r {self.basepath}")

    def attach_file(self, instance, attr, filename):
        path = self.basepath + filename
        with open(path, 'w+') as f:
            file = File(f)
            file.write("some content")
            setattr(instance, attr, file)
            instance.save()

        return getattr(instance, attr).path

    def test_copy_event(self):
        
        variables = self.data

        request = HttpRequest()
        request.user = self.authenticatedUser

        result = graphql_sync(schema, { "query": self.mutation, "variables": variables }, context_value={ "request": request })
        time = datetime_isoformat(timezone.now())

        data = result[1]["data"]

        self.assertEqual(data["copyEntity"]["entity"]["title"], ugettext_lazy("Copy %s") %self.eventPublic.title)
        self.assertEqual(data["copyEntity"]["entity"]["richDescription"], self.eventPublic.rich_description)
        self.assertEqual(data["copyEntity"]["entity"]["startDate"], time)
        self.assertEqual(data["copyEntity"]["entity"]["endDate"], None)
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
        variables = self.data

        request = HttpRequest()
        request.user = self.anonymousUser

        result = graphql_sync(schema, { "query": self.mutation, "variables": variables }, context_value={ "request": request })

        errors = result[1]["errors"]

        self.assertEqual(errors[0]["message"], "not_logged_in")

    def test_copy_event_unauthorized(self):
        variables = self.data

        request = HttpRequest()
        request.user = self.user2

        result = graphql_sync(schema, { "query": self.mutation, "variables": variables }, context_value={ "request": request })

        errors = result[1]["errors"]

        self.assertEqual(errors[0]["message"], "could_not_save")

    def test_copy_with_attachment(self):

        variables = self.data2
    
        request = HttpRequest()
        request.user = self.admin

        result = graphql_sync(schema, { "query": self.mutation, "variables": variables }, context_value={ "request": request })

        data = result[1]["data"]
        event = Event.objects.get(id=data["copyEntity"]["entity"]["guid"])

        attachments = event.attachments_in_text()

        access = [ACCESS_TYPE.user.format(self.admin.id)]
        self.assertEqual(event.read_access[0], access[0])
        self.assertEqual(event.write_access[0], access[0])
        
        for x in attachments:
            self.assertTrue(event.attachments.filter(id=x.id).exists())
            self.assertEqual(x.owner, self.admin)
            response = attachment(request, x.id)
            self.assertEqual(response.status_code, 200)

        self.assertNotEqual(data["copyEntity"]["entity"]["richDescription"], self.eventAttachment.rich_description)

    def test_copy_with_attachment_delete(self):

        variables = self.data2
    
        request = HttpRequest()
        request.user = self.admin

        result = graphql_sync(schema, { "query": self.mutation, "variables": variables }, context_value={ "request": request })

        data = result[1]["data"]
        event = Event.objects.get(id=data["copyEntity"]["entity"]["guid"])

        attachments = event.attachments_in_text()

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

        result = graphql_sync(schema, { "query": mutation, "variables": variables }, context_value={ "request": request })

        for x in attachments:
            self.assertTrue(event.attachments.filter(id=x.id).exists())
            self.assertEqual(x.owner, self.admin)
            response = attachment(request, x.id)
            self.assertEqual(response.status_code, 200)