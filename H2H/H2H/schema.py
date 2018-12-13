import graphene

import QR_Code.schema
import User.schema
import Event.schema
import Organisation.schema
import Location.schema
import Feedback.schema
import Image.schema


class Query(
    User.schema.Query,
    Event.schema.Query,
    Organisation.schema.Query,
    Location.schema.Query,
    Feedback.schema.Query,
    QR_Code.schema.Query,
    Image.schema.Query,
    graphene.ObjectType
):
    pass


class Mutation(
    User.schema.Mutation,
    Event.schema.Mutation,
    Organisation.schema.Mutation,
    Location.schema.Mutation,
    Feedback.schema.Mutation,
    QR_Code.schema.Mutation,
    Image.schema.Mutation,
    graphene.ObjectType
):
    pass


schema = graphene.Schema(query=Query, mutation=Mutation)
