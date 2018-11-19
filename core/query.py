from django.contrib.contenttypes.models import ContentType
import graphene
from .entities import Entity, Viewer
from .lists import GroupList
from .models import Group as GroupModel


class Query(object):
    entity = graphene.Field(Entity, id=graphene.ID(required=True))
    viewer = graphene.Field(Viewer)
    groups = graphene.Field(
        GroupList,
        filter=graphene.String(),
        offset=graphene.Int(),
        limit=graphene.Int(),
        )

    def resolve_node(self, info, id):
        try:
            parts = id.split(':')
            object_type = parts[0].split('.')

            content_type = ContentType.objects.get(
                app_label=object_type[0],
                model=object_type[1]
                )
            model_class = content_type.model_class()

            # core.group fix needed
            if model_class.objects.visible:
                return model_class.objects.visible(
                    info.context.user
                    ).get(id=parts[1])
            else:
                return model_class.objects.get(id=parts[1])
        except ContentType.DoesNotExist:
            pass

    def resolve_groups(self, info, offset=0, limit=20):
        return GroupList(
            totalCount=GroupModel.objects.count(),
            edges=GroupModel.objects.all()[offset:(offset+limit)]
        )

    def resolve_viewer(self, info):
        user = info.context.user

        return Viewer(
            is_authenticated=user.is_authenticated,
            user=(user if user.is_authenticated else None)
        )
