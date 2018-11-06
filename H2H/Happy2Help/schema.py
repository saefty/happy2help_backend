import graphene
import graphql_jwt
from django.contrib.auth.models import User
from graphene_django import DjangoObjectType
from .models import Favourite, Rating, Participation, Event, Organisation, Report, Job, Profile, Location
from graphql_jwt.decorators import login_required


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


@login_required
def field_restrictor(self, info, field):
    """ allows only the user himself access on the given field"""
    if info.context.user != self:
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

    """
    def resolve_user(self, info):
        if info.context.user.id != self.event.creator.id:
            raise Exception(
                "You have to be the creator of the event to get the participators")
        return self.user

    """


class RatingType(DjangoObjectType):
    class Meta:
        model = Rating


class FavouriteType(DjangoObjectType):
    class Meta:
        model = Favourite

    def resolve_user(self, info):
        if info.context.user != self.user:
            raise Exception("not authorized")
        return self.user


class ReportType(DjangoObjectType):
    class Meta:
        model = Report

class LocationType(DjangoObjectType):
    class Meta:
        model = Location


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
            user=User.objects.filter(username=user.username).first(),
            birthday=kwargs.get('birthday', None),
        )
        profile.save()

        return CreateUser(user=user, profile=profile)


class CreateParticipation(graphene.Mutation):
    participation = graphene.Field(ParticipationType)

    class Arguments:
        job_id = graphene.ID(required=True)

    @login_required
    def mutate(self, info, job_id):
        user = info.context.user
        job = Job.objects.filter(pk=job_id).first()

        if Participation.objects.filter(user=user, job=job):
            raise Exception("User already applied")

        participation = Participation(
            job=job,
            user=user,
            state="AP"
        )
        participation.save()

        return CreateParticipation(participation=participation)


class UpdateParticipation(graphene.Mutation):
    participation = graphene.Field(ParticipationType)

    class Arguments:
        participation_id = graphene.ID(required=True)
        state = graphene.String(required=True)

    @login_required
    def mutate(self, info, state, participation_id):
        user = info.context.user
        participation = Participation.objects.filter(pk=participation_id).first()
        event_creator = participation.job.event.creator
        job = participation.job

        if state == "CA":
            if user != participation.user:
                raise Exception("You need to be the participator")
            if participation.state == "AC": #case user cancels after he was accepted
                job.openpositions = job.openpositions + 1
                job.save()
            participation.state = state
            participation.save()
            return UpdateParticipation(participation=participation)

        #if event_creator != user:
        #    raise Exception("You need to be the event creator")

        if state == "AC" and participation.state != "AC": #case event creator accepts user
            job.openpositions = job.openpositions - 1
            job.save()
        elif state == "DE" and participation.state == "AC":#case event creator declines user after he accepted him
            job.openpositions = job.openpositions + 1
            job.save()
        participation.state = state
        participation.save()
        return UpdateParticipation(participation=participation)


class UpdateUser(graphene.Mutation):
    user = graphene.Field(UserType)
    class Arguments:
        birthday = graphene.types.datetime.Date()
        email = graphene.String()

    @login_required
    def mutate(self, info, **kwargs):
        user = info.context.user
        if kwargs.get('birthday', None):
            user.profile.birthday = kwargs.get('birthday', None)
        if kwargs.get('email', None):
            user.email = kwargs.get('email', None)
        user.profile.save()
        user.save()

        return UpdateUser(user=user)

class DeleteUser(graphene.Mutation):
    user = graphene.Field(UserType)

    @login_required
    def mutate(self, info):
        user = info.context.user
        user.delete()
        return DeleteUser(user)


class CreateOrganisation(graphene.Mutation):
    organisation = graphene.Field(OrganisationType)

    class Arguments:
        name = graphene.String(required=True)
        description = graphene.String(required=True)

    @login_required
    def mutate(self, info, **kwargs):
        organisation = Organisation(
            admin = info.context.user,
            name = kwargs.get('name'),
            description = kwargs.get('description')
        )
        organisation.save()
        organisation.members.add(info.context.user)

        return CreateOrganisation(organisation=organisation)

class UpdateOrganisation(graphene.Mutation):
    organisation = graphene.Field(OrganisationType)

    class Arguments:
        org_id = graphene.ID(required=True)
        new_name = graphene.String()
        new_description = graphene.String()
        add_member = graphene.ID()
        delete_member = graphene.ID()

    @login_required
    def mutate(self, info, **kwargs):
        user = info.context.user
        organisation = Organisation.objects.get(pk=kwargs.get('org_id'))

        if user != organisation.admin:
            raise Exception('You have to be the admin of this organisation to update it')

        if kwargs.get('new_name', None):
            organisation.name = kwargs.get('new_name', None)
        if kwargs.get('new_description', None):
            organisation.description = kwargs.get('new_description', None)
        if kwargs.get('add_member', None):
            organisation.members.add(User.objects.get(pk=kwargs.get('add_member')))
        if kwargs.get('delete_member', None):
            to_be_deleted = User.objects.get(pk=kwargs.get('delete_member'))
            if to_be_deleted != organisation.admin:
                organisation.members.remove(to_be_deleted)
            else:
                raise Exception('You cannot remove the admin of an organisation')

        organisation.save()

        return UpdateOrganisation(organisation=organisation)

class DeleteOrganisation(graphene.Mutation):
    organisation = graphene.Field(OrganisationType)

    class Arguments:
        org_id = graphene.ID(required=True)

    @login_required
    def mutate(self, info, org_id):
        user = info.context.user
        organisation = Organisation.objects.get(pk=org_id)

        if user != organisation.admin:
            raise Exception('You have to be the admin of this organisation to delete it')

        organisation.delete()
        return DeleteOrganisation(organisation)


class Mutation(graphene.AbstractType):
    create_user = CreateUser.Field()
    create_participation = CreateParticipation.Field()
    update_participaion = UpdateParticipation.Field()
    update_user = UpdateUser.Field()
    delete_user = DeleteUser.Field()
    create_organisation = CreateOrganisation.Field()
    update_organisation = UpdateOrganisation.Field()
    delete_organisation = DeleteOrganisation.Field()
    token_auth = graphql_jwt.ObtainJSONWebToken.Field()
    verify_token = graphql_jwt.Verify.Field()
    refresh_token = graphql_jwt.Refresh.Field()
