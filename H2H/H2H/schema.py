import graphene
import Happy2Help.schema


class Query(Happy2Help.schema.Query, graphene.ObjectType):
    pass


schema = graphene.Schema(query=Query)
