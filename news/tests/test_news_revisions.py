from core.tests.helpers.revision_template import RevisionTemplate
from news.factories import NewsFactory
from user.factories import EditorFactory


class TestNewsRevisionsTestCase(RevisionTemplate.BaseTestCase):
    useAbstract = True
    useIsFeatured = True
    useFeatured = True
    useWriteAccess = True
    useTimeCreated = True
    useArchiveDeletePublish = True
    useOwnerGuid = True
    useSuggestedItems = True
    useSource = True

    def build_entity(self, owner):
        return NewsFactory(owner=owner,
                           title="Default title",
                           rich_description=self.tiptap_paragraph("Default rich description"),
                           abstract='Default abstract',
                           source="Initial source",
                           is_recommended=False,
                           is_featured=False)

    def build_owner(self):
        return EditorFactory()
