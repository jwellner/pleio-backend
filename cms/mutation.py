import graphene
import reversion

from core.lib import get_id
from .models import CmsPage
from .nodes import CmsPageNode

class CmsPageInput(graphene.InputObjectType):
    title = graphene.String(required=True)
    description = graphene.String(required=True)

class CreateCmsPage(graphene.Mutation):
    class Arguments:
        input = CmsPageInput(required=True)

    ok = graphene.Boolean()
    cms_page = graphene.Field(lambda: CmsPageNode)

    def mutate(self, info, title, description):
        try:
            with reversion.create_revision():
                cms_page = CmsPage.objects.create(
                    owner=info.context.user,
                    title=title,
                    description=description
                )

                reversion.set_user(info.context.user)
                reversion.set_comment("createCmsPage mutation")

            ok = True
        except:
            cms_page = None
            ok = False

        return CreateCmsPage(cms_page=cms_page, ok=ok)

class UpdateCmsPage(graphene.Mutation):
    class Arguments:
        id = graphene.ID(required=True)
        input = CmsPageInput(required=True)

    ok = graphene.Boolean()
    cms_page = graphene.Field(lambda: CmsPageNode)

    def mutate(self, info, id, title, description):
        try:
            with reversion.create_revision():
                cms_page = CmsPage.objects.get(pk=get_id(id))
                cms_page.title = title
                cms_page.description = description
                cms_page.save()

                reversion.set_user(info.context.user)
                reversion.set_comment("updateCmsPage mutation")

            ok = True
        except:
            cms_page = None
            ok = False

        return UpdateCmsPage(cms_page=cms_page, ok=ok)

class DeleteCmsPage(graphene.Mutation):
    class Arguments:
        id = graphene.ID(required=True)

    ok = graphene.Boolean()

    def mutate(self, info, id):
        try:
            with reversion.create_revision():
                cms_page = CmsPage.objects.get(pk=get_id(id))
                cms_page.delete()

                reversion.set_user(info.context.user)
                reversion.set_comment("deleteCmsPage mutation")

            ok = True
        except:
            ok = False

        return DeleteCmsPage(ok=ok)

class Mutation(graphene.ObjectType):
    create_cms_page = CreateCmsPage.Field()
    update_cms_page = UpdateCmsPage.Field()
    delete_cms_page = DeleteCmsPage.Field()
