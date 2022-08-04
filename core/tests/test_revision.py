from mixer.backend.django import mixer
from core.models import Revision
from blog.models import Blog
from core.tests.helpers import PleioTenantTestCase
from user.models import User
from core.constances import ACCESS_TYPE

class RevisionTestCase(PleioTenantTestCase):

    def setUp(self):
        super(RevisionTestCase, self).setUp()

        self.authenticatedUser = mixer.blend(User)
        self.blog = Blog.objects.create(
            title="Test public event",
            rich_description="JSON to string",
            read_access=[ACCESS_TYPE.public],
            write_access=[ACCESS_TYPE.user.format(self.authenticatedUser.id)],
            owner=self.authenticatedUser
        )
        self.blog2 = Blog.objects.create(
            title="Test public event",
            rich_description="JSON to string",
            read_access=[ACCESS_TYPE.public],
            write_access=[ACCESS_TYPE.user.format(self.authenticatedUser.id)],
            owner=self.authenticatedUser
        )
        self.revision1 = mixer.blend(Revision,
            object=self.blog2,
            content={"richDescription": "Content1"},
            description="Version 1"
        )
        self.revision2 = mixer.blend(Revision,
            object=self.blog2,
            content={"richDescription": "Content2"},
            description="Version 2"
        )
        self.blog2.last_revision = self.revision2
        self.blog2.save()

        self.mutation = """
            mutation ($input: publishContentInput!) {
                publishContent(input: $input) {
                    success
                }
            }
        """
    
    def test_blog_revisions(self):

        mutation = """
            mutation ($input: editEntityInput!, $draft: Boolean) {
                editEntity(input: $input, draft: $draft) {
                    entity {
                    guid
                    status
                    }
                }
            }
        """
        variables1 = {
            "input": {
                "guid": self.blog.guid,
                "richDescription": "description1"
            },
            "draft": True,
        }
        variables2 = {
            "input": {
                "guid": self.blog.guid,
                "richDescription": "description2"
            },
            "draft": True,
        }
        variables3 = {
            "input": {
                "guid": self.blog.guid,
                "description": "v1"
            },
        }
        variables4 = {
            "input": {
                "guid": self.blog.guid,
                "description": "v2"
            },
        }

        self.graphql_client.force_login(self.authenticatedUser)
        self.graphql_client.post(mutation, variables1)
        self.graphql_client.post(self.mutation, variables3)

        self.blog.refresh_from_db()
        self.assertEqual(self.blog.rich_description, variables1["input"]["richDescription"])

        result = self.graphql_client.post(mutation, variables2)
        self.graphql_client.post(self.mutation, variables4)

        entity = result["data"]["editEntity"]["entity"]

        revisions = Revision.objects.filter(object=entity["guid"])
        self.assertEqual(len(revisions), 2)
        self.assertEqual(revisions[0].description, variables3["input"]["description"])
        self.assertEqual(revisions[0].content.get("richDescription"), variables1["input"]["richDescription"])
        self.assertEqual(revisions[1].description, variables4["input"]["description"])
        self.assertEqual(revisions[1].content.get("richDescription"), variables2["input"]["richDescription"])

    def test_revert_to_revision(self):
        variables1 = {
            "input": {
                "guid": self.blog2.guid,
                "description": "v2"
            },
            "draft": True,
        }
        variables2 = {
            "input": {
                "guid": self.blog2.guid,
                "revisionGuid": str(self.revision1.id),
                "description": "v1"
            },
            "draft": True,
        }

        self.graphql_client.force_login(self.authenticatedUser)
        result = self.graphql_client.post(self.mutation, variables1)

        self.assertTrue(result["data"]["publishContent"]["success"])

        self.blog2.refresh_from_db()
        self.assertEqual(self.blog2.rich_description, self.revision2.content.get("richDescription"))

        result = self.graphql_client.post(self.mutation, variables2)

        self.blog2.refresh_from_db()
        self.revision1.refresh_from_db()
        self.revision2.refresh_from_db()
        self.assertEqual(self.blog2.rich_description, self.revision1.content.get("richDescription"))
        self.assertEqual(self.revision1.description, variables2["input"]["description"])
        self.assertEqual(self.revision2.description, variables1["input"]["description"])
