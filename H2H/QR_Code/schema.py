import graphene
from django.contrib.auth.models import User
from graphql_jwt.decorators import login_required
from django.core.signing import TimestampSigner


def make_token(user):
    return TimestampSigner().sign(user.username)


class TokenType(graphene.ObjectType):
    username = graphene.String()
    token = graphene.String()


class Query(graphene.ObjectType):
    qr_get_token = graphene.Field(TokenType)
    qr_check_token = graphene.Field("User.schema.UserType", token=graphene.String())

    @login_required
    def resolve_qr_get_token(self, info, **kwargs):
        username, token = make_token(info.context.user).split(":", 1)
        qr_token = TokenType()
        qr_token.username = username
        qr_token.token = token
        return qr_token

    @login_required
    def resolve_qr_check_token(self, info, token, **kwargs):
        key = '%s:%s' % (info.context.user, token)
        username = TimestampSigner().unsign(key, max_age=60 * 5)
        user = User.objects.get(username=username)
        return user



class Mutation(graphene.AbstractType):
    pass
