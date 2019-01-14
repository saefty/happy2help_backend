import re

import graphene
from django.contrib.postgres.search import SearchVector, SearchQuery, SearchRank, TrigramSimilarity
from django.db.models import Case, When, F
from django.db.models.functions import Greatest
from graphene_django import DjangoObjectType
from graphql_jwt.decorators import login_required
from django.utils import timezone

from Location.models import Location
from Location.schema import LocationInputType
from User.models import Skill
from .models import Event, Job, Participation, RequiresSkill
from Organisation.models import Organisation


class EventType(DjangoObjectType):
    class Meta:
        model = Event


class ParticipationType(DjangoObjectType):
    state = graphene.Int()

    class Meta:
        model = Participation

    def resolve_state(self, info, **kwargs):
        return self.state


class JobType(DjangoObjectType):
    current_users_participation = graphene.Field(ParticipationType)
    required_skills = graphene.List(graphene.String)

    class Meta:
        model = Job

    def resolve_current_users_participation(self, info, **kwargs):
        participation = Participation.objects.filter(user=info.context.user, job=self)
        return None if not participation else participation.first()

    def resolve_required_skills(self, info, **kwargs):
        return Skill.objects.filter(requiresskill__job=self)


class RequiresSkillType(DjangoObjectType):
    class Meta:
        model = RequiresSkill


class CreateParticipation(graphene.Mutation):
    id = graphene.ID()
    job = graphene.Field(JobType)
    user = graphene.Field("User.schema.UserType")
    state = graphene.Int()
    rating = graphene.Field("Feedback.schema.RatingType")

    class Arguments:
        job_id = graphene.ID(required=True)

    @login_required
    def mutate(self, info, job_id):
        user = info.context.user
        job = Job.objects.get(id=job_id)

        if Participation.objects.filter(user=user, job=job).exists():
            raise Exception("User already applied")

        if job.deleted_at:  # can not apply to a canceled job
            raise Exception("Job has been removed")

        participation = Participation.objects.create(user=user, job=job, state=2)

        return CreateParticipation(
            id=participation.id,
            job=job,
            user=user,
            state=participation.state,
            rating=participation.rating
        )


class UpdateParticipation(graphene.Mutation):
    id = graphene.ID()
    job = graphene.Field(JobType)
    user = graphene.Field("User.schema.UserType")
    state = graphene.Int()
    rating = graphene.Field("Feedback.schema.RatingType")

    class Arguments:
        participation_id = graphene.ID(required=True)
        state = graphene.Int(required=True)

    @login_required
    def mutate(self, info, state, participation_id):
        user = info.context.user
        participation = Participation.objects.get(id=participation_id)
        job = participation.job
        event_creator = job.event.creator

        # if job.deleted_at:  # it is not possible to change the state of a canceled/inactive job
        #     raise Exception("Job is canceled/inactive")

        if state == 5:  # 5 = canceled
            if user != participation.user:
                raise Exception("You need to be the participator")
            participation.state = state
            participation.save()
            return UpdateParticipation(
                id=participation.id,
                job=job,
                user=user,
                state=participation.state,
                rating=participation.rating
            )

        if state == 2:  # 2 = applied
            if user != participation.user:
                raise Exception("You need to be the participator")
            if job.deleted_at:
                raise Exception("The job you try to apply for has been removed")
            participation.state = state
            participation.save()
            return UpdateParticipation(
                id=participation.id,
                job=job,
                user=user,
                state=participation.state,
                rating=participation.rating
            )

        if state in (3, 4, 1):  # 3 = declined, 4 = accepted, 1 = participated
            if event_creator != user:
                raise Exception("You need to be the event creator")
            if state == 4 and job.deleted_at:
                raise Exception("You cannot accept a user for a removed job")
            if state == 1:
                if participation.state == 1:
                    raise Exception("This user already participated")
                if participation.state in (3, 5):
                    raise Exception("This user was either declined already or cancelled the participation")
                participation.user.profile.credit_points += 5
                participation.user.profile.save()

            participation.state = state
            participation.save()
            return UpdateParticipation(
                id=participation.id,
                job=job,
                user=participation.user,
                state=participation.state,
                rating=participation.rating
            )

        raise Exception("State change not allowed")


