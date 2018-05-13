import graphene
from .types import GroupType

class CreateGroup(graphene.Mutation):
    class Arguments:
        name = graphene.String()
        description = graphene.String()
        is_open = graphene.Boolean()

    ok = graphene.Boolean()
    group = graphene.Field(lambda: GroupType)

    def mutate(self, info, name, description, is_open):
        group = GroupType(name=name, description=description, is_open=is_open)
        ok = True
        return CreateGroup(group=group, ok=ok)

class UpdateGroup(graphene.Mutation):
    class Arguments:
        guid = graphene.ID()
        name = graphene.String()
        description = graphene.String()
        is_open = graphene.Boolean()

    ok = graphene.Boolean()
    group = graphene.Field(lambda: GroupType)

    def mutate(self, info, name, description, is_open):
        group = GroupType(name=name, description=description, is_open=is_open)
        ok = True
        return UpdateGroup(group=group, ok=ok)

class DeleteGroup(graphene.Mutation):
    class Arguments:
        guid = graphene.ID()

    ok = graphene.Boolean()

    def mutate(self, info, guid):
        ok = True
        return DeleteGroup(ok=ok)

class Mutation(graphene.ObjectType):
    create_group = CreateGroup.Field()
    update_group = UpdateGroup.Field()
    delete_group = DeleteGroup.Field()