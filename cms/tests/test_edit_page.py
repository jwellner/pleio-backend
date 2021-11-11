from django.db import connection
from django_tenants.test.cases import FastTenantTestCase
from backend2.schema import schema
from ariadne import graphql_sync
import json
from django.contrib.auth.models import AnonymousUser
from django.http import HttpRequest
from core.models import Group
from user.models import User
from core.constances import ACCESS_TYPE, USER_ROLES
from mixer.backend.django import mixer
from graphql import GraphQLError
from cms.models import Page

class EditPageTestCase(FastTenantTestCase):

    def setUp(self):
        self.anonymousUser = AnonymousUser()
        self.user = mixer.blend(User)
        self.admin = mixer.blend(User, roles=[USER_ROLES.ADMIN])
        self.editor = mixer.blend(User, roles=[USER_ROLES.EDITOR])
        self.page = mixer.blend(Page,
                                owner=self.user,
                                read_access=[ACCESS_TYPE.public],
                                write_access=[ACCESS_TYPE.user.format(self.user.id)]
                                )

    def test_edit_page_by_admin(self):

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
                "richDescription": '{"blocks":[{"key":"6sb64","text":"test","type":"unstyled","depth":0,"inlineStyleRanges":[],"entityRanges":[],"data":{}}],"entityMap":{}}'

            }
        }

        request = HttpRequest()
        request.user = self.admin

        result = graphql_sync(schema, {"query": mutation, "variables": variables }, context_value={ "request": request })

        data = result[1]["data"]

        self.assertEqual(data["editPage"]["entity"]["title"], "test")
        self.assertEqual(data["editPage"]["entity"]["richDescription"], '{"blocks":[{"key":"6sb64","text":"test","type":"unstyled","depth":0,"inlineStyleRanges":[],"entityRanges":[],"data":{}}],"entityMap":{}}')
        self.assertEqual(data["editPage"]["entity"]["tags"], [])
        self.assertEqual(data["editPage"]["entity"]["accessId"], 1)
        self.assertEqual(data["editPage"]["entity"]["canEdit"], True)
        self.assertEqual(data["editPage"]["entity"]["parent"], None)

    def test_edit_page_by_editor(self):

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
                "richDescription": '{"blocks":[{"key":"6sb64","text":"test","type":"unstyled","depth":0,"inlineStyleRanges":[],"entityRanges":[],"data":{}}],"entityMap":{}}'

            }
        }

        request = HttpRequest()
        request.user = self.editor

        result = graphql_sync(schema, {"query": mutation, "variables": variables }, context_value={ "request": request })

        data = result[1]["data"]

        self.assertEqual(data["editPage"]["entity"]["title"], "test")
        self.assertEqual(data["editPage"]["entity"]["richDescription"], '{"blocks":[{"key":"6sb64","text":"test","type":"unstyled","depth":0,"inlineStyleRanges":[],"entityRanges":[],"data":{}}],"entityMap":{}}')
        self.assertEqual(data["editPage"]["entity"]["tags"], [])
        self.assertEqual(data["editPage"]["entity"]["accessId"], 1)
        self.assertEqual(data["editPage"]["entity"]["canEdit"], True)
        self.assertEqual(data["editPage"]["entity"]["parent"], None)

    def test_edit_page_by_anonymous(self):

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
                "richDescription": '{"blocks":[{"key":"6sb64","text":"test","type":"unstyled","depth":0,"inlineStyleRanges":[],"entityRanges":[],"data":{}}],"entityMap":{}}'

            }
        }

        request = HttpRequest()
        request.user = self.anonymousUser

        result = graphql_sync(schema, {"query": mutation, "variables": variables }, context_value={ "request": request })

        errors = result[1]["errors"]

        self.assertEqual(errors[0]["message"], "not_logged_in")

    def test_edit_page_by_user(self):

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
                "richDescription": '{"blocks":[{"key":"6sb64","text":"test","type":"unstyled","depth":0,"inlineStyleRanges":[],"entityRanges":[],"data":{}}],"entityMap":{}}'

            }
        }

        request = HttpRequest()
        request.user = self.user

        result = graphql_sync(schema, {"query": mutation, "variables": variables }, context_value={ "request": request })

        errors = result[1]["errors"]

        self.assertEqual(errors[0]["message"], "could_not_save")
