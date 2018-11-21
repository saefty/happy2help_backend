import graphene
from graphene_django import DjangoObjectType
from graphql_jwt.decorators import login_required
from django.utils import timezone

from Location.models import Location
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
        job = Job.objects.get(id=job_id)

        if Participation.objects.filter(user=user, job=job).exists():
            raise Exception("User already applied")

        if job.canceled:  # can not apply to a canceled job
            raise Exception("Job is canceled/inactive")

        participation = Participation.objects.create(user=user, job=job, state=2)

        return CreateParticipation(participation=participation)


class UpdateParticipation(graphene.Mutation):
    participation = graphene.Field(ParticipationType)

    class Arguments:
        participation_id = graphene.ID(required=True)
        state = graphene.Int(required=True)

    @login_required
    def mutate(self, info, state, participation_id):
        user = info.context.user
        participation = Participation.objects.get(id=participation_id)
        job = participation.job
        event_creator = job.event.creator

        if job.canceled:  # it is not possible to change the state of a canceled/inactive job
            raise Exception("Job is canceled/inactive")

        if state == 5:  # 5 = canceled
            if user != participation.user:
                raise Exception("You need to be the participator")
            participation.state = state
            participation.save()
            return UpdateParticipation(participation=participation)

        if event_creator != user:
            raise Exception("You need to be the event creator")

        if state in (3, 4):  # 3 = declined, 4 = accepted
            participation.state = state
            participation.save()
            return UpdateParticipation(participation=participation)

        raise Exception("State change not allowed")


class CreateJob(graphene.Mutation):
    job = graphene.Field(JobType)

    class Arguments:
        event_id = graphene.ID(required=True)
        name = graphene.String(required=True)
        description = graphene.String()
        total_positions = graphene.Int(required=True)

    @login_required
    def mutate(self, info, event_id, name, description, total_positions):
        user = info.context.user
        event = Event.objects.get(id=event_id)

        if event.creator != user:
            raise Exception("You need to be the event creator to create a job")
        if Job.objects.filter(name=name, event=event).exists():
            raise Exception("This Job already exists")

        job = Job.objects.create(
            name=name,
            description=description,
            event=event,
            total_positions=total_positions
        )
        return CreateJob(job=job)


class UpdateJob(graphene.Mutation):
    job = graphene.Field(JobType)

    class Arguments:
        job_id = graphene.ID(required=True)
        name = graphene.String()
        description = graphene.String()
        total_positions = graphene.Int()

    @login_required
    def mutate(self, info, job_id, **kwargs):
        user = info.context.user
        job = Job.objects.get(id=job_id)
        event = job.event

        if event.creator != user:
            raise Exception("You need to be the event creator to update a job")

        name = kwargs.get('name', None)
        description = kwargs.get('description', None)
        total_positions = kwargs.get('total_positions', None)

        if name:
            job.name = name
        if description:
            job.description = description
        if total_positions:
            occupied_positions = job.occupied_positions()
            if total_positions < occupied_positions:
                raise Exception(f"Total positions cannot be less than occupied positions({occupied_positions})")
            job.total_positions = total_positions

        job.save()
        return CreateJob(job=job)


class DeleteJob(graphene.Mutation):
    """
    Deletes a job if it is not the last job for an event
    if a job gets deleted, participations with a state of accepted or applied
    will get cancelled (job delete signal).
    """
    job = graphene.Field(JobType)

    class Arguments:
        job_id = graphene.ID(required=True)

    @login_required
    def mutate(self, info, job_id):
        user = info.context.user
        job = Job.objects.get(id=job_id)
        event = job.event

        if event.creator != user:
            raise Exception("You need to be the event creator to delete a job")

        if event.job_set.count() == 1:  # if its the last job
            raise Exception("Cannot delete last job of event. Events need to have at least one job")

        job.delete()
        return DeleteJob(job=job)


