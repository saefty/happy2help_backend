import graphene
import graphql_jwt
from django.contrib.auth.models import User
from graphene_django import DjangoObjectType
from .models import Favourite, Rating, Participation, Event, Organisation, Report, Job, Profile, Location
from graphql_jwt.decorators import login_required


class UserType(DjangoObjectType):
    class Meta:
        model = User

    # restricted Fields:
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
    state = graphene.Int()

    class Meta:
        model = Participation

    def resolve_state(self, info, **kwargs):
        return self.state


class RatingType(DjangoObjectType):
    class Meta:
        model = Rating


class FavouriteType(DjangoObjectType):
    class Meta:
        model = Favourite


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
    locations = graphene.List(LocationType)

    def resolve_user(self, info):
        if info.context.user.is_anonymous:
            raise Exception('Not logged!')
        return info.context.user

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

    def resolve_favourites(self, info):
        return Favourite.objects.all()

    def resolve_reports(self, info, id):
        return Report.objects.all()

    def resolve_locations(self, info):
        return Location.objects.all()


# Mutations
class CreateUser(graphene.Mutation):
    user = graphene.Field(UserType)
    profile = graphene.Field(ProfileType)

    class Arguments:
        username = graphene.String(required=True)
        password = graphene.String(required=True)
        email = graphene.String(required=True)
        birthday = graphene.types.datetime.Date()
        location = graphene.String()

    def mutate(info, username, password, email, **kwargs):
        user = User(username=username, email=email)
        user.set_password(password)
        user.save()

        profile = Profile(
            user=user,
            birthday=kwargs.get('birthday', None),
        )
        profile.save()

        return CreateUser(user=user, profile=profile)


class UpdateUser(graphene.Mutation):
    user = graphene.Field(UserType)

    class Arguments:
        birthday = graphene.types.datetime.Date()
        email = graphene.String()
        # gps_coordinates

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


class CreateParticipation(graphene.Mutation):
    participation = graphene.Field(ParticipationType)

    class Arguments:
        job_id = graphene.ID(required=True)

    @login_required
    def mutate(self, info, job_id):
        user = info.context.user
        job = Job.objects.filter(pk=job_id).first()

        if Participation.objects.filter(user=user,
                                        job=job):  # avoids multiple participations from a user to the same job
            raise Exception("User already applied")

        if job.canceled:  # can not apply to a canceled job
            raise Exception("Job is canceled/inactive")

        participation = Participation(
            job=job,
            user=user,
            state=2
        )
        participation.save()

        return CreateParticipation(participation=participation)


class UpdateParticipation(graphene.Mutation):
    participation = graphene.Field(ParticipationType)

    class Arguments:
        participation_id = graphene.ID(required=True)
        state = graphene.Int(required=True)

    @login_required
    def mutate(self, info, state, participation_id):
        user = info.context.user
        participation = Participation.objects.get(
            pk=participation_id)
        event_creator = participation.job.event.creator
        job = participation.job

        if job.canceled == True:  # it is not possible to change the state of a canceled/inactive job
            raise Exception("Job is canceled/inactive")

        if state == 5:  # 5=canceled
            if user != participation.user:
                raise Exception("You need to be the participator")
            if participation.state == 4:  # case user cancels after he was accepted, 4=accepted
                job.open_positions = job.open_positions + 1
                job.save()
            participation.state = state
            participation.save()
            return UpdateParticipation(participation=participation)

        if event_creator != user:
            raise Exception("You need to be the event creator")

        if state == 4 and participation.state != 4:  # case event creator accepts user, 4=accepted
            job.open_positions = job.open_positions - 1
            job.save()
        # case event creator declines user after he accepted him
        elif state == 3 and participation.state == 4:  # 3=declined, 4=accepted
            job.open_positions = job.open_positions + 1
            job.save()
        participation.state = state
        participation.save()
        return UpdateParticipation(participation=participation)


class CreateJob(graphene.Mutation):
    job = graphene.Field(JobType)

    class Arguments:
        event_id = graphene.ID(required=True)
        name = graphene.String(required=True)
        description = graphene.String()
        total_positions = graphene.Int(required=True)

    @login_required
    def mutate(self, info, **kwargs):
        user = info.context.user
        event = Event.objects.get(pk=kwargs.get('event_id'))

        if event.creator != user:
            raise Exception("You need to be the event creator to create a job")
        if Job.objects.filter(name=kwargs.get('name'), event=event):
            raise Exception("This Job already exists")

        job = Job(
            name=kwargs.get('name'),
            description=kwargs.get('description', None),
            event=event,
            total_positions=kwargs.get('total_positions')
        )
        job.save()
        return CreateJob(job=job)


class UpdateJob(graphene.Mutation):
    job = graphene.Field(JobType)

    class Arguments:
        id = graphene.ID(required=True)
        name = graphene.String()
        description = graphene.String()
        total_positions = graphene.Int()

    @login_required
    def mutate(self, info, **kwargs):
        user = info.context.user
        job = Job.objects.get(pk=kwargs.get('id'))
        event = job.event

        if event.creator != user:
            raise Exception("You need to be the event creator to create a job")

        if kwargs.get('name', None):
            if Job.objects.filter(name=kwargs.get('name'),
                                  event=event).exists():  # no jobs with the same name at the same event
                raise Exception("This Job already exists")
            job.name = kwargs.get('name')

        if kwargs.get('description', None):
            job.description = kwargs.get('description')

        if kwargs.get('total_positions', None):
            total_positions = kwargs.get('total_positions')
            if -total_positions + job.total_positions > job.total_positions:  # make sure not more users are accepted than possible
                raise Exception(
                    "already accepted too many users, decline some users")
            job.open_positions = total_positions - job.total_positions + job.open_positions  # keeping open position up to date
            job.total_positions = total_positions

        job.save()
        return CreateJob(job=job)


