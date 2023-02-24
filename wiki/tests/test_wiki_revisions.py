from wiki.factories import WikiFactory
from core.tests.helpers.revision_template import RevisionTemplate
from user.factories import UserFactory


class TestWikiRevisionsTestCase(RevisionTemplate.BaseTestCase):
    useAbstract = True
    useIsFeatured = True
    useFeatured = True
    useWriteAccess = True
    useTimeCreated = True
    useArchiveDeletePublish = True
    useGroupGuid = True
    useOwnerGuid = True
    useParent = True

    def build_entity(self, owner):
        return WikiFactory(owner=owner,
                           title="Default title",
                           rich_description=self.tiptap_paragraph("Default rich description"),
                           abstract='Default abstract',
                           is_recommended=False,
                           is_featured=False)

    def build_owner(self):
        return UserFactory()

    def localSetUp(self):
        super().localSetUp()
        self.reference_data = {
            'title': self.entity.title,
            'richDescription': self.entity.rich_description,
        }
