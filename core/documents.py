from django_elasticsearch_dsl import Document, fields
from django_elasticsearch_dsl.registries import registry
from .models.user import User, UserProfile, UserProfileField
from .models.group import Group
from django_tenants.utils import parse_tenant_config_path


class DefaultDocument(Document):
    tenant_name = fields.KeywordField()

    def prepare_tenant_name(self, instance):
        # pylint: disable=unused-argument
        return parse_tenant_config_path("")


@registry.register_document
class UserDocument(DefaultDocument):
    id = fields.StringField()
    type = fields.KeywordField(attr="type_to_string")
    read_access = fields.ListField(fields.StringField(attr="search_read_access"))

    _profile = fields.NestedField(properties={
        'user_profile_fields': fields.ObjectField(properties={
            'value': fields.KeywordField(),
            'name': fields.KeywordField(),
            'key': fields.KeywordField(),
            'read_access': fields.ListField(fields.StringField(attr="read_access"))
        })
    })

    class Index:
        name = 'users'

    class Django:
        model = User

        fields = [
            'name',
            'email',
            'created_at',
            'updated_at'
        ]

        related_models = [UserProfile, UserProfileField]

    def get_instances_from_related(self, related_instance):
        """From Django dsl docs: If related_models is set, define how to retrieve the UserProfile instance(s) from the related model.
        The related_models option should be used with caution because it can lead in the index
        to the updating of a lot of items.
        """
        if isinstance(related_instance, UserProfile):
            return related_instance.user
        return related_instance.user_profile.user

@registry.register_document
class GroupDocument(DefaultDocument):
    id = fields.StringField()
    tags = fields.ListField(fields.StringField())
    type = fields.KeywordField(attr="type_to_string")
    read_access = fields.ListField(fields.StringField(attr="search_read_access"))

    class Index:
        name = 'groups'

    class Django:
        model = Group
        
        fields = [
            'name',
            'description',
            'introduction',
            'created_at',
            'updated_at'
        ]
