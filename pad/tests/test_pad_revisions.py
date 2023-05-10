from file.factories import PadFactory
from core.tests.helpers.revision_template import RevisionTemplate
from user.factories import UserFactory


class TestPadRevisionsTestCase(RevisionTemplate.BaseTestCase):
    editMutation = 'editPad'
    editMutationInput = 'editPadInput'

    useWriteAccess = True

    def build_entity(self, owner):
        return PadFactory(owner=owner,
                          title="Default title",
                          rich_description=self.tiptap_paragraph("Default rich description"))

    def build_owner(self):
        return UserFactory()

    def localSetUp(self):
        super().localSetUp()
        self.reference_data = {
            'title': self.entity.title,
            'richDescription': self.entity.rich_description,
        }
