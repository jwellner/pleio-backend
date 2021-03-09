from django.apps import AppConfig


class FlowConfig(AppConfig):
    name = 'flow'

    def ready(self):
        # pylint: disable=unused-import
        # pylint: disable=import-outside-toplevel
        import flow.signals