class CreateJob(graphene.Mutation):
    id = graphene.ID()
    name = graphene.String()
    description = graphene.String()
    event = graphene.Field(EventType)
    total_positions = graphene.Int()
    required_skills = graphene.List(graphene.String)

    class Arguments:
        event_id = graphene.ID(required=True)
        name = graphene.String(required=True)
        description = graphene.String()
        total_positions = graphene.Int(required=False)
        required_skills = graphene.List(graphene.String, required=False)

    @login_required
    def mutate(self, info, event_id, name, description, **kwargs):
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
            total_positions=kwargs.get("total_positions", None)
        )

        required_skills = kwargs.get("required_skills", None)
        if required_skills:
            for required_skill in required_skills:
                skill, created = Skill.objects.get_or_create(name=required_skill)
                RequiresSkill.objects.create(job=job, skill=skill)

        return CreateJob(
            id=job.id,
            name=job.name,
            description=job.description,
            event=job.event,
            total_positions=job.total_positions,
            required_skills=required_skills
        )


class UpdateJob(graphene.Mutation):
    id = graphene.ID()
    name = graphene.String()
    description = graphene.String()
    event = graphene.Field(EventType)
    total_positions = graphene.Int()
    required_skills = graphene.List(graphene.String)

    class Arguments:
        job_id = graphene.ID(required=True)
        name = graphene.String()
        description = graphene.String()
        total_positions = graphene.Int()
        required_skills = graphene.List(graphene.String, required=False)

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

        required_skills = kwargs.get("required_skills", None)
        if required_skills:
            for required_skill in required_skills:
                skill, created = Skill.objects.get_or_create(name=required_skill)
                RequiresSkill.objects.create(job=job, skill=skill)

        return UpdateJob(
            id=job.id,
            name=job.name,
            description=job.description,
            event=job.event,
            total_positions=job.total_positions,
            required_skills=required_skills
        )


class DeleteJob(graphene.Mutation):
    """
    Deletes a job if it is not the last job for an event
    if a job gets deleted, participations with a state of accepted or applied
    will get cancelled (job delete signal).
    """
    id = graphene.ID()

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
        return DeleteJob(id=job_id)


class JobInputType(graphene.InputObjectType):
    id = graphene.ID()
    name = graphene.String(required=True)
    description = graphene.String(required=True)
    total_positions = graphene.Int(required=True)
    required_skills = graphene.List(graphene.String)


class CreateEvent(graphene.Mutation):
    """
    Creates an event. Organisation is optional.
    If no organisation is given, the creator has to pay credits.
    """
    id = graphene.ID()
    name = graphene.String()
    description = graphene.String()
    start = graphene.DateTime()
    end = graphene.DateTime()
    organisation = graphene.Field("Organisation.schema.OrganisationType")
    creator = graphene.Field("User.schema.UserType")
    location = graphene.Field("Location.schema.LocationType")
    jobs = graphene.List(JobType)

    class Arguments:
        organisation_id = graphene.ID()
        name = graphene.String()
        description = graphene.String()
        location_id = graphene.ID()
        location_name = graphene.String()
        location_lat = graphene.Float()
        location_lon = graphene.Float()
        start = graphene.DateTime()
        end = graphene.DateTime()
        jobs = graphene.List(JobInputType)

    @login_required
    def mutate(self, info, name, description, start, end, **kwargs):
        user = info.context.user

        location_id = kwargs.get('location_id', None)
        location = None
        if location_id:
            # add existing location
            location = Location.objects.get(id=location_id)
        else:
            # create new location
            location_name = kwargs.get('location_name', None)
            location_lat = kwargs.get('location_lat', None)
            location_lon = kwargs.get('location_lon', None)
            if location_name and location_lat and location_lon:
                location = Location.objects.create(
                    name=location_name,
                    latitude=location_lat,
                    longitude=location_lon
                )
            else:
                raise Exception("Please provide: location_name, location_lat, location_lon OR location_id !")

        # add organisation if given
        organisation_id = kwargs.get('organisation_id', None)
        organisation = None
        if organisation_id:
            organisation = Organisation.objects.get(id=organisation_id)
            if user not in organisation.members.all():
                raise Exception(f"You need to be a member of {organisation.name} to create an event")
        else:
            user.profile.credit_points -= 10
            user.profile.save()

        event = Event.objects.create(
            name=name,
            description=description,
            creator=user,
            location=location,
            organisation=organisation,
            start=start,
            end=end
        )

        jobs = kwargs.get("jobs", None)
        if jobs:
            for job in jobs:
                new_job = Job.objects.create(
                    name=job.name,
                    description=job.description,
                    event=event,
                    total_positions=job.total_positions
                )
                required_skills = job.required_skills
                if required_skills:
                    for skill in required_skills:
                        skill, created = Skill.objects.get_or_create(name=skill)
                        RequiresSkill.objects.create(skill=skill, job=new_job)
        # create default job
        else:
            Job.objects.create(name=event.name, description=event.description, event=event)

        return CreateEvent(
            id=event.id,
            name=event.name,
            description=event.description,
            start=event.start,
            end=event.end,
            organisation=event.organisation,
            creator=event.creator,
            location=event.location,
            jobs=Job.objects.filter(event=event)
        )


