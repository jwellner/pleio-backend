import graphene
import reversion

from core.lib import get_id
from .models import Blog
from .types import BlogType

class CreateBlog(graphene.Mutation):
    class Arguments:
        title = graphene.String(required=True)
        description = graphene.String(required=True)

    ok = graphene.Boolean()
    blog = graphene.Field(lambda: BlogType)

    def mutate(self, info, title, description):
        try:
            with reversion.create_revision():
                blog = Blog.objects.create(
                    owner=info.context.user,
                    title=title,
                    description=description
                )

                reversion.set_user(info.context.user)
                reversion.set_comment("createBlog mutation")

            ok = True
        except:
            blog = None
            ok = False

        return CreateBlog(blog=blog, ok=ok)

class UpdateBlog(graphene.Mutation):
    class Arguments:
        id = graphene.ID(required=True)
        title = graphene.String(required=True)
        description = graphene.String(required=True)

    ok = graphene.Boolean()
    blog = graphene.Field(lambda: BlogType)

    def mutate(self, info, id, title, description):
        try:
            with reversion.create_revision():
                blog = Blog.objects.get(pk=get_id(id))
                blog.title = title
                blog.description = description
                blog.save()

                reversion.set_user(info.context.user)
                reversion.set_comment("updateBlog mutation")

            ok = True
        except:
            blog = None
            ok = False

        return UpdateBlog(blog=blog, ok=ok)

class DeleteBlog(graphene.Mutation):
    class Arguments:
        id = graphene.ID(required=True)

    ok = graphene.Boolean()

    def mutate(self, info, id):
        try:
            with reversion.create_revision():
                blog = Blog.objects.get(pk=get_id(id))
                blog.delete()

                reversion.set_user(info.context.user)
                reversion.set_comment("deleteBlog mutation")

            ok = True
        except:
            blog = None
            ok = False

        return DeleteBlog(ok=ok)

class Mutation(graphene.ObjectType):
    create_blog = CreateBlog.Field()
    update_blog = UpdateBlog.Field()
    delete_blog = DeleteBlog.Field()
