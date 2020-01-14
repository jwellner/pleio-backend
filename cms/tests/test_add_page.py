from django.db import connection
from django_tenants.test.cases import FastTenantTestCase
from backend2.schema import schema
from ariadne import graphql_sync
import json
from django.contrib.auth.models import AnonymousUser
from django.http import HttpRequest
from core.models import Group, User
from mixer.backend.django import mixer
from graphql import GraphQLError
from cms.models import Page

class AddPageTestCase(FastTenantTestCase):

    def setUp(self):
        self.anonymousUser = AnonymousUser()
        self.user = mixer.blend(User)
        self.admin = mixer.blend(User, is_admin=True)
        self.page = mixer.blend(Page)

    def test_add_campaign_page_by_admin(self):

        mutation = """
            mutation AddPage($input: addPageInput!) {
                addPage(input: $input) {
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
                "title": "test",
                "pageType": "campagne",
                "accessId": 1,
                "tags": [],
                "description": "test",
                "richDescription": '{"blocks":[{"key":"6sb64","text":"test","type":"unstyled","depth":0,"inlineStyleRanges":[],"entityRanges":[],"data":{}}],"entityMap":{}}'

            }
        }

        request = HttpRequest()
        request.user = self.admin

        result = graphql_sync(schema, {"query": mutation, "variables": variables }, context_value=request)
        data = result[1]["data"]

        self.assertEqual(data["addPage"]["entity"]["title"], "test")
        self.assertEqual(data["addPage"]["entity"]["description"], "test")
        self.assertEqual(data["addPage"]["entity"]["richDescription"], '{"blocks":[{"key":"6sb64","text":"test","type":"unstyled","depth":0,"inlineStyleRanges":[],"entityRanges":[],"data":{}}],"entityMap":{}}')
        self.assertEqual(data["addPage"]["entity"]["pageType"], "campagne")
        self.assertEqual(data["addPage"]["entity"]["tags"], [])
        self.assertEqual(data["addPage"]["entity"]["accessId"], 1)
        self.assertEqual(data["addPage"]["entity"]["canEdit"], True)
        self.assertEqual(data["addPage"]["entity"]["parent"], None)


    def test_add_text_sub_page_by_admin(self):

        mutation = """
            mutation AddPage($input: addPageInput!) {
                addPage(input: $input) {
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
                "title": "text",
                "pageType": "text",
                "containerGuid": self.page.guid,
                "accessId": 1,
                "tags": [],
                "description": "text",
                "richDescription": '{"blocks":[{"key":"6sb64","text":"test","type":"unstyled","depth":0,"inlineStyleRanges":[],"entityRanges":[],"data":{}}],"entityMap":{}}'

            }
        }

        request = HttpRequest()
        request.user = self.admin

        result = graphql_sync(schema, {"query": mutation, "variables": variables }, context_value=request)
        data = result[1]["data"]

        self.assertEqual(data["addPage"]["entity"]["title"], "text")
        self.assertEqual(data["addPage"]["entity"]["description"], "text")
        self.assertEqual(data["addPage"]["entity"]["richDescription"], '{"blocks":[{"key":"6sb64","text":"test","type":"unstyled","depth":0,"inlineStyleRanges":[],"entityRanges":[],"data":{}}],"entityMap":{}}')
        self.assertEqual(data["addPage"]["entity"]["pageType"], "text")
        self.assertEqual(data["addPage"]["entity"]["tags"], [])
        self.assertEqual(data["addPage"]["entity"]["accessId"], 1)
        self.assertEqual(data["addPage"]["entity"]["canEdit"], True)
        self.assertEqual(data["addPage"]["entity"]["parent"]["guid"], self.page.guid)


    def test_add_campaign_page_by_anonymous(self):

        mutation = """
            mutation AddPage($input: addPageInput!) {
                addPage(input: $input) {
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
                "title": "test",
                "pageType": "campagne",
                "accessId": 1,
                "tags": [],
                "description": "test",
                "richDescription": '{"blocks":[{"key":"6sb64","text":"test","type":"unstyled","depth":0,"inlineStyleRanges":[],"entityRanges":[],"data":{}}],"entityMap":{}}'

            }
        }

        request = HttpRequest()
        request.user = self.anonymousUser

        result = graphql_sync(schema, {"query": mutation, "variables": variables }, context_value=request)

        errors = result[1]["errors"]

        self.assertEqual(errors[0]["message"], "not_logged_in")


    def test_add_campaign_page_by_user(self):

        mutation = """
            mutation AddPage($input: addPageInput!) {
                addPage(input: $input) {
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
                "title": "test",
                "pageType": "campagne",
                "accessId": 1,
                "tags": [],
                "description": "test",
                "richDescription": '{"blocks":[{"key":"6sb64","text":"test","type":"unstyled","depth":0,"inlineStyleRanges":[],"entityRanges":[],"data":{}}],"entityMap":{}}'

            }
        }

        request = HttpRequest()
        request.user = self.user

        result = graphql_sync(schema, {"query": mutation, "variables": variables }, context_value=request)

        errors = result[1]["errors"]

        self.assertEqual(errors[0]["message"], "could_not_save")
