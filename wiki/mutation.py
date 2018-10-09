import graphene
import reversion

from core.lib import get_id
from .models import Wiki
from .nodes import WikiNode


class WikiInput(graphene.InputObjectType):
    title = graphene.String(required=True)
    description = graphene.String(required=True)


class CreateWiki(graphene.Mutation):
    class Arguments:
        input = WikiInput(required=True)

    ok = graphene.Boolean()
    wiki = graphene.Field(lambda: WikiNode)

    def mutate(self, info, input):
        try:
            with reversion.create_revision():
                wiki = Wiki.objects.create(
                    owner=info.context.user,
                    title=input['title'],
                    description=input['description']
                )

                reversion.set_user(info.context.user)
                reversion.set_comment("createWiki mutation")

            ok = True
        except Exception:
            wiki = None
            ok = False

        return CreateWiki(wiki=wiki, ok=ok)


class UpdateWiki(graphene.Mutation):
    class Arguments:
        id = graphene.ID(required=True)
        input = WikiInput(required=True)

    ok = graphene.Boolean()
    wiki = graphene.Field(lambda: WikiNode)

    def mutate(self, info, id, input):
        try:
            with reversion.create_revision():
                wiki = Wiki.objects.get(pk=get_id(id))
                wiki.title = input['title']
                wiki.description = input['description']
                wiki.save()

                reversion.set_user(info.context.user)
                reversion.set_comment("updateWiki mutation")

            ok = True
        except Exception:
            wiki = None
            ok = False

        return UpdateWiki(wiki=wiki, ok=ok)


class DeleteWiki(graphene.Mutation):
    class Arguments:
        id = graphene.ID(required=True)

    ok = graphene.Boolean()

    def mutate(self, info, id):
        try:
            with reversion.create_revision():
                wiki = Wiki.objects.get(pk=get_id(id))
                wiki.delete()

                reversion.set_user(info.context.user)
                reversion.set_comment("deleteWiki mutation")

            ok = True
        except Exception:
            ok = False

        return DeleteWiki(ok=ok)


class Mutation(graphene.ObjectType):
    create_wiki = CreateWiki.Field()
    update_wiki = UpdateWiki.Field()
    delete_wiki = DeleteWiki.Field()
