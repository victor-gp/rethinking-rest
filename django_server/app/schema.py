import graphene
import graphene_django
from django.contrib.auth.backends import UserModel
from .models import Book, HasRead, read_book, average_rating
from graphql import GraphQLError

class UserType(graphene_django.DjangoObjectType):
    is_admin = graphene.Boolean()

    def resolve_is_admin(self, info):
        return self.is_staff

    class Meta:
        model = UserModel
        only_fields = ('id', 'username', 'books_read')

class BookType(graphene_django.DjangoObjectType):
    average_rating = graphene.Float()

    def resolve_average_rating(self, info):
        return average_rating(self.id)

    class Meta:
        model = Book

class HasReadType(graphene_django.DjangoObjectType):
    class Meta:
        model = HasRead

user_args = {
    'id': graphene.Int(),
    'username': graphene.String()
}

book_args = {
    'id': graphene.Int(),
    'title': graphene.String()
}

class Query(graphene.ObjectType):
    users = graphene.List(UserType)
    user = graphene.Field(UserType, **user_args)
    books = graphene.List(BookType, fiction=graphene.Boolean(),
        first=graphene.Int(), last=graphene.Int(), offset=graphene.Int())
    book = graphene.Field(BookType, **book_args)

    def resolve_users(self, info):
        return UserModel.objects.all()

    def resolve_books(self, info, **kwargs):
        q = Book.objects.all()

        fiction = kwargs.get('fiction')
        if fiction is not None:
            q = q.filter(fiction=fiction)

        first = kwargs.get('first')
        last = kwargs.get('last')
        offset = abs(kwargs.get('offset') or 0)
        if first:
            return q[offset : offset + first]
        elif last:
            return Query.paginate_last(q, last, offset)

        return q

    def paginate_last(q, last, offset):
        last_index = q.count()
        end = last_index - offset
        if end < 0: end = 0

        start =  end - last
        if start < 0: start = 0

        return q[start:end]

    def resolve_user(self, info, **kwargs):
        Query.validate_either_args('id', 'username', kwargs)
        if 'id' in kwargs:
            return UserModel.objects.get(id=kwargs['id'])
        elif 'username' in kwargs:
            return UserModel.objects.get(username=kwargs['username'])

    def resolve_book(self, info, **kwargs):
        Query.validate_either_args('id', 'title', kwargs)
        if 'id' in kwargs:
            return Book.objects.get(id=kwargs['id'])
        elif 'title' in kwargs:
            return Book.objects.get(title=kwargs['title'])

    def validate_either_args(arg1, arg2, kwargs):
        both_error_message = (f"Only one of arguments \"{arg1}\" and \"{arg2}\""
                               " is allowed but both provided.")
        neither_error_message = (f"One of arguments \"{arg1}\" and \"{arg2}\""
                                  "is required but not provided.")
        if arg1 in kwargs:
            if arg2 in kwargs:
                raise GraphQLError(both_error_message)
        elif arg2 not in kwargs:
            raise GraphQLError(neither_error_message)

class ReadBook(graphene.Mutation):
    class Arguments:
        username = graphene.String(required=True)
        book_title = graphene.String(required=True)
        rating = graphene.Int()

    has_read = graphene.Field(HasReadType)

    def mutate(self, info, **kwargs):
        user = UserModel.objects.get(username=kwargs['username']).id
        book = Book.objects.get(title=kwargs['book_title']).id
        rating = kwargs.get('rating')

        has_read = read_book(book, user, rating)
        return ReadBook(has_read = has_read)

class Mutations(graphene.ObjectType):
    read_book = ReadBook.Field()

schema = graphene.Schema(query=Query, mutation=Mutations)
