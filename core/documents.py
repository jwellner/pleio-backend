from django.conf import settings
from django_elasticsearch_dsl import Document, fields
from django_elasticsearch_dsl.registries import registry
from .models.user import User


@registry.register_document
class UserDocument(Document):
    id = fields.StringField()
    type = fields.KeywordField(attr="type_to_string")
    read_access = fields.ListField(fields.StringField(attr="search_read_access"))

    class Index:
        name = settings.ELASTICSEARCH_INDEX

    class Django:
        model = User

        fields = [
            'name',
            'email',
            'created_at',
            'updated_at'
        ]