class CreateEvent(graphene.Mutation):
    """
    Creates an event. Organisation is optional.
    If no organisation is given, the creator has to pay credits.
    """
    event = graphene.Field(EventType)

    class Arguments:
        organisation_id = graphene.ID()
        name = graphene.String(required=True)
        description = graphene.String(required=True)
        location_id = graphene.ID(required=True)
        start = graphene.DateTime(required=True)
        end = graphene.DateTime(required=True)

    @login_required
    def mutate(self, info, name, description, location_id, **kwargs):
        user = info.context.user
        location = Location.objects.get(id=location_id)

        organisation_id = kwargs.get('organisation_id', None)
        organisation = None
        if organisation_id:
            organisation = Organisation.objects.get(id=organisation_id)
        else:
            user.profile.credit_points -= 10
            user.profile.save()

        event = Event.objects.create(
            name=name,
            description=description,
            creator=user,
            location=location,
            organisation=organisation,  # will be set to NULL if organisation = None
            start=kwargs.get('start'),
            end=kwargs.get('end')
        )

        return CreateEvent(event=event)


class UpdateEvent(graphene.Mutation):
    event = graphene.Field(EventType)

    class Arguments:
        event_id = graphene.ID(required=True)
        name = graphene.String()
        description = graphene.String()
        start = graphene.DateTime()
        end = graphene.DateTime()

    @login_required
    def mutate(self, info, event_id, **kwargs):
        user = info.context.user
        event = Event.objects.get(id=event_id)
        organisation = event.organisation

        if not organisation and user != event.creator:
            raise Exception("You need to be the event creator to update the event")

        if user not in organisation.members.all():
            raise Exception(f"You need to be a member of {organisation.name} to update the event")

        if kwargs.get('name', None):
            event.name = kwargs['name']
        if kwargs.get('description', None):
            event.description = kwargs['description']
        if kwargs.get('start', None):
            event.start = kwargs['start']
        if kwargs.get('end', None):
            event.end = kwargs['end']

        event.save()

        return UpdateEvent(event=event)


class DeleteEvent(graphene.Mutation):
    event = graphene.Field(EventType)

    class Arguments:
        event_id = graphene.ID(required=True)

    @login_required
    def mutate(self, info, event_id):
        user = info.context.user
        event = Event.objects.get(id=event_id)
        organisation = event.organisation

        if user != event.creator:
            if organisation.exists():
                if user not in organisation.members.all():
                    raise Exception(f"You need to be a member of {organisation.name} to delete the event")
            raise Exception("You need to be the event creator to delete the event")

        event.delete()

        return DeleteEvent(event)


class Query(graphene.ObjectType):
    event = graphene.Field(EventType, id=graphene.Int())
    events = graphene.List(EventType)
    events_by_coordinates = graphene.List(EventType, ul_longitude=graphene.Float(), ul_latitude=graphene.Float(),
                                          lr_longitude=graphene.Float(), lr_latitude=graphene.Float())

    jobs = graphene.List(JobType)
    participations = graphene.List(ParticipationType)

    def resolve_event(self, info, id):
        return Event.objects.get(pk=id)

    def resolve_events(self, info):
        return Event.objects.filter(end__gt = timezone.now())

    def resolve_events_by_coordinates(self, info, ul_longitude, ul_latitude, lr_longitude, lr_latitude):
        """
        Returns all events that are inside the span of the rectangle area made up of two coordinates.
        ul = upper left
        lr = lower right
        """
        return Event.objects.filter(
            end__gt = timezone.now(),
            location__latitude__gte=ul_latitude,
            location__longitude__gte=ul_longitude,
            location__latitude__lte=lr_latitude,
            location__longitude__lte=lr_longitude,
        )

    def resolve_jobs(self, info):
        return [p.job for p in Participation.objects.filter(user=info.context.user)]

    def resolve_participations(self, info):
        return Participation.objects.filter(user=info.context.user)


class Mutation(graphene.AbstractType):
    create_participation = CreateParticipation.Field()
    update_participation = UpdateParticipation.Field()

    create_job = CreateJob.Field()
    update_job = UpdateJob.Field()
    delete_job = DeleteJob.Field()

    create_event = CreateEvent.Field()
    update_event = UpdateEvent.Field()
    delete_event = DeleteEvent.Field()
