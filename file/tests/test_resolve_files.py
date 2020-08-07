import json
import os
from django.db import connection
from django_tenants.test.cases import FastTenantTestCase
from backend2.schema import schema
from ariadne import graphql_sync
from django.contrib.auth.models import AnonymousUser
from django.http import HttpRequest
from django.utils import timezone
from core.models import Group
from user.models import User
from file.models import FileFolder
from mixer.backend.django import mixer
from core.constances import ACCESS_TYPE
from core.lib import get_acl, access_id_to_acl
from django.utils.text import slugify
from django.core.files import File
from unittest.mock import MagicMock, patch
from django.conf import settings

class FilesCase(FastTenantTestCase):

    def setUp(self):
        self.anonymousUser = AnonymousUser()
        self.authenticatedUser = mixer.blend(User)

        self.group = mixer.blend(Group, owner=self.authenticatedUser)

        self.folder = FileFolder.objects.create(
            title="images",
            read_access=[ACCESS_TYPE.user.format(self.authenticatedUser.id)],
            write_access=[ACCESS_TYPE.user.format(self.authenticatedUser.id)],
            owner=self.authenticatedUser,
            is_folder=True
        )

        self.file1 = FileFolder.objects.create(
            owner=self.authenticatedUser,
            upload=None,
            title="file1",
            is_folder=False,
            group=None,
            parent=None,
            read_access=[ACCESS_TYPE.user.format(self.authenticatedUser.id)],
            write_access=[ACCESS_TYPE.user.format(self.authenticatedUser.id)]
        )
        self.file2 = FileFolder.objects.create(
            owner=self.authenticatedUser,
            upload=None,
            title="file2",
            is_folder=False,
            group=None,
            parent=self.folder,
            read_access=[ACCESS_TYPE.user.format(self.authenticatedUser.id)],
            write_access=[ACCESS_TYPE.user.format(self.authenticatedUser.id)]
        )

        self.file3 = FileFolder.objects.create(
            owner=self.authenticatedUser,
            upload=None,
            title="file3",
            is_folder=False,
            group=self.group,
            parent=None,
            read_access=[ACCESS_TYPE.user.format(self.authenticatedUser.id)],
            write_access=[ACCESS_TYPE.user.format(self.authenticatedUser.id)]
        )

        self.query = """
            fragment FileParts on FileFolder {
                title
            }
            query FilesQuery($containerGuid: String!) {
                files(containerGuid: $containerGuid) {
                    total
                    edges {
                        guid
                        ...FileParts
                    }
                }
            }
        """

    def tearDown(self):
        FileFolder.objects.all().delete()
        self.authenticatedUser.delete()

    def test_user_container(self):
        request = HttpRequest()
        request.user = self.authenticatedUser

        variables = {
            "containerGuid": self.authenticatedUser.guid
        }

        result = graphql_sync(schema, { "query": self.query , "variables": variables}, context_value={ 'request': request })

        self.assertTrue(result[0])

        data = result[1]["data"]

        self.assertEqual(data["files"]["total"], 2)
        self.assertEqual(data["files"]["edges"][0]["title"], "file1")


    def test_folder_container(self):
        request = HttpRequest()
        request.user = self.authenticatedUser

        variables = {
            "containerGuid": self.folder.guid
        }

        result = graphql_sync(schema, { "query": self.query , "variables": variables}, context_value={ 'request': request })

        self.assertTrue(result[0])

        data = result[1]["data"]

        self.assertEqual(data["files"]["total"], 1)
        self.assertEqual(data["files"]["edges"][0]["title"], "file2")

    def test_group_container(self):
        request = HttpRequest()
        request.user = self.authenticatedUser

        variables = {
            "containerGuid": self.group.guid
        }

        result = graphql_sync(schema, { "query": self.query , "variables": variables}, context_value={ 'request': request })

        self.assertTrue(result[0])

        data = result[1]["data"]

        self.assertEqual(data["files"]["total"], 1)
        self.assertEqual(data["files"]["edges"][0]["title"], "file3")
