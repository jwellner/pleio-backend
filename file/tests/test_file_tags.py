from django.core.files.base import ContentFile
from django.test import override_settings

from core.factories import GroupFactory
from core.tests.helpers.tags_testcase import Template
from file.models import FileFolder
from user.models import User


class TestFileTagsTestCase(Template.TagsTestCaseTemplate):
    # Overrides:
    graphql_label = 'File'
    graphql_update_mutation = 'editFileFolder'
    graphql_update_input = 'editFileFolderInput'
    graphql_add_mutation = 'addFile'
    graphql_add_input = 'addFileInput'
    model = FileFolder

    _container = None

    variables_add = {'input': {
        'file': 'test.gif'
    }}

    @override_settings(CLAMAV_HOST='')
    def setUp(self):
        super().setUp()

    @property
    def container(self):
        if not self._container:
            # required by baseclass
            self._container = GroupFactory(owner=self.owner)
        return self._container

    def article_factory(self, owner: User, **kwargs):
        kwargs.setdefault('type', FileFolder.Types.FILE)
        kwargs.setdefault('upload', ContentFile("test", "test.txt"))
        kwargs.setdefault('group', self.container)
        return super().article_factory(owner, **kwargs)

    include_site_search = True
    include_entity_search = True


class TestFolderTagsTestCase(Template.TagsTestCaseTemplate):
    # Overrides:
    graphql_label = 'Folder'
    graphql_update_mutation = 'editFileFolder'
    graphql_update_input = 'editFileFolderInput'
    model = FileFolder

    _container = None

    variables_add = {'input': {
        'title': 'Some folder',
        'subtype': 'folder'
    }}

    @property
    def container(self):
        if not self._container:
            # required by baseclass
            self._container = GroupFactory(owner=self.owner)
        return self._container

    def article_factory(self, owner: User, **kwargs):
        kwargs.setdefault('type', FileFolder.Types.FOLDER)
        kwargs.setdefault('title', 'Some folder')
        kwargs.setdefault('group', self.container)
        return super().article_factory(owner, **kwargs)

    include_site_search = True
    include_entity_search = True