class DeleteJob(graphene.Mutation):
    job = graphene.Field(JobType)

    class Arguments:
        id = graphene.ID(required=True)

    @login_required
    def mutate(self, info, **kwargs):
        user = info.context.user
        job = Job.objects.get(pk=kwargs.get('id'))
        event = job.event

        if event.creator != user:
            raise Exception("You need to be the event creator to delete a job")

        if not Participation.objects.filter(job=job).exists():  # if there are no participations
            job.delete()  # the job gets deleted in the db immediately
            return DeleteJob(job=job)

        # if there are already participations the job is marked as canceled but not deleted
        job.canceled = True
        job.save()
        return DeleteJob(job=job)


class CreateOrganisation(graphene.Mutation):
    organisation = graphene.Field(OrganisationType)

    class Arguments:
        name = graphene.String(required=True)
        description = graphene.String(required=True)

    @login_required
    def mutate(self, info, **kwargs):
        organisation = Organisation(
            admin=info.context.user,
            name=kwargs.get('name'),
            description=kwargs.get('description')
        )
        organisation.save()
        organisation.members.add(info.context.user)

        return CreateOrganisation(organisation=organisation)


class UpdateOrganisation(graphene.Mutation):
    organisation = graphene.Field(OrganisationType)

    class Arguments:
        id = graphene.ID(required=True)
        name = graphene.String()
        description = graphene.String()
        add_member = graphene.ID()
        delete_member = graphene.ID()

    @login_required
    def mutate(self, info, **kwargs):
        user = info.context.user
        organisation = Organisation.objects.get(pk=kwargs.get('id'))

        if user != organisation.admin:
            raise Exception('You have to be the admin of this organisation to update it')

        if kwargs.get('name', None):
            organisation.name = kwargs.get('name', None)
        if kwargs.get('description', None):
            organisation.description = kwargs.get('description', None)
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
        id = graphene.ID(required=True)

    @login_required
    def mutate(self, info, id):
        user = info.context.user
        organisation = Organisation.objects.get(pk=id)

        if user != organisation.admin:
            raise Exception('You have to be the admin of this organisation to delete it')

        organisation.delete()
        return DeleteOrganisation(organisation)


class CreateEvent(graphene.Mutation):
    event = graphene.Field(EventType)

    class Arguments:
        id = graphene.ID(required=True)
        name = graphene.String(required=True)
        description = graphene.String(required=True)

    @login_required
    def mutate(self, info, name, description, id):
        user = info.context.user
        try:
            organisation = user.organisation_set.get(pk=id)
        except Organisation.DoesNotExist:
            raise Exception("You need to be a member of the organisation to create an event for it")

        event = Event.objects.create(name=name, description=description, organisation=organisation, creator=user)
        # initial default job for the event
        job = Job.objects.create(name=name, description=description, event=event)

        return CreateEvent(event=event)


class UpdateEvent(graphene.Mutation):
    event = graphene.Field(EventType)

    class Arguments:
        id = graphene.ID(required=True)
        name = graphene.String()
        description = graphene.String()

    @login_required
    def mutate(self, info, **kwargs):
        user = info.context.user
        event = Event.objects.get(pk=kwargs.get('id'))
        organisation = event.organisation

        try:
            user.organisation_set.get(pk=organisation.id)
        except Organisation.DoesNotExist:
            raise Exception("You need to be a member of the organisation to update this event")

        if kwargs.get('name', None):
            event.name = kwargs.get('name', None)
        if kwargs.get('description', None):
            event.description = kwargs.get('description', None)
        event.save()

        return UpdateEvent(event=event)


class DeleteEvent(graphene.Mutation):
    event = graphene.Field(EventType)

    class Arguments:
        id = graphene.ID(required=True)

    @login_required
    def mutate(self, info, id):
        user = info.context.user
        event = Event.objects.get(pk=id)
        organisation = event.organisation

        try:
            user.organisation_set.get(pk=organisation.id)
        except Organisation.DoesNotExist:
            raise Exception("You need to be a member of the organisation to delete this event")

        event.delete()
        return DeleteEvent(event)


class Mutation(graphene.AbstractType):
    create_user = CreateUser.Field()
    update_user = UpdateUser.Field()
    delete_user = DeleteUser.Field()

    create_participation = CreateParticipation.Field()
    update_participation = UpdateParticipation.Field()

    create_job = CreateJob.Field()
    update_job = UpdateJob.Field()
    delete_job = DeleteJob.Field()

    create_organisation = CreateOrganisation.Field()
    update_organisation = UpdateOrganisation.Field()
    delete_organisation = DeleteOrganisation.Field()

    create_event = CreateEvent.Field()
    update_event = UpdateEvent.Field()
    delete_event = DeleteEvent.Field()

    token_auth = graphql_jwt.ObtainJSONWebToken.Field()
    verify_token = graphql_jwt.Verify.Field()
    refresh_token = graphql_jwt.Refresh.Field()
