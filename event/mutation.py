import graphene
import reversion

from core.lib import get_id
from .models import Event
from .nodes import EventNode

class EventInput(graphene.InputObjectType):
    title = graphene.String(required=True)
    description = graphene.String(required=True)
    start_date = graphene.DateTime(required=True)
    end_date = graphene.DateTime(required=True)

class CreateEvent(graphene.Mutation):
    class Arguments:
        input = EventInput(required=True)

    ok = graphene.Boolean()
    event = graphene.Field(lambda: EventNode)

    def mutate(self, info, title, description, start_date, end_date):
        try:
            with reversion.create_revision():
                event = Event.objects.create(
                    owner=info.context.user,
                    title=title,
                    description=description,
                    start_date=start_date,
                    end_date=end_date
                )

                reversion.set_user(info.context.user)
                reversion.set_comment("createEvent mutation")

            ok = True
        except:
            event = None
            ok = False

        return CreateEvent(event=event, ok=ok)

class UpdateEvent(graphene.Mutation):
    class Arguments:
        id = graphene.ID(required=True)
        input = EventInput(required=True)

    ok = graphene.Boolean()
    event = graphene.Field(lambda: EventNode)

    def mutate(self, info, id, title, description, start_date, end_date):
        try:
            with reversion.create_revision():
                event = Event.objects.get(pk=get_id(id))
                event.title = title,
                event.description = description,
                event.start_date = start_date,
                event.end_date = end_date
                event.save()

                reversion.set_user(info.context.user)
                reversion.set_comment("updateEvent mutation")

            ok = True
        except:
            event = None
            ok = False

        return UpdateEvent(event=event, ok=ok)

class DeleteEvent(graphene.Mutation):
    class Arguments:
        id = graphene.ID(required=True)

    ok = graphene.Boolean()

    def mutate(self, info, id):
        try:
            with reversion.create_revision():
                event = Event.objects.get(pk=get_id(id))
                event.delete()

                reversion.set_user(info.context.user)
                reversion.set_comment("deleteEvent mutation")

            ok = True
        except:
            event = None
            ok = False

        return DeleteEvent(ok=ok)

class Mutation(graphene.ObjectType):
    create_event = CreateEvent.Field()
    update_event = UpdateEvent.Field()
    delete_event = DeleteEvent.Field()
