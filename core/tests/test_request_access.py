from core.tests.helpers import PleioTenantTestCase

class RequestAccessTestCase(PleioTenantTestCase):

    def setUp(self):
        super(RequestAccessTestCase, self).setUp()

    def test_request_access(self):
        session = self.client.session
        session['request_access_claims'] = {
            'email': 'test@pleio.nl',
            'name': 'test user'
        }
        session.save()

        response = self.client.get('/login/request', follow=True)
        
        self.assertTemplateUsed(response, 'registration/request.html')