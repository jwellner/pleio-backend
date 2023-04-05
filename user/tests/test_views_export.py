from unittest import mock

from django.http import HttpResponse
from django.urls import reverse

from core.tests.helpers import PleioTenantTestCase
from user.exception import ExportError
from user.factories import UserFactory, AdminFactory, EditorFactory


class TestViewsExportTestCase(PleioTenantTestCase):

    def setUp(self):
        super().setUp()
        self.admin = AdminFactory(email="admin@example.com",
                                  name="admin")
        self.override_config(IS_CLOSED=False)

    def test_export_as_anonymous_user(self):
        response = self.client.get(reverse('users_export'))
        self.assertEqual(response.status_code, 401)
        self.assertEqual(response.reason_phrase, 'Not logged in')

    def test_export_as_std_user(self):
        user = UserFactory(email="authenticated@example.com")
        self.client.force_login(user)
        response = self.client.get(reverse('users_export'))
        self.assertEqual(response.status_code, 405)
        self.assertEqual(response.reason_phrase, 'Not admin')

    def test_views_export_no_fields(self):
        self.client.force_login(self.admin)
        response = self.client.get(reverse('users_export'))
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.reason_phrase, 'No fields passed')

    @mock.patch('user.views.ExportUsers.stream')
    def test_export_custom_error(self, stream):
        stream.side_effect = ExportError("Foo")

        self.client.force_login(self.admin)
        response = self.client.get(reverse('users_export') + '?user_fields[]=name&user_fields[]=email')
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.reason_phrase, 'Foo')

    @mock.patch('user.views.StreamingHttpResponse')
    @mock.patch('user.views.ExportUsers')
    def test_export_using_expected_tools(self, ExportUsers, StreamingHttpResponse):
        export_users = mock.MagicMock()
        ExportUsers.return_value = export_users
        stream_result = mock.MagicMock()
        export_users.stream.return_value = stream_result
        StreamingHttpResponse.return_value = HttpResponse("Bar")
        admin_user = UserFactory(email="superadmin@example.com",
                                 is_superadmin=True)
        expected_users = {UserFactory(email="user@example.com"),
                          EditorFactory(email="editor@example.com"),
                          self.admin}

        self.client.force_login(self.admin)
        response = self.client.get(reverse('users_export')
                                   + '?user_fields[]=name&user_fields[]=email'
                                   + '&profile_field_guids[]=Foo&profile_field_guids[]=Bar')

        self.assertEqual(ExportUsers.call_count, 1)

        self.assertEqual({*ExportUsers.call_args.args[0]}, expected_users)
        self.assertEqual(ExportUsers.call_args.kwargs, {
            "user_fields": ['name', 'email'],
            "profile_field_guids": ['Foo', 'Bar']
        })

        self.assertEqual(StreamingHttpResponse.call_count, 1)
        self.assertEqual(StreamingHttpResponse.call_args.kwargs, {
            'streaming_content': stream_result,
            'content_type': 'text/csv'
        })

    def test_export_returns_csv(self):
        expected_users = {UserFactory(email="user@example.com"),
                          EditorFactory(email="editor@example.com"),
                          self.admin}

        self.client.force_login(self.admin)
        response = self.client.get(reverse('users_export') + '?user_fields[]=email')

        self.assertEqual(response.status_code, 200)

        content = response.getvalue()
        self.assertEqual(content, b"email\r\nadmin@example.com\r\nuser@example.com\r\neditor@example.com\r\n")
