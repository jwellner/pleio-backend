from django.contrib.contenttypes.models import ContentType
import graphene, logging
from .entities import Entity, Viewer, Site, MenuItem
from .lists import GroupList, SearchList, EntityList, UserList, TrendingList, TopList
from .models import Group as GroupModel
from .enums import ORDER_DIRECTION, ORDER_BY

logger = logging.getLogger('django')

GroupFilter = graphene.Enum('GroupFilter', [('all', 'all'), ('mine', 'mine')])
SearchType = graphene.Enum('Type', [('user', 'user'), ('group', 'group'), ('object', 'object'), ('page', 'page')])
OrderBy = graphene.Enum.from_enum(ORDER_BY)
OrderDirection = graphene.Enum.from_enum(ORDER_DIRECTION)

class Query:
    entity = graphene.Field(
        Entity,
        guid=graphene.ID(required=True),
        username=graphene.String()
    )
    viewer = graphene.Field(Viewer)
    groups = graphene.Field(
        GroupList,
        filter=GroupFilter(),
        offset=graphene.Int(),
        limit=graphene.Int()
    )
    search = graphene.Field(
        SearchList,
        q=graphene.String(required=True),
        containerGuid=graphene.String(),
        _type=SearchType(name='type'),
        subType=graphene.String(),
        offset=graphene.Int(),
        limit=graphene.Int(),
    )
    users = graphene.Field(
        UserList,
        q=graphene.String(required=True),
        offset=graphene.Int(),
        limit=graphene.Int()
    )
    entities = graphene.Field(
        EntityList,
        _type=graphene.String(name='type'),
        subtype=graphene.String(),
        subtypes=graphene.List(graphene.String),
        containerGuid=graphene.Int(),
        tags=graphene.List(graphene.String),
        orderBy=OrderBy(),
        orderDirection=OrderDirection(),
        offset=graphene.Int(),
        limit=graphene.Int(),
    )
    site = graphene.Field(Site)
    recommended = graphene.Field(
        EntityList,
        offset=graphene.Int(),
        limit=graphene.Int()
    )
    trending = graphene.Field(graphene.List(TrendingList))
    top = graphene.Field(graphene.List(TopList))

    def resolve_entity(self, info, guid, username):
        try:
            parts = guid.split(':')
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

    def resolve_groups(self, info, filter='all', offset=0, limit=20):
        if filter == 'mine':
            return GroupList(
                total=info.context.user.groups.count(),
                can_write=True,
                edges=info.context.user.groups.all()[offset:(offset+limit)]
            )

        return GroupList(
            total=GroupModel.objects.all().count(),
            can_write=True,
            edges=GroupModel.objects.all()[offset:(offset+limit)]
        )

    def resolve_viewer(self, info):
        user = info.context.user

        return Viewer(
            guid=user.guid(),
            logged_in=user.is_authenticated,
            is_sub_editor=False,
            is_admin=False,
            tags=[],
            user=(user if user.is_authenticated else None),
            can_write_to_container=True
        )

    def resolve_search(self, info, q, containerGuid, type, subType, offset=0, limit=20):

        return SearchList(
            total=0,
            totals=[],
            edges=[]
        )

    def resolve_entities(self, info, type=None, subtype=None, subtypes=[], containerGuid=None, tags=[], orderBy=ORDER_BY.timeUpdated, orderDirection=ORDER_DIRECTION.desc, offset=0, limit=20):

        return EntityList(
            total=0,
            can_write=False,
            edges=[]
        )

    def resolve_site(self, info):
        return Site(
            guid="1",
            name="Backend2",
            theme="leraar",
            menu=[
                MenuItem(
                    title='Nieuws',
                    link='/news',
                    children=[]
                ),
                MenuItem(
                    title='Groups',
                    link='/groups',
                    children=[]
                )
            ],
            footer=[],
            defaultAccessId=1,
            showIcon=False,
            showLeader=False,
            showLeaderButtons=False,
            showInitiative=False,
            usersOnline=999
        )

    def resolve_recommended(self, info, offset=0, limit=20):
        return EntityList(
            total=0,
            can_write=False,
            edges=[]
        )

    def resolve_trending(self, info):
        return [TrendingList(
            tag="test",
            likes=99
        )]

    def resolve_top(self, info):
        return [TopList(
            user=info.context.user,
            likes=99
        )]
