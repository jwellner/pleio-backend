import uuid

import faker

from core.utils.convert import tiptap_to_html
from external_content.api_handlers import ApiHandlerBase
from external_content.models import ExternalContent


class ApiHandler(ApiHandlerBase):
    ID = 'default'

    def get_description(self):
        from core.tests.helpers import PleioTenantTestCase
        json = PleioTenantTestCase.tiptap_paragraph(faker.Faker().sentence(),
                                                    faker.Faker().sentence(),
                                                    faker.Faker().sentence())
        return tiptap_to_html(json)

    def pull(self):
        factory = faker.Faker()
        ExternalContent.objects.create(
            title=factory.sentence(),
            source=self.source,
            owner=self.author,
            description=self.get_description(),
            remote_id=uuid.uuid4(),
            canonical_url=factory.url(),
        )
