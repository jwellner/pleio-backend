from django.db import connection
from django_tenants.test.cases import FastTenantTestCase
from backend2.schema import schema
from ariadne import graphql_sync
import json
from django.contrib.auth.models import AnonymousUser
from django.http import HttpRequest
from core.models import Group, User
from core.constances import ACCESS_TYPE
from mixer.backend.django import mixer
from graphql import GraphQLError
from cms.models import Page

class EditPageTestCase(FastTenantTestCase):

    def setUp(self):
        self.anonymousUser = AnonymousUser()
        self.user = mixer.blend(User)
        self.page = mixer.blend(Page,
                                owner=self.user,
                                read_access=[ACCESS_TYPE.public],
                                write_access=[ACCESS_TYPE.user.format(self.user.id)]
                                )

    def test_edit_page(self):

        mutation = """
            mutation EditPage($input: editPageInput!) {
                editPage(input: $input) {
                    entity {
                    guid
                    ...PageDetailFragment
                    __typename
                    }
                    __typename
                }
            }

            fragment PageDetailFragment on Page {
                pageType
                canEdit
                title
                url
                description
                richDescription
                tags
                parent {
                    guid
                }
                accessId
            }
        """
        variables = {
            "input": {
                "guid": self.page.guid,
                "title": "test",
                "accessId": 1,
                "tags": [],
                "description": "test",
                "richDescription": '{"blocks":[{"key":"6sb64","text":"test","type":"unstyled","depth":0,"inlineStyleRanges":[],"entityRanges":[],"data":{}}],"entityMap":{}}'

            }
        }

        request = HttpRequest()
        request.user = self.user

        result = graphql_sync(schema, {"query": mutation, "variables": variables }, context_value=request)

        data = result[1]["data"]

        self.assertEqual(data["editPage"]["entity"]["title"], "test")
        self.assertEqual(data["editPage"]["entity"]["description"], "test")
        self.assertEqual(data["editPage"]["entity"]["richDescription"], '{"blocks":[{"key":"6sb64","text":"test","type":"unstyled","depth":0,"inlineStyleRanges":[],"entityRanges":[],"data":{}}],"entityMap":{}}')
        self.assertEqual(data["editPage"]["entity"]["tags"], [])
        self.assertEqual(data["editPage"]["entity"]["accessId"], 1)
        self.assertEqual(data["editPage"]["entity"]["canEdit"], True)
        self.assertEqual(data["editPage"]["entity"]["parent"], None)
