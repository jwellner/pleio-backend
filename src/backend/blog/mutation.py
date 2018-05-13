import graphene
from .types import BlogType

class CreateBlog(graphene.Mutation):
    class Arguments:
        title = graphene.String()
        description = graphene.String()

    ok = graphene.Boolean()
    blog = graphene.Field(lambda: BlogType)

    def mutate(self, info, title, description):
        blog = BlogType(title=title, description=description)
        ok = True
        return CreateBlog(blog=blog, ok=ok)

class UpdateBlog(graphene.Mutation):
    class Arguments:
        guid = graphene.ID()
        title = graphene.String()
        description = graphene.String()

    ok = graphene.Boolean()
    blog = graphene.Field(lambda: BlogType)

    def mutate(self, info, guid, title, description):
        blog = BlogType(guid=guid, title=title, description=description)
        ok = True
        return UpdateBlog(blog=blog, ok=ok)

class DeleteBlog(graphene.Mutation):
    class Arguments:
        guid = graphene.ID()

    ok = graphene.Boolean()

    def mutate(self, info, guid):
        ok = True
        return DeleteBlog(ok=ok)

class Mutation(graphene.ObjectType):
    create_blog = CreateBlog.Field()
    update_blog = UpdateBlog.Field()
    delete_blog = DeleteBlog.Field()
