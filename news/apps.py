from django.apps import AppConfig


class NewsConfig(AppConfig):
    name = 'news'

    def ready(self):
        from actstream import registry
        registry.register(self.get_model('News'))
