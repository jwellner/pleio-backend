import json
import os
import time
from contextlib import contextmanager

from datetime import datetime
from unittest import mock

from django.conf import settings
from django.core.cache import cache
from PIL import Image, UnidentifiedImageError
from ariadne import graphql_sync
from django.contrib.auth.models import AnonymousUser
from django.core.files.base import ContentFile
from django.http import HttpRequest
from django.test import override_settings
from django.utils.crypto import get_random_string
from mixer.backend.django import mixer

from backend2.schema import schema
from django.db.models import QuerySet
from collections import Counter

from tenants.helpers import FastTenantTestCase


class PleioTenantTestCase(FastTenantTestCase):

    def setUp(self):
        super().setUp()
        self.graphql_client = GraphQLClient()
        self.file_cleanup = []
        self.settings_cache = {}

        self.mocked_log_warning = mock.patch("logging.Logger.warning").start()
        self.mocked_warn = mock.patch("warnings.warn").start()

    def file_factory(self, filepath):
        from file.models import FileFolder
        filename = os.path.basename(filepath)
        upload = None
        if os.path.exists(filepath):
            with open(filepath, 'rb') as fh:
                upload = ContentFile(fh.read(), filename)
        file = mixer.blend(FileFolder,
                           type=FileFolder.Types.FILE,
                           upload=upload)
        if upload:
            upload_dir = os.path.dirname(file.upload.path)
            self.file_cleanup.append(os.path.join(upload_dir, filename))
            self.file_cleanup.append(file.upload.path)
            if file.thumbnail.name:
                self.file_cleanup.append(file.thumbnail.path)

        return file

    def override_config(self, **kwargs):
        for key, value in kwargs.items():
            cache.set("%s%s" % (self.tenant.schema_name, key), value)

    def override_setting(self, **kwargs):
        for key, value in kwargs.items():
            if key not in self.settings_cache:
                self.settings_cache[key] = getattr(settings, key, None)
            setattr(settings, key, value)

    @staticmethod
    def relative_path(root, path):
        return os.path.join(os.path.dirname(root), *path)

    def build_contentfile(self, path):
        content = open(path, 'rb').read()
        return ContentFile(content, os.path.basename(path))

    def tearDown(self):
        for file in self.file_cleanup:
            cleanup_path(file)

        for key, value in self.settings_cache.items():
            setattr(settings, key, value)
        cache.clear()
        super().tearDown()

    @contextmanager
    def assertGraphQlError(self, expected=None, msg=None):
        fail_reason = False
        try:
            yield
            fail_reason = "Unexpectedly didn't find any errors in graphql result"
        except GraphQlError as e:
            if not e.has_message(expected):
                fail_reason = msg or f"Didn't find [{expected}] in {e.messages}"

        if fail_reason:
            self.fail(fail_reason)

    def assertDateEqual(self, left_date_string, right_date_string, *args, **kwargs):
        assert isinstance(left_date_string, str), "left_date_string should be a string. Is now %s." % type(
            left_date_string)
        assert isinstance(right_date_string, str), "right_date_string should be a string. Is now %s." % type(
            left_date_string)

        left = datetime.fromisoformat(left_date_string)
        right = datetime.fromisoformat(right_date_string)
        self.assertEqual(left, right, *args, **kwargs)

    def assertDictEqual(self, d1, d2, msg=None):
        if isinstance(d1, dict) and isinstance(d2, dict):
            super().assertDictEqual(d1, d2, msg)
        super().assertDictEqual({'data': d1},
                                {'data': d2},
                                msg)

    def tiptap_paragraph(self, *paragraphs):
        return json.dumps({
            'type': 'doc',
            'content': [{
                'type': "paragraph",
                'content': [{
                    'type': 'text',
                    'text': p,
                }]
            } for p in paragraphs]
        })

    def assertExif(self, fp, msg=None):
        image = None
        try:
            image = Image.open(fp)
        except UnidentifiedImageError:
            pass
        assert image and image.getexif(), msg or "Unexpectedly no exif data found."

    def assertNotExif(self, fp, msg=None):
        try:
            image = Image.open(fp)
            assert not image.getexif(), msg or "Unexpectedly found exif data."
        except UnidentifiedImageError:
            pass


class GraphQlError(Exception):

    def __init__(self, data):
        self.data = data

    def has_message(self, expected=None):
        if expected:
            return expected in self.messages
        return True

    @property
    def messages(self):
        return [e['message'] for e in self.data['errors']]


class GraphQLClient():
    result = None
    request = None

    def __init__(self):
        self.reset()

    def reset(self):
        self.force_login(AnonymousUser())

    def force_login(self, user):
        self.request = HttpRequest()
        self.request.user = user
        self.request.COOKIES['sessionid'] = get_random_string(32)

    def post(self, query, variables):
        success, self.result = graphql_sync(schema, {"query": query,
                                                     "variables": variables},
                                            context_value={"request": self.request})

        if self.result.get('errors'):
            raise GraphQlError(self.result)

        return self.result


class ElasticsearchTestCase(PleioTenantTestCase):

    @staticmethod
    @override_settings(ENV='test')
    def initialize_index():
        from core.lib import tenant_schema
        from core.tasks.elasticsearch_tasks import elasticsearch_recreate_indices, elasticsearch_index_data_for_tenant
        elasticsearch_recreate_indices()
        elasticsearch_index_data_for_tenant(tenant_schema(), None)
        time.sleep(.100)


class QuerySetWith:
    """ Class to help identify whether arguments are equal when a QuerySet is expected """

    def __init__(self, result):
        self.result = result

    def __eq__(self, value):
        if not isinstance(value, QuerySet):
            return False

        return Counter(list(value)) == Counter(self.result)


@contextmanager
def suppress_stdout():
    # pylint: disable=import-outside-toplevel
    from contextlib import redirect_stderr, redirect_stdout
    from os import devnull
    with mock.patch('warnings.warn'):
        with open(devnull, 'w') as fnull:
            with redirect_stderr(fnull) as err, redirect_stdout(fnull) as out:
                yield (err, out)


def cleanup_path(path):
    if path == get_system_root():
        return
    try:
        if os.path.isfile(path):
            os.unlink(path)
        else:
            os.rmdir(path)
    except Exception:
        return

    cleanup_path(os.path.dirname(path))


def get_system_root():
    return os.path.abspath(os.path.sep)
