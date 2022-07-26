from tenants.helpers import FastTenantTestCase
from user.factories import UserFactory
from user.models import User


class TestCaseSensitiveQueryTestCase(FastTenantTestCase):

    def setUp(self):
        super().setUp()

        self.QUERY = 'case sensitive username'
        self.USERNAME = 'cAse SEnSItIVE UsErNAME'
        self.user = UserFactory(name=self.USERNAME)

    def test_implicit_exact_match(self):
        with self.assertRaises(User.DoesNotExist):
            User.objects.get(name=self.QUERY)

    def test_explicit_iexact_match(self):
        User.objects.get(name__iexact=self.QUERY)
