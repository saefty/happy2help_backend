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
    public_id = graphene.String()
    url = graphene.String() 

    class Arguments:
        image = Upload(required=True)
        event_id = graphene.ID()
        organisation_id = graphene.ID()

    def mutate(self, info, image):
        user = info.context.user
        cloud_img = cloudinary.uploader.upload(image)

        server_img = Image.objects.create(
            public_id=cloud_img.get('public_id'),
            url=cloud_img.get('secure_url'),
            organisation=None,
            event=None,
            user=None,
        )

        return UploadImage(public_id=server_img.public_id, url=server_img.url)


class Query(graphene.ObjectType):
    images = graphene.List(ImageType)

    def resolve_images(self, info):
        return Image.objects.all()


class Mutation(graphene.AbstractType):
    upload_image = UploadImage.Field()
