import graphene
from graphene_django import DjangoObjectType
from graphql_jwt.decorators import login_required

from .models import Event, Job, Participation
from Organisation.models import Organisation


class EventType(DjangoObjectType):
    class Meta:
        model = Event


class JobType(DjangoObjectType):
    class Meta:
        model = Job


class ParticipationType(DjangoObjectType):
    state = graphene.Int()

    class Meta:
        model = Participation

    def resolve_state(self, info, **kwargs):
        return self.state


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


# Queries
class Query(graphene.ObjectType):
    events = graphene.List(EventType)
    jobs = graphene.List(JobType)
    participations = graphene.List(ParticipationType)

    def resolve_events(self, info):
        return Event.objects.all()

    def resolve_jobs(self, info):
        return Job.objects.all()

    def resolve_participations(self, info):
        return Participation.objects.all()


# Mutations
class Mutation(graphene.AbstractType):
    create_participation = CreateParticipation.Field()
    update_participation = UpdateParticipation.Field()

    create_job = CreateJob.Field()
    update_job = UpdateJob.Field()
    delete_job = DeleteJob.Field()

    create_event = CreateEvent.Field()
    update_event = UpdateEvent.Field()
    delete_event = DeleteEvent.Field()