class UpdateEvent(graphene.Mutation):
    id = graphene.ID()
    name = graphene.String()
    description = graphene.String()
    start = graphene.DateTime()
    end = graphene.DateTime()
    organisation = graphene.Field("Organisation.schema.OrganisationType")
    creator = graphene.Field("User.schema.UserType")
    location = graphene.Field("Location.schema.LocationType")
    jobs = graphene.List(JobType)

    class Arguments:
        event_id = graphene.ID(required=True)
        name = graphene.String()
        description = graphene.String()
        start = graphene.DateTime()
        end = graphene.DateTime()
        jobs = graphene.List(JobInputType)

    @login_required
    def mutate(self, info, event_id, jobs, **kwargs):
        user = info.context.user
        event = Event.objects.get(id=event_id)
        organisation = event.organisation

        if not organisation and user != event.creator:
            raise Exception("You need to be the event creator to update the event")

        if organisation and user not in organisation.members.all():
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

        # delete job if id not in 'jobs'
        job_ids = [job.id for job in jobs if job.id]
        jobs_to_delete = Job.objects.filter(event=event).exclude(id__in=job_ids)
        if jobs_to_delete == event.job_set:
            raise Exception("You cannot delete all jobs. There has to be at least one job per event!")
        jobs_to_delete.delete()

        # jobs is required
        for job in jobs:
            # if id is given, update the job
            current_job = None
            if job.id:
                current_job = Job.objects.get(id=job.id)
                current_job.name = job.name
                current_job.description = job.description
                current_job.total_positions = job.total_positions
                current_job.save()

            # create new job
            else:
                current_job = Job.objects.create(
                    name=job.name,
                    description=job.description,
                    event=event,
                    total_positions=job.total_positions
                )

            # update required_skills
            if job.required_skills:
                req_skills_to_delete = RequiresSkill.objects.filter(job=current_job).exclude(
                    skill__name__in=job.required_skills
                )
                req_skills_to_delete.delete()
                for req_skill in job.required_skills:
                    skill, _ = Skill.objects.get_or_create(name=req_skill)
                    RequiresSkill.objects.get_or_create(skill=skill, job=current_job)


        return UpdateEvent(
            id=event.id,
            name=event.name,
            description=event.description,
            start=event.start,
            end=event.end,
            organisation=event.organisation,
            creator=event.creator,
            location=event.location,
            jobs=Job.objects.filter(event=event)
        )


class DeleteEvent(graphene.Mutation):
    id = graphene.ID()

    class Arguments:
        event_id = graphene.ID(required=True)

    @login_required
    def mutate(self, info, event_id):
        user = info.context.user
        event = Event.objects.get(id=event_id)
        organisation = event.organisation

        if user != event.creator:
            if organisation:
                if user not in organisation.members.all():
                    raise Exception(f"You need to be a member of {organisation.name} to delete the event")
            raise Exception("You need to be the event creator to delete the event")

        event.delete()

        return DeleteEvent(id=event_id)


class SortInputType(graphene.InputObjectType):
    field = graphene.String()
    desc = graphene.Boolean()
    distance = LocationInputType()


class TimeDeltaInputType(graphene.InputObjectType):
    start = graphene.DateTime()
    end = graphene.DateTime()


class FilterInputType(graphene.InputObjectType):
    show_private = graphene.Boolean()
    required_skills = graphene.List(graphene.String)
    time = TimeDeltaInputType()


