import json
from unittest import mock

from django.utils import timezone
from django.utils.timezone import now

from core import config
from core.tests.helpers import PleioTenantTestCase
from external_content.api_handlers.datahub import ApiHandler, TagCollector
from external_content.factories import ExternalContentSourceFactory, ExternalContentFactory
from external_content.models import ExternalContent


class TestHandlerDatahubTestCase(PleioTenantTestCase):

    def setUp(self):
        super().setUp()
        self.API_URL = 'https://test.datahub.pleio.wonderbit.com/api/v1/'
        self.FRONTEND_URL = 'https://test.datahub.pleio.wonderbit.com/en/explorer/'
        self.BATCH_SIZE = 50
        self.source = ExternalContentSourceFactory(
            name="Datahub",
            settings={
                'apiUrl': self.API_URL,
                'frontendUrl': self.FRONTEND_URL,
                'batchSize': self.BATCH_SIZE,
            })
        self.handler = ApiHandler(self.source)
        self.override_config(DATAHUB_EXTERNAL_CONTENT_ENABLED=True)

    def tearDown(self):
        self.source.delete()
        super().tearDown()

    def create_json_response_from_file(self, path):
        with open(self.relative_path(__file__, path), 'r') as fh:
            content = json.load(fh)
        response = mock.MagicMock()
        response.ok = True
        response.json.return_value = content
        return response

    @mock.patch("external_content.api_handlers.datahub.ApiHandler.should_do_full_sync")
    @mock.patch("external_content.api_handlers.datahub.ApiHandler.full_sync")
    def test_run_with_datahub_external_content_disabled(self, full_sync, should_do_full_sync):
        should_do_full_sync.return_value = True
        self.override_config(DATAHUB_EXTERNAL_CONTENT_ENABLED=False)
        self.handler.pull()

        self.assertFalse(should_do_full_sync.called)
        self.assertFalse(full_sync.called)

    @mock.patch("external_content.api_handlers.datahub.requests.get")
    def test_pull_study_zones(self, requests_get):
        requests_get.return_value = self.create_json_response_from_file(['assets', 'datahub', 'studies.json'])
        self.handler.pull_study_zones()
        self.assertDictEqual(self.handler.study_zones, {
            'Geotechnical investigations HKN': ['Ancillary', 'Hollandse Kust (noord)'],
            'Study 2': ['Doordewind'],
            'Study 3': ['Ancillary']
        })
        url = requests_get.call_args.args[0]
        query = requests_get.call_args.args[1]
        self.assertEqual(self.source.settings['batchSize'], 50)
        self.assertTrue(url.startswith('http'))
        self.assertTrue(url.startswith(self.source.settings['apiUrl']))
        self.assertEqual(query['limit'], self.source.settings['batchSize'])
        self.assertEqual(query['format'], 'json')

    @mock.patch("external_content.api_handlers.datahub.requests.get")
    @mock.patch("external_content.api_handlers.datahub.ApiHandler.import_file")
    def test_pull_files(self, import_file, requests_get):
        self.handler.study_zones = {
            'Geotechnical investigations HKN': ['Ancillary', 'Hollandse Kust (noord)'],
            'Study 2': ['Doordewind'],
            'Study 3': ['Ancillary']
        }
        requests_get.side_effect = [
            self.create_json_response_from_file(['assets', 'datahub', 'files1.json']),
            self.create_json_response_from_file(['assets', 'datahub', 'files2.json']),
        ]

        self.handler.pull_files()
        self.assertEqual(requests_get.call_count, 2)
        self.assertEqual(import_file.call_count, 40)

    @mock.patch("external_content.api_handlers.datahub.requests.get")
    def test_pull_files_since(self, requests_get):
        date_since = timezone.now()
        response = mock.MagicMock()
        response.json.return_value = {}
        response.ok = True
        requests_get.return_value = response

        self.handler.pull_files(date_since)

        self.assertEqual(requests_get.call_args.args,
                         ("%sfiles" % self.API_URL, {
                             "format": "json",
                             "limit": self.BATCH_SIZE,
                             "modified_after": date_since.isoformat()
                         }))

    @mock.patch("external_content.api_handlers.datahub.ApiHandler.full_sync")
    @mock.patch("external_content.api_handlers.datahub.ApiHandler.update")
    def test_full_sync_not_called(self, update, full_sync):
        self.source.last_full_sync = timezone.now()
        self.source.last_update_sync = timezone.now()
        self.source.save()

        self.handler.pull()

        self.assertEqual(update.call_count, 0)
        self.assertEqual(full_sync.call_count, 0)

    @mock.patch("external_content.api_handlers.datahub.ApiHandler.full_sync")
    @mock.patch("external_content.api_handlers.datahub.ApiHandler.update")
    def test_full_sync_called(self, update, full_sync):
        self.source.last_full_sync = timezone.now() - timezone.timedelta(days=1, minutes=5)
        self.source.last_update_sync = timezone.now() - timezone.timedelta(hours=2)
        self.source.save()

        self.handler.pull()

        self.assertEqual(update.call_count, 0)
        self.assertEqual(full_sync.call_count, 1)

    @mock.patch("external_content.api_handlers.datahub.ApiHandler.full_sync")
    @mock.patch("external_content.api_handlers.datahub.ApiHandler.update")
    def test_update_called(self, update, full_sync):
        self.source.last_full_sync = timezone.now()
        self.source.last_update_sync = timezone.now() - timezone.timedelta(hours=2)
        self.source.save()

        self.handler.pull()

        self.assertEqual(update.call_count, 1)
        self.assertEqual(full_sync.call_count, 0)

    @mock.patch("external_content.api_handlers.datahub.ApiHandler.pull_study_zones")
    @mock.patch("external_content.api_handlers.datahub.ApiHandler.pull_files")
    @mock.patch("external_content.api_handlers.datahub.ApiHandler.apply_tags")
    @mock.patch("external_content.api_handlers.datahub.ApiHandler.cleanup_files")
    def test_full_sync_call_sequence(self, cleanup_files, apply_tags, pull_files, pull_study_zones):
        self.handler.full_sync()

        self.assertTrue(pull_study_zones.called)
        self.assertTrue(pull_files.called)
        self.assertTrue(apply_tags.called)
        self.assertTrue(cleanup_files.called)

    @mock.patch("external_content.api_handlers.datahub.ApiHandler.pull_study_zones")
    @mock.patch("external_content.api_handlers.datahub.ApiHandler.pull_files")
    @mock.patch("external_content.api_handlers.datahub.ApiHandler.apply_tags")
    @mock.patch("external_content.api_handlers.datahub.ApiHandler.cleanup_files")
    def test_update_call_sequence(self, cleanup_files, apply_tags, pull_files, pull_study_zones):
        update_time = timezone.now()
        self.handler.update(update_time)

        self.assertTrue(pull_study_zones.called)
        self.assertTrue(pull_files.called)
        self.assertEqual(pull_files.call_args.args[0], update_time)
        self.assertFalse(apply_tags.called)
        self.assertFalse(cleanup_files.called)


