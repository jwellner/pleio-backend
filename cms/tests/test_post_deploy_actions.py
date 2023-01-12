import uuid

from cms.factories import CampagnePageFactory
from cms.models import Row, Column
from core.models import Widget
from core.post_deploy.migrate_rows_cols_widgets import do_migrate_campagne_page_rows
from core.tests.helpers import PleioTenantTestCase
from user.factories import EditorFactory


class TestMigrateCampagnePageRowsTestCase(PleioTenantTestCase):
    """
    This test is not required to be maintained far after the fact.
    """

    maxDiff = None

    def setUp(self):
        super().setUp()

        self.attachment_id = str(uuid.uuid4())
        self.owner = EditorFactory()
        self.page = CampagnePageFactory(owner=self.owner)
        self.new_page = CampagnePageFactory(owner=self.owner, row_repository=[{"already": "processed"}, {"yes!": [1, 2, 3, 4, 5]}])
        self.row1 = Row.objects.create(page=self.page, is_full_width=False, position=1)
        self.row0 = Row.objects.create(page=self.page, is_full_width=True, position=0)
        self.column3 = Column.objects.create(row=self.row0, page=self.page, position=3, width=[1, 3, 1])
        self.column0 = Column.objects.create(row=self.row1, page=self.page, position=0, width=[])
        self.column1 = Column.objects.create(row=self.row0, page=self.page, position=1, width=[2, 1, 2])
        self.column2 = Column.objects.create(row=self.row1, page=self.page, position=2, width=[4, 2, 4])
        self.settings0 = [{'key': 'value', 'value': "Some value"},
                          {'key': 'richDescription', 'richDescription': self.tiptap_paragraph("Some richDescription")},
                          {'key': 'attachment', 'attachment': self.attachment_id}]
        self.settings1 = [{'key': 'devalue', 'value': "Some other value"},
                          {'key': 'richDescription', 'richDescription': self.tiptap_paragraph("Some other richDescription")}]
        self.settings2 = [{"key": "title", "value": "Some title"}]
        self.widget2 = Widget.objects.create(column=self.column3, page=self.page, position=2, type="demo0", settings=self.settings2)
        self.widget1 = Widget.objects.create(column=self.column0, page=self.page, position=1, type="demo1", settings=self.settings1)
        self.widget0 = Widget.objects.create(column=self.column0, page=self.page, position=0, type="demo2", settings=self.settings0)
        self.widget5 = Widget.objects.create(column=self.column0, page=self.page, position=5, type="demo3", settings=[])
        self.widget4 = Widget.objects.create(column=self.column1, page=self.page, position=4, type="demo4", settings=[])
        self.widget3 = Widget.objects.create(column=self.column2, page=self.page, position=3, type="demo5", settings=[])

    def test_migration_method(self):
        # given
        new_before = self.new_page.row_repository
        before = self.page.row_repository
        expected_row_spec = [
            {"isFullWidth": True,
             "columns": [{"width": [2, 1, 2],
                          "widgets": [{"type": "demo4",
                                       'settings': []}]},
                         {"width": [1, 3, 1],
                          "widgets": [{"type": "demo0",
                                       'settings': [{'key': 'title',
                                                     'value': 'Some title',
                                                     'richDescription': None,
                                                     'attachmentId': None}]
                                       }]
                          }]
             },
            {"isFullWidth": False,
             "columns": [{"width": [],
                          "widgets": [{"type": "demo2",
                                       "settings": [{'key': 'value',
                                                     'value': 'Some value',
                                                     'richDescription': None,
                                                     'attachmentId': None},
                                                    {'key': 'richDescription',
                                                     'value': None,
                                                     'richDescription': self.tiptap_paragraph("Some richDescription"),
                                                     'attachmentId': None},
                                                    {'key': 'attachment',
                                                     'value': None,
                                                     'richDescription': None,
                                                     'attachmentId': self.attachment_id}
                                                    ]},
                                      {"type": "demo1",
                                       "settings": [{'key': 'devalue',
                                                     'value': "Some other value",
                                                     'richDescription': None,
                                                     'attachmentId': None},
                                                    {'key': 'richDescription',
                                                     'value': None,
                                                     'richDescription': self.tiptap_paragraph("Some other richDescription"),
                                                     'attachmentId': None}
                                                    ]},
                                      {"type": "demo3",
                                       "settings": []}
                                      ]},
                         {"width": [4, 2, 4],
                          "widgets": [{"type": "demo5",
                                       "settings": []
                                       }]
                          }]
             }
        ]

        # when
        do_migrate_campagne_page_rows(self.new_page)
        do_migrate_campagne_page_rows(self.page)
        self.new_page.refresh_from_db()
        self.page.refresh_from_db()

        # then
        self.assertEqual(self.new_page.row_repository, new_before)
        self.assertNotEqual(self.page.row_repository, before)
        self.assertDictEqual({'d': self.page.row_repository}, {'d': expected_row_spec})
