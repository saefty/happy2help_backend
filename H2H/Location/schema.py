import graphene
from graphene_django import DjangoObjectType

from .models import Location


class LocationType(DjangoObjectType):
    class Meta:
        model = Location

# Queries
class Query(graphene.ObjectType):
    locations = graphene.List(LocationType)

    def resolve_locations(self, info):
        return Location.objects.all()


# Mutations
class Mutation(graphene.AbstractType):
    pass