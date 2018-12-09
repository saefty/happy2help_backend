import graphene
from graphene_django import DjangoObjectType
from graphql_jwt.decorators import login_required

from .models import Location


class LocationType(DjangoObjectType):
    class Meta:
        model = Location
        exclude_fields = ('profile', 'event',)


class CreateLocation(graphene.Mutation):
    id = graphene.ID()
    latitude = graphene.Float()
    longitude = graphene.Float()
    name = graphene.String()

    class Arguments:
        latitude = graphene.Float(required=True)
        longitude = graphene.Float(required=True)
        name = graphene.String(required=True)

    @login_required
    def mutate(self, info, latitude, longitude, name):
        location = Location.objects.create(latitude=latitude, longitude=longitude, name=name)
        return CreateLocation(
            id=location.id,
            latitude=location.latitude,
            longitude=location.longitude,
            name=location.name
        )


class UpdateLocation(graphene.Mutation):
    id = graphene.ID()
    latitude = graphene.Float()
    longitude = graphene.Float()
    name = graphene.String()

    class Arguments:
        location_id = graphene.ID(required=True)
        latitude = graphene.Float()
        longitude = graphene.Float()
        name = graphene.String()

    @login_required
    def mutate(self, info, location_id, **kwargs):
        location = Location.objects.get(id=location_id)
        if kwargs.get('latitude', None):
            location.latitude = kwargs['latitude']
        if kwargs.get('longitude', None):
            location.latitude = kwargs['longitude']
        if kwargs.get('name', None):
            location.latitude = kwargs['name']
        location.save()
        return UpdateLocation(
            id=location.id,
            latitude=location.latitude,
            longitude=location.longitude,
            name=location.name
        )


# Queries
class Query(graphene.ObjectType):
    pass


# Mutations
class Mutation(graphene.AbstractType):
    create_location = CreateLocation.Field()
    update_location = UpdateLocation.Field()
