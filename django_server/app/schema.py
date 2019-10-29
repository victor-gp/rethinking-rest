import graphene
import graphene_django
from django.contrib.auth.backends import UserModel
from .models import Book, HasRead, read_book, average_rating

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

class Query(graphene.ObjectType):
    users = graphene.List(UserType)
    user = graphene.Field(UserType, id=graphene.Int(required=True))
    books = graphene.List(BookType, fiction=graphene.Boolean(),
        first=graphene.Int(), last=graphene.Int(), offset=graphene.Int())
    book = graphene.Field(BookType, id=graphene.Int(required=True))

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
        return UserModel.objects.get(id=kwargs['id'])

    def resolve_book(self, info, **kwargs):
        return Book.objects.get(id=kwargs['id'])

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