class Query(graphene.ObjectType):
    event = graphene.Field(EventType, id=graphene.ID())
    events = graphene.List(
        EventType,
        search=graphene.String(),
        sorting=SortInputType(),
        filtering=FilterInputType()
    )
    events_by_coordinates = graphene.List(
        EventType,
        ul_longitude=graphene.Float(),
        ul_latitude=graphene.Float(),
        lr_longitude=graphene.Float(),
        lr_latitude=graphene.Float()
    )
    jobs = graphene.List(JobType)
    job = graphene.Field(JobType, id=graphene.ID())
    participations = graphene.List(ParticipationType)

    def resolve_event(self, info, id):
        return Event.objects.get(id=id)

    def resolve_events(self, info, **kwargs):
        events = Event.objects.filter(end__gt=timezone.now())

        # Search Events
        search = kwargs.get("search", None)
        if search:
            # fields to consider with weighing and stop words
            # weights are debatable
            vector = SearchVector('name', weight='A', config='german') + \
                SearchVector('description', weight='B', config='german') + \
                SearchVector('job__name', weigth='C', config='german') + \
                SearchVector('job__description', weight='C', config='german') + \
                SearchVector('location__name', weight='C', config='german') + \
                SearchVector('organisation__name', weight='D', config='german') + \
                SearchVector('organisation__description', weight='D', config='german')

            query = SearchQuery(search, config='german')  # use german stop words

            # get the relevant event ids first. uses trigram similarity and search rank
            event_ids = events.annotate(
                rank=SearchRank(vector, query),
                similarity=Greatest(
                    TrigramSimilarity('name', search),
                    TrigramSimilarity('description', search),
                    TrigramSimilarity('job__name', search),
                    TrigramSimilarity('job__description', search),
                    TrigramSimilarity('location__name', search),
                    TrigramSimilarity('organisation__name', search),
                    TrigramSimilarity('organisation__description', search)),
                score=(F("rank") + F("similarity")) / 2.  # open for debate.
            ).order_by('-score').filter(score__gt=0.1).values_list("id", flat=True)

            if event_ids:
                # keep the ordering of the relevant ids
                preserved = Case(*[When(pk=pk, then=pos) for pos, pk in enumerate(event_ids)])
                # filter by relevant ids
                events = Event.objects.all().filter(id__in=event_ids).order_by(preserved)
            else:
                # nothing relevant found. return none
                return Event.objects.none()

        # Filter Events
        filtering = kwargs.get("filtering", None)
        if filtering:
            # has organisation
            show_private = filtering.get("show_private", True)
            if not show_private:
                events = events.exclude(organisation__isnull=True)
            required_skills = filtering.get("required_skills", None)
            if required_skills:
                events = events.filter(job__requiresskill__skill__name__in=required_skills).distinct()
            # time is between start and/or end
            timedelta = filtering.get("time", None)
            if timedelta:
                start = timedelta.get("start", None)
                end = timedelta.get("end", None)
                if start:
                    events = events.filter(start__gte=start)
                if end:
                    events = events.filter(end__lte=end)

        # Sort Events
        sorting = kwargs.get("sorting", None)
        if sorting:
            field = sorting.get("field", None)
            distance = sorting.get("distance", None)
            if field and distance:
                raise Exception("Cannot sort by field and distance at the same time!")
            # sort by field name
            if field:
                desc = sorting.get("desc", False)
                minus = "-" if desc else ""
                events = events.order_by(minus + field)
            # sort by distance to self
            if distance:
                # events is a list, not a QuerySet
                events = events.order_by_distance(distance)

        return events

    def resolve_events_by_coordinates(self, info, ul_longitude, ul_latitude, lr_longitude, lr_latitude):
        """
        Returns all events that are inside the span of the rectangle area made up of two coordinates.
        ul = upper left
        lr = lower right
        """
        return Event.objects.filter(
            end__gt=timezone.now(),
            location__latitude__gte=ul_latitude,
            location__longitude__gte=ul_longitude,
            location__latitude__lte=lr_latitude,
            location__longitude__lte=lr_longitude,
        )

    def resolve_jobs(self, info):
        return Job.objects.filter(participation__user=info.context.user)
        # return [p.job for p in Participation.objects.filter(user=info.context.user)]

    def resolve_job(self, info, id):
        # all_objects to also select jobs with deleted_at != None
        return Job.all_objects.filter(participation__user=info.context.user).get(id=id)

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
