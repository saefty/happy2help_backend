import graphene
import Happy2Help.schema


class Query(Happy2Help.schema.Query, graphene.ObjectType):
    pass


class Mutation(Happy2Help.schema.Mutation, graphene.ObjectType):
    pass


schema = graphene.Schema(query=Query, mutation=Mutation)
