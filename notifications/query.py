import graphene
from .lists import NotificationList

class Query(object):
    notifications = graphene.Field(
        NotificationList,
        offset=graphene.Int(),
        limit=graphene.Int()
    )

    def resolve_notifications(self, info, offset=0, limit=20):
        return NotificationList(
            total=0,
            totalUnread=0,
            edges=[]
        )
