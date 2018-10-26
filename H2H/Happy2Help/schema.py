import graphene
import graphql_jwt
from django.contrib.auth.models import User
from graphene_django import DjangoObjectType
from .models import Favourite, Rating, Participation, Event, Organisation, Report, Job, Profile


class UserType(DjangoObjectType):
    class Meta:
        model = User

    def resolve_organisation_set(self, info):
        return field_restrictor(self, info, self.organisation_set)

    def resolve_profile(self, info):
       return field_restrictor(self, info, self.profile)

    def resolve_event_set(self, info):
        return field_restrictor(self, info, self.event_set)

    def resolve_participation_set(self, info):
        return field_restrictor(self, info, self.participation_set)

    def resolve_favourite_set(self, info):
        return field_restrictor(self, info, self.favourite_set)
    

def field_restrictor(self, info, field):
    """ allows only the user himself access on the given field"""
    if info.context.user.id != self.id:
        raise Exception("You tried to request a restricted Field")
    return field


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
            raise Exception(
                "You have to be the creator of the event to get the participators")
        return self.user


class RatingType(DjangoObjectType):
    class Meta:
        model = Rating


class FavouriteType(DjangoObjectType):
    class Meta:
        model = Favourite

    def resolve_user(self, info):
        if info.context.user.id != self.user.id:
            raise Exception("not authorized")
        return self.user


class ReportType(DjangoObjectType):
    class Meta:
        model = Report


class Query(graphene.ObjectType):
    user = graphene.Field(UserType)
    all_users = graphene.List(UserType)
    profiles = graphene.List(ProfileType)
    events = graphene.List(EventType)
    organisations = graphene.List(OrganisationType)
    jobs = graphene.List(JobType)
    participations = graphene.List(ParticipationType)
    ratings = graphene.List(RatingType)
    favourites = graphene.List(FavouriteType)
    reports = graphene.List(ReportType)

    def resolve_user(self, info):
        me = info.context.user
        if me.is_anonymous:
            raise Exception('Not logged!')
        return me

    def resolve_all_users(self, info):
        return User.objects.all()

    def resolve_profiles(self, info):
        return Profile.objects.all()

    def resolve_events(self, info):
        return Event.objects.all()

    def resolve_organisations(self, info):
        return Organisation.objects.all()

    def resolve_jobs(self, info):
        return Job.objects.all()

    def resolve_participations(self, info):
        return Participation.objects.all()

    def resolve_ratings(self, info, id):
        return Rating.objects.all()

    def resolve_favourites(self, info, id):
        return Favourite.objects.all()

    def resolve_reports(self, info, id):
        return Report.objects.all()


# Mutations
class CreateUser(graphene.Mutation):
    user = graphene.Field(UserType)
    profile = graphene.Field(ProfileType)

    class Arguments:
        username = graphene.String(required=True)
        password = graphene.String(required=True)
        email = graphene.String(required=True)
        birthday = graphene.types.datetime.Date(required=False)


    def mutate(self, info, username, password, email, **kwargs):
        user = User(
            username=username,
            email=email,
        )
       
        user.set_password(password)
        user.save()

        profile = Profile(
            user= User.objects.filter(username=user.username).first(),
            birthday = kwargs.get('birthday', None),
        )

        profile.save()

        return CreateUser(user=user, profile=profile)


class Mutation(graphene.AbstractType):
    create_user = CreateUser.Field()
    token_auth = graphql_jwt.ObtainJSONWebToken.Field()
    verify_token = graphql_jwt.Verify.Field()
    refresh_token = graphql_jwt.Refresh.Field()
