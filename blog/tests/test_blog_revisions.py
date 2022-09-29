from blog.factories import BlogFactory
from core.tests.helpers.revision_template import RevisionTemplate
from user.factories import UserFactory


class TestBlogRevisionsTestCase(RevisionTemplate.BaseTestCase):
    useAbstract = True
    useIsRecommended = True
    useIsFeatured = True
    useFeatured = True
    useWriteAccess = True
    useTimeCreated = True
    useArchiveDeletePublish = True
    useGroupGuid = True
    useOwnerGuid = True
    useSuggestedItems = True

    def build_entity(self, owner):
        return BlogFactory(owner=owner,
                           title="Default title",
                           rich_description=self.tiptap_paragraph("Default rich description"),
                           abstract='Default abstract',
                           is_recommended=False,
                           is_featured=False)

    def build_owner(self):
        return UserFactory()
