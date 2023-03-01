from blog.factories import BlogFactory
from core.lib import datetime_utciso
from core.models import Comment
from core.tests.helpers import PleioTenantTestCase
from user.factories import UserFactory


class TestNewsModelTestCase(PleioTenantTestCase):
    CONTENT = "Demo wiki content"
    ANONYMOUS_NAME = "John Doe"
    ANONYMOUS_EMAIL = "jd@example.com"

    maxDiff = None

    def setUp(self):
        super().setUp()

        self.owner = UserFactory()
        self.parent = BlogFactory(owner=self.owner)
        self.entity = Comment.objects.create(owner=self.owner,
                                             rich_description=self.CONTENT,
                                             container=self.parent)

    def tearDown(self):
        self.entity.delete()
        self.parent.delete()
        self.owner.delete()

        super().tearDown()

    def test_serialize_authenticated(self):
        serialized = self.entity.serialize()

        self.assertEqual(serialized, {"containerGuid": self.parent.guid,
                                      "ownerGuid": self.owner.guid,
                                      "email": self.owner.email,
                                      "name": self.owner.name,
                                      "richDescription": self.CONTENT,
                                      "timeCreated": datetime_utciso(self.entity.created_at)})

    def test_serialize_anonymous(self):
        self.entity.owner = None
        self.entity.name = self.ANONYMOUS_NAME
        self.entity.email = self.ANONYMOUS_EMAIL
        self.entity.save()
        serialized = self.entity.serialize()

        self.assertEqual(serialized, {"containerGuid": self.parent.guid,
                                      "ownerGuid": '',
                                      "email": self.ANONYMOUS_EMAIL,
                                      "name": self.ANONYMOUS_NAME,
                                      "richDescription": self.CONTENT,
                                      "timeCreated": datetime_utciso(self.entity.created_at)})

    def test_map_rich_text_fields(self):
        before = self.entity.serialize()
        expected = self.entity.serialize()
        expected['richDescription'] = f"new {self.CONTENT}"

        self.entity.map_rich_text_fields(lambda s: "new {}".format(s))
        after = self.entity.serialize()

        self.assertNotEqual(after, before)
        self.assertEqual(after, expected)
