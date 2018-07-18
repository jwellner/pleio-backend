import graphene
import reversion

from core.lib import get_id
from .models import Blog
from .nodes import BlogNode

class BlogInput(graphene.InputObjectType):
    title = graphene.String(required=True)
    description = graphene.String(required=True)

class CreateBlog(graphene.Mutation):
    class Arguments:
        input = BlogInput(required=True)

    ok = graphene.Boolean()
    blog = graphene.Field(lambda: BlogNode)

    def mutate(self, info, input):
        try:
            with reversion.create_revision():
                blog = Blog.objects.create(
                    owner=info.context.user,
                    title=input['title'],
                    description=input['description']
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
        input = BlogInput(required=True)

    ok = graphene.Boolean()
    blog = graphene.Field(lambda: BlogNode)

    def mutate(self, info, id, input):
        try:
            with reversion.create_revision():
                blog = Blog.objects.get(pk=get_id(id))
                blog.title = input['title']
                blog.description = input['description']
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
            ok = False

        return DeleteBlog(ok=ok)

class Mutation(graphene.ObjectType):
    create_blog = CreateBlog.Field()
    update_blog = UpdateBlog.Field()
    delete_blog = DeleteBlog.Field()
