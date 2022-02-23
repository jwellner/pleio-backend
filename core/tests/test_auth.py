from core import config
from django_tenants.test.cases import FastTenantTestCase

from core.auth import OIDCAuthBackend
from core.models.site import SiteAccessRequest

class OIDCAuthBackendTestCase(FastTenantTestCase):

    def setUp(self):
        config.ALLOW_REGISTRATION = False
        config.OIDC_PROVIDERS = ['oidc']
        config.IDP_ID = 'saml'
        config.DIRECT_REGISTRATION_DOMAINS = []
        config.AUTO_APPROVE_SSO = False
        SiteAccessRequest.objects.all().delete()

    def tearDown(self):
        config.reset()

    def test_requires_approval_required(self):
        claims = {
            'is_admin' : False,
            'email': 'email@pleio.nl',
            'sso': [],
        }
        auth = OIDCAuthBackend()

        required = auth.requires_approval(claims)

        self.assertTrue(required)

    def test_requires_approval_open_registration(self):
        config.ALLOW_REGISTRATION = True
        claims = {
            'is_admin' : False,
            'email': 'email@pleio.nl',
            'sso': [],
        }
        auth = OIDCAuthBackend()

        skip = auth.requires_approval(claims)

        self.assertFalse(skip)

    def test_requires_approval_email_domain(self):
        config.DIRECT_REGISTRATION_DOMAINS = ['pleio.nl']
        claims = {
            'is_admin' : False,
            'email': 'email@pleio.nl',
            'sso': [],
        }
        auth = OIDCAuthBackend()

        required = auth.requires_approval(claims)

        self.assertFalse(required)

    def test_requires_approval_approved_request(self):
        claims = {
            'is_admin' : False,
            'email': 'email@pleio.nl',
            'sso': [],
        }
        SiteAccessRequest.objects.create(email='email@pleio.nl', accepted=True)
        auth = OIDCAuthBackend()

        required = auth.requires_approval(claims)

        self.assertFalse(required)

    def test_requires_approval_auto_approve_sso_oidc(self):
        config.AUTO_APPROVE_SSO = True
        claims = {
            'is_admin' : False,
            'email': 'email@pleio.nl',
            'sso': ['oidc'],
        }
        auth = OIDCAuthBackend()

        required = auth.requires_approval(claims)

        self.assertFalse(required)

    def test_requires_approval_auto_approve_sso_saml(self):
        config.AUTO_APPROVE_SSO = True
        claims = {
            'is_admin' : False,
            'email': 'email@pleio.nl',
            'sso': ['saml'],
        }
        auth = OIDCAuthBackend()

        required = auth.requires_approval(claims)

        self.assertFalse(required)

    def test_requires_approval_sso_oidc(self):
        claims = {
            'is_admin' : False,
            'email': 'email@pleio.nl',
            'sso': ['oidc'],
        }
        auth = OIDCAuthBackend()

        required = auth.requires_approval(claims)

        self.assertTrue(required)

    def test_requires_approval_sso_saml(self):
        claims = {
            'is_admin' : False,
            'email': 'email@pleio.nl',
            'sso': ['saml'],
        }
        auth = OIDCAuthBackend()

        required = auth.requires_approval(claims)

        self.assertTrue(required)

    def test_requires_approval_auto_approve_sso_none(self):
        config.AUTO_APPROVE_SSO = True
        claims = {
            'is_admin' : False,
            'email': 'email@pleio.nl',
            'sso': ['none'],
        }
        auth = OIDCAuthBackend()

        required = auth.requires_approval(claims)

        self.assertTrue(required)
