import graphene
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
            blog = Blog.objects.create(owner=info.context.user, title=title, description=description)
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
            blog = Blog.objects.get(pk=get_id(id))
            blog.title = title
            blog.description = description
            blog.save()
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
            blog = Blog.objects.get(pk=get_id(id))
            blog.delete()
            ok = True
        except:
            blog = None
            ok = False

        return DeleteBlog(ok=ok)

class Mutation(graphene.ObjectType):
    create_blog = CreateBlog.Field()
    update_blog = UpdateBlog.Field()
    delete_blog = DeleteBlog.Field()
