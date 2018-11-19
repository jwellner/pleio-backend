import graphene
import reversion

from core.lib import get_id
from .models import News as NewsModel
from .entities import News


class NewsInput(graphene.InputObjectType):
    title = graphene.String(required=True)
    description = graphene.String(required=True)


class CreateNews(graphene.Mutation):
    class Arguments:
        input = NewsInput(required=True)

    ok = graphene.Boolean()
    news = graphene.Field(lambda: News)

    def mutate(self, info, input):
        try:
            with reversion.create_revision():
                news = NewsModel.objects.create(
                    owner=info.context.user,
                    title=input['title'],
                    description=input['description']
                )

                reversion.set_user(info.context.user)
                reversion.set_comment("createNews mutation")

            ok = True
        except Exception:
            news = None
            ok = False

        return CreateNews(news=news, ok=ok)


class UpdateNews(graphene.Mutation):
    class Arguments:
        id = graphene.ID(required=True)
        input = NewsInput(required=True)

    ok = graphene.Boolean()
    news = graphene.Field(lambda: News)

    def mutate(self, info, id, input):
        try:
            with reversion.create_revision():
                news = NewsModel.objects.get(pk=get_id(id))
                news.title = input['title']
                news.description = input['description']
                news.save()

                reversion.set_user(info.context.user)
                reversion.set_comment("updateNews mutation")

            ok = True
        except Exception:
            news = None
            ok = False

        return UpdateNews(news=news, ok=ok)


class DeleteNews(graphene.Mutation):
    class Arguments:
        id = graphene.ID(required=True)

    ok = graphene.Boolean()

    def mutate(self, info, id):
        try:
            with reversion.create_revision():
                news = NewsModel.objects.get(pk=get_id(id))
                news.delete()

                reversion.set_user(info.context.user)
                reversion.set_comment("deleteNews mutation")

            ok = True
        except Exception:
            ok = False

        return DeleteNews(ok=ok)


class Mutation(graphene.ObjectType):
    create_news = CreateNews.Field()
    update_news = UpdateNews.Field()
    delete_news = DeleteNews.Field()
