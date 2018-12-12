import graphene
from django.contrib.auth.models import User
from graphene_django import DjangoObjectType
from graphql_jwt.decorators import login_required
from graphene_file_upload.scalars import Upload
import cloudinary

from Organisation.models import Organisation
from Event.models import Event
from .models import Image


class ImageType(DjangoObjectType):
    class Meta:
        model = Image


class UploadImage(graphene.Mutation):
    """
    This mutation handles file input. The transferred file is uploaded to cloudinary and
    a server-side Image object is created. Depending on whether an organisation or event Id
    was part of the mutation, the model establishes a one-to-one field to the respective entity.
    If no Id was given, the image references the auth user.
    """

    id = graphene.ID()
    public_id = graphene.String()
    url = graphene.String()
    organisation = graphene.Field('Organisation.schema.OrganisationType')
    event = graphene.Field('Event.schema.EventType')
    user = graphene.Field('User.schema.UserType') 

    class Arguments:
        image = Upload(required=True)
        event_id = graphene.ID()
        organisation_id = graphene.ID()

    @login_required
    def mutate(self, info, image, **kwargs):
        user = info.context.user
        organisation = event = None
        folder = 'userProfiles'
        organisation_id = kwargs.get('organisation_id', None)
        event_id = kwargs.get('event_id', None)

        if organisation_id and event_id:
            raise Exception("Mutation with either organisationId, eventId or no ID at all")

        if organisation_id:
            organisation = Organisation.objects.get(id=organisation_id)
            if user not in organisation.members.all():
                 raise Exception(f"You need to be a member of {organisation.name} to upload the image")
            folder = 'organisationProfiles'
            user = None
        elif event_id:
            event = Event.objects.get(id=event_id)
            if user not in event.organisation.members.all():
                 raise Exception(f"You need to be a member of {organisation.name} to upload the image")
            folder = 'eventImages'
            user = None

        cloud_img = cloudinary.uploader.upload(image, folder=folder)

        server_img = Image.objects.create(
            public_id=cloud_img.get('public_id'),
            url=cloud_img.get('secure_url'),
            organisation=organisation,
            event=event,
            user=user,
        )

        return UploadImage(
            id=server_img.id,
            public_id=server_img.public_id, 
            url=server_img.url, 
            organisation=server_img.organisation, 
            event=server_img.event,
            user=server_img.user
        )


class DeleteImage(graphene.Mutation):
    public_id = graphene.String()
    url = graphene.String()

    class Arguments:
        image_id = graphene.ID(required=True)

    @login_required
    def mutate(self, info, image_id):
        user = info.context.user
        image = Image.objects.get(id=image_id)
        event = image.event
        organisation = image.organisation
        img_user = image.user

        if event and event.creator != user:
            raise Exception("You need to be the event creator to delete this image")

        if organisation and organisation.admin != user:
            raise Exception("You need to be the admin of this organisation to delete this image")

        if img_user and img_user != user:
            raise Exception("You need to be the rightful user to delete this image")

        image.delete()
        return DeleteImage(public_id=image.public_id, url=image.url)


class Query(graphene.ObjectType):
    images = graphene.List(ImageType)

    def resolve_images(self, info):
        return Image.objects.all()


class Mutation(graphene.AbstractType):
    upload_image = UploadImage.Field()
    delete_image = DeleteImage.Field()
