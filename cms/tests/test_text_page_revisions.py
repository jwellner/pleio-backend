from cms.factories import TextPageFactory
from core.lib import get_access_id
from core.tests.helpers.revision_template import RevisionTemplate
from user.factories import EditorFactory


class TestTextPageRevisionsTestCase(RevisionTemplate.BaseTestCase):
    editMutation = 'editPage'
    editMutationInput = 'editPageInput'

    def build_owner(self):
        return EditorFactory()

    def build_entity(self, owner):
        return TextPageFactory(owner=owner,
                               rich_description=self.tiptap_paragraph("Original rich description."))

    def default_variables(self):
        return {
            'title': self.entity.title,
            'richDescription': self.entity.rich_description,
            'tags': [],
            'accessId': get_access_id(self.entity.read_access),
        }

    def localSetUp(self):
        super().localSetUp()
        self.reference_data = {
            'title': self.entity.title,
            'richDescription': self.entity.rich_description,
        }
