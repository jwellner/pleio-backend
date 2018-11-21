import graphene

class NotificationList(graphene.ObjectType):
    total = graphene.Int(required=True)
    totalUnread = graphene.Int()
    edges = graphene.List('notifications.entities.Notification')
