from unittest import mock

from django.utils import timezone

from concierge.api import ApiTokenData
from core.tests.helpers import PleioTenantTestCase


class TestApiTokenData(PleioTenantTestCase):
    def setUp(self):
        super().setUp()

        token_source = mock.patch("concierge.api.tenant_api_token").start()
        token_source.return_value = "demo"

        self.request = mock.MagicMock()
        self.request.POST = {"Foo": "Bar",
                             "Koe": "Kaa",
                             "timestamp": "baz",
                             "checksum": "d3cd9f69a887"}
        self.request.method = "POST"

        self.api_token_data = ApiTokenData(self.request)

    def test_valid_token(self):
        # Given. Test preset parameters.

        # When...
        self.api_token_data.assert_valid_checksum()

        # Then... No errors.

    def test_invalid_timestamp(self):
        # given... default timestamp, that is not in isoformat.

        try:
            # When.
            self.api_token_data.assert_valid_timestamp()

            self.fail("Unexpectedly did not recognize invalid parameters")  # pragma: no cover
        except AssertionError:

            # Then. An exception
            pass

    def test_valid_timestamp(self):
        # Given, update the timestamp to an isoformat datetime.
        self.request.POST['timestamp'] = timezone.now().timestamp()

        # When
        self.api_token_data.assert_valid_timestamp()

        # Then
        # ... no errors ...

    def test_invalid_token(self):
        # Given, change of parameters.
        self.request.POST['timestamp'] = timezone.now().timestamp()

        try:
            # When
            self.api_token_data.assert_valid_checksum()

            self.fail("Unexpectedly did not recognize invalid parameters")  # pragma: no cover

        except AssertionError:
            # Then... an exception as expected
            pass
