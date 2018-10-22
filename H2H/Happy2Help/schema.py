from graphene import relay
from django.contrib.auth.models import User
from graphene_django import DjangoObjectType
from graphene_django.filter import DjangoFilterConnectionField
from .models import Favourite, Rating, Participation, Event, Organisation, Report, Job, Profile


class UserNode(DjangoObjectType):
    class Meta:
        model = User
        filter_fields = ['username', 'email']
        interfaces = (relay.Node, )


class ProfileNode(DjangoObjectType):
    class Meta:
        model = Profile
        filter_fields = ['user__username', 'user__email', 'birthday']
        interfaces = (relay.Node, )


class EventNode(DjangoObjectType):
    class Meta:
        model = Event
        filter_fields = ['name', 'description', 'organisation', 'creator']
        interfaces = (relay.Node, )


class OrganisationNode(DjangoObjectType):
    class Meta:
        model = Organisation
        filter_fields = ['name', 'description', 'member']
        interfaces = (relay.Node, )


class JobNode(DjangoObjectType):
    class Meta:
        model = Job
        filter_fields = ['name', 'description']
        interfaces = (relay.Node, )


class ParticipationNode(DjangoObjectType):
    class Meta:
        model = Participation
        filter_fields = ['event', 'user', 'rating']
        interfaces = (relay.Node, )


class RatingNode(DjangoObjectType):
    class Meta:
        model = Rating
        filter_fields = ['user_a', 'orga_a', 'user_b', 'orga_b', 'rating']
        interfaces = (relay.Node, )


class FavouriteNode(DjangoObjectType):
    class Meta:
        model = Favourite
        filter_fields = ['event', 'user']
        interfaces = (relay.Node, )


class ReportNode(DjangoObjectType):
    class Meta:
        model = Report
        filter_fields = ['reason', 'user_a', 'orga_a', 'user_b', 'orga_b', 'text']
        interfaces = (relay.Node, )


class Query(object):
    user = relay.Node.Field(UserNode)
    all_users = DjangoFilterConnectionField(UserNode)

    profile = relay.Node.Field(ProfileNode)
    all_profiles = DjangoFilterConnectionField(ProfileNode)

    event = relay.Node.Field(EventNode)
    all_events = DjangoFilterConnectionField(EventNode)

    organisation = relay.Node.Field(OrganisationNode)
    all_organisations = DjangoFilterConnectionField(OrganisationNode)

    job = relay.Node.Field(JobNode)
    all_jobs = DjangoFilterConnectionField(JobNode)

    participation = relay.Node.Field(ParticipationNode)
    all_participations = DjangoFilterConnectionField(ParticipationNode)

    rating = relay.Node.Field(RatingNode)
    all_ratings = DjangoFilterConnectionField(RatingNode)

    favourite = relay.Node.Field(FavouriteNode)
    all_favourites = DjangoFilterConnectionField(FavouriteNode)

    report = relay.Node.Field(ReportNode)
    all_reports = DjangoFilterConnectionField(ReportNode)
