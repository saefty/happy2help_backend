import graphene
import graphql_jwt
from graphene import relay
from django.contrib.auth.models import User
from graphene_django import DjangoObjectType
from graphene_django.filter import DjangoFilterConnectionField
from .models import Favourite, Rating, Participation, Event, Organisation, Report, Job, Profile


class UserType(DjangoObjectType):
    class Meta:
        model = User


class ProfileType(DjangoObjectType):
    class Meta:
        model = Profile


class EventType(DjangoObjectType):
    class Meta:
        model = Event


class OrganisationType(DjangoObjectType):
    class Meta:
        model = Organisation


class JobType(DjangoObjectType):
    class Meta:
        model = Job


class ParticipationType(DjangoObjectType):
    class Meta:
        model = Participation

    def resolve_user(self, info):
        if info.context.user.id != self.event.creator.id:
           raise Exception("not authorized")
        return self.user


class RatingType(DjangoObjectType):
    class Meta:
        model = Rating


class FavouriteType(DjangoObjectType):
    class Meta:
        model = Favourite


class ReportType(DjangoObjectType):
    class Meta:
        model = Report


class Query(graphene.ObjectType):
    user = graphene.Field(UserType)  # relay.Node.Field(UserNode)

    def resolve_user(self, info):
        me = info.context.user
        print(me)
        if me.is_anonymous:
            raise Exception('Not logged!')
        return me

    all_users = graphene.List(UserType)

    profile = graphene.Field(ProfileType)
    all_profiles = graphene.List(ProfileType)

    event = graphene.Field(EventType)
    all_events = graphene.List(EventType)

    organisation = graphene.Field(OrganisationType)
    all_organisations = graphene.List(OrganisationType)

    job = graphene.Field(JobType)
    all_jobs = graphene.List(JobType)

    participation = graphene.Field(ParticipationType)
    all_participations = graphene.List(ParticipationType)

    rating = graphene.Field(RatingType)
    all_ratings = graphene.List(RatingType)

    favourite = graphene.Field(FavouriteType)
    all_favourites = graphene.List(FavouriteType)

    report = graphene.Field(ReportType)
    all_reports = graphene.List(ReportType)


# Mutations
class CreateUser(graphene.Mutation):
    user = graphene.Field(UserType)

    class Arguments:
        username = graphene.String(required=True)
        password = graphene.String(required=True)
        email = graphene.String(required=True)

    def mutate(self, info, username, password, email):
        user = User(
            username=username,
            email=email,
        )
        user.set_password(password)
        user.save()

        return CreateUser(user=user)


class Mutation(graphene.AbstractType):
    create_user = CreateUser.Field()
    token_auth = graphql_jwt.ObtainJSONWebToken.Field()
    verify_token = graphql_jwt.Verify.Field()
    refresh_token = graphql_jwt.Refresh.Field()