class TestHandlerDatahubImportFileTestCase(PleioTenantTestCase):

    def setUp(self):
        super().setUp()
        self.source = ExternalContentSourceFactory(settings={
            'apiUrl': 'https://test.datahub.pleio.wonderbit.com/api/v1/',
            'frontendUrl': 'https://test.datahub.pleio.wonderbit.com/en/explorer/',
            'batchSize': 50,
        })
        self.handler = ApiHandler(self.source)
        self.handler.study_zones = {
            'Geotechnical investigations HKN': ['Ancillary', 'Hollandse Kust (noord)'],
            'Study 2': ['Doordewind'],
            'Study 3': ['Ancillary']
        }

        with open(self.relative_path(__file__, ['assets', 'datahub', 'files1.json']), 'r') as fh:
            self.files = json.load(fh)

    def tearDown(self):
        self.source.delete()
        super().tearDown()

    def test_import_minimal_file_record(self):
        with self.assertRaises(KeyError):
            self.handler.import_file({})

        with self.assertRaises(KeyError):
            self.handler.import_file({"id": "1"})

        with self.assertRaises(KeyError):
            self.handler.import_file({"id": "1",
                                      "name": "First file"})

        with self.assertRaises(KeyError):
            self.handler.import_file({"id": "1",
                                      "name": "First file",
                                      "date_created": str(now())})

        self.handler.import_file({"id": "1",
                                  "name": "First file",
                                  "description": "some description",
                                  "date_created": str(now()),
                                  "date_modified": str(now())})
        self.assertDictEqual({**self.handler.tag_categories}, {})

    def test_import_file_record(self):
        # Given
        expected_categories = {
            "chapter": TagCollector('General Information'),
            "classification": TagCollector('Raw data'),
            "extension": TagCollector('PDF'),
            "sensor": TagCollector('Multibeam echo sounder'),
            "study": TagCollector('Geotechnical investigations HKN'),
            "zone": TagCollector('Ancillary', 'Hollandse Kust (noord)'),
        }

        record = self.files['results'][0]

        # When
        self.handler.import_file(record)

        # Then
        self.assertDictEqual({k: v.as_dict(k) for k, v in self.handler.tag_categories.items()},
                             {k: v.as_dict(k) for k, v in expected_categories.items()})

        just_added: ExternalContent = ExternalContent.objects.first()

        self.assertEqual(just_added.title, record['name'])
        self.assertEqual(just_added.description, record['description'])
        self.assertDateEqual(str(just_added.created_at), record['date_created'])
        self.assertDateEqual(str(just_added.updated_at), record['date_modified'])
        self.assertEqual(just_added.owner, self.handler.owner)
        self.assertEqual(just_added.source, self.handler.source)
        self.assertTrue(just_added.remote_id.startswith(self.source.guid))
        self.assertTrue(just_added.remote_id.endswith(str(record['id'])))
        self.assertTrue(just_added.canonical_url.startswith(self.source.settings['frontendUrl']))
        self.assertTrue(just_added.canonical_url.endswith(str(record['id'])))
        self.assertDictEqual({t['name']: t for t in just_added.category_tags},
                             {k: v.as_dict(k) for k, v in expected_categories.items()})

    def test_import_multiple_file_records(self):
        expected_categories = {
            "chapter": TagCollector('General Information', 'Obstructions'),
            "classification": TagCollector('Processed data', 'Raw data', 'Report'),
            "extension": TagCollector('PDF', 'XYZ', 'ZIP'),
            "sensor": TagCollector('Magnetometer', 'Multibeam echo sounder'),
            "study": TagCollector('Geotechnical investigations HKN', 'Study 2'),
            "zone": TagCollector('Ancillary', 'Doordewind', 'Hollandse Kust (noord)'),
        }

        for record in self.files['results']:
            self.handler.import_file(record)

        self.assertDictEqual({k: v.as_dict(k) for k, v in self.handler.tag_categories.items()},
                             {k: v.as_dict(k) for k, v in expected_categories.items()})

    def test_apply_tags(self):
        self.handler.tag_categories = {"Demo": TagCollector('Tag1', 'Tag2')}
        self.handler.apply_tags()

        self.assertEqual(config.TAG_CATEGORIES, [v.as_dict(k) for k, v in self.handler.tag_categories.items()])


class TestHandlerDatahubCleanupFilesTestCase(PleioTenantTestCase):

    def setUp(self):
        super().setUp()
        self.source = ExternalContentSourceFactory(settings={
            "apiUrl": "https://www.pleio.nl",
            "batchSize": 50,
        })
        self.handler = ApiHandler(self.source)
        self.article1 = ExternalContentFactory(source=self.source)
        self.article2 = ExternalContentFactory(source=self.source)


    def tearDown(self):
        self.source.delete()
        ExternalContent.objects.all().delete()

        super().tearDown()

    def test_delete_files(self):
        self.handler.imported_files = [self.article1.guid]

        self.handler.cleanup_files()

        # Article1 is probably updated.
        self.article1.refresh_from_db()

        # Article1 is probably deleted.
        try:
            self.article2.refresh_from_db()
            self.fail("Article2 unexpectedly still exists in the database")
        except ExternalContent.DoesNotExist:
            pass
