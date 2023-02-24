from core.lib import datetime_utciso
from core.models import Entity
from core.tests.helpers import PleioTenantTestCase
from user.factories import UserFactory


class EntityModelTestCase(PleioTenantTestCase):

    def setUp(self):
        super().setUp()

        self.owner = UserFactory()
        self.entity = Entity.objects.create(owner=self.owner)

    def test_serialize_entity(self):
        self.assertEqual(self.entity.serialize(), {
            "accessId": 0,
            "writeAccessId": 0,
            "groupGuid": '',
            "isFeatured": False,
            "isPinned": False,
            "isRecommended": False,
            "ownerGuid": self.owner.guid,
            "scheduleArchiveEntity": '',
            "scheduleDeleteEntity": '',
            "statusPublished": 'published',
            "suggestedItems": [],
            "tagCategories": [],
            "tags": [],
            "timeCreated": datetime_utciso(self.entity.created_at),
            "timePublished": datetime_utciso(self.entity.published),
        })
