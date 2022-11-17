from mixer.backend.django import mixer

from blog.models import Blog
from core.tests.helpers import PleioTenantTestCase
from user.models import User
from core.models import Revision
from core.constances import ACCESS_TYPE


class RevisionQueryTestCase(PleioTenantTestCase):

    def setUp(self):
        super().setUp()
        self.authenticatedUser1 = mixer.blend(User)
        self.authenticatedUser2 = mixer.blend(User)

        self.blog = mixer.blend(Blog, 
            write_access=[ACCESS_TYPE.user.format(self.authenticatedUser1.id),
                          ACCESS_TYPE.user.format(self.authenticatedUser2.id)]
        )
        self.revision1 = mixer.blend(Revision,
            _container=self.blog,
            content={"richDescription": "Content1"},
            description="Version 1"
        )
        self.revision2 = mixer.blend(Revision,
            _container=self.blog,
            content={"richDescription": "Content2"},
            description="Version 2"
        )
        self.revision3 = mixer.blend(Revision,
            _container=self.blog,
            content={"richDescription": "Content3"},
            description="Version 3"
        )

        self.mutation = """
            fragment RevisionParts on Revision {
                description
                content {
                    richDescription
                }
            }
            query testRevisions ($containerGuid: String!) {
                revisions(containerGuid: $containerGuid) {
                    total
                    edges {
                        ...RevisionParts
                    }
                }
            } 
        """

        self.variables = {
            "containerGuid": self.blog.guid
        }
        

    def test_blog_all_revisions(self):
        self.graphql_client.force_login(self.authenticatedUser1)
        result = self.graphql_client.post(self.mutation, self.variables)
        edges = result["data"]["revisions"]["edges"]

        self.assertEqual(len(edges), 3)
        self.assertEqual(result["data"]["revisions"]["total"], 3)
        self.assertEqual(edges[0]["description"], self.revision3.description)
        self.assertEqual(edges[1]["description"], self.revision2.description)
        self.assertEqual(edges[2]["description"], self.revision1.description)
        self.assertEqual(edges[0]["content"]["richDescription"], self.revision3.content.get("richDescription"))
        self.assertEqual(edges[1]["content"]["richDescription"], self.revision2.content.get("richDescription"))
        self.assertEqual(edges[2]["content"]["richDescription"], self.revision1.content.get("richDescription"))
