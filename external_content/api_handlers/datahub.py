from external_content.api_handlers import ApiHandlerBase


class ApiHandler(ApiHandlerBase):
    ID = 'datahub'

    def pull(self):
        raise NotImplementedError()
