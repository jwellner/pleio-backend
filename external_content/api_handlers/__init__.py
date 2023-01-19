from external_content.models import ExternalContentSource
from external_content.utils import get_or_create_default_author


class ApiHandlerBase:
    ID = None
    source: ExternalContentSource = None

    def __init__(self, source):
        self.source = source

    def pull(self):
        raise NotImplementedError()

    @property
    def owner(self):
        return get_or_create_default_author()


class ApiHandlerError(Exception):
    pass
