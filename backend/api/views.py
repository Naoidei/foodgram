from django.contrib.auth import get_user_model
from django.db import transaction
from django.db.models import Sum
from django.http import HttpResponse
from django.shortcuts import get_object_or_404
from django_filters.rest_framework import DjangoFilterBackend
from djoser.permissions import CurrentUserOrAdmin
from djoser.views import UserViewSet
from rest_framework import filters, status, viewsets
from rest_framework.decorators import action
from rest_framework.exceptions import ValidationError
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from urlshortner.utils import shorten_url

from ..recipes.models import (Favorite, Ingredient, IngredientInRecipe, Recipe,
                              ShoppingList, Subscription, Tag)
from .filters import RecipeFilter
from .paginators import PageNumberLimitPagination
from .permissions import IsAuthorOrReadOnly
from .serializers import (AvatarSerializer, FavoriteSerializer,
                          IngredientSerializer, RecipeGetSerializer,
                          RecipePostSerializer, ShoppingListSerializer,
                          SubscriptionGetSerializer,
                          SubscriptionPostSerializer, TagSerializer)

User = get_user_model()


class IngredientViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Ingredient.objects.all()
    serializer_class = IngredientSerializer
    filter_backends = (filters.SearchFilter,)
    search_fields = ('^name',)


class TagViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Tag.objects.all()
    serializer_class = TagSerializer


class FoodgramUserViewSet(UserViewSet):
    pagination_class = PageNumberLimitPagination
    http_method_names = ['get', 'post', 'put', 'delete']

    def get_permissions(self):
        if self.action == 'me':
            self.permission_classes = [CurrentUserOrAdmin]
        return super().get_permissions()

    @action(detail=True,
            methods=['post', 'delete'],
            permission_classes=[IsAuthenticated]
            )
    @transaction.atomic
    def subscribe(self, request, id):
        author = get_object_or_404(User, pk=id)
        if request.method == 'POST':
            serializer = SubscriptionPostSerializer(
                data={'author': author.id}, context={'request': request}
            )
            serializer.is_valid(raise_exception=True)
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        instance = Subscription.objects.filter(
            user=request.user, author=author
        )
        if instance.exists():
            instance.delete()
            return Response(status=status.HTTP_204_NO_CONTENT)
        raise ValidationError({'errors': f'Вы не подписаны на {author}!'})

    @action(detail=False,
            permission_classes=[IsAuthenticated])
    def subscriptions(self, request):
        paginated_subscriptions = self.paginate_queryset(
            User.objects.filter(subscribers__user=self.request.user)
        )
        serializer = SubscriptionGetSerializer(
            paginated_subscriptions,
            many=True,
            context={'request': request},
        )
        return self.get_paginated_response(serializer.data)

    @action(methods=['put', 'delete'],
            detail=False,
            permission_classes=[CurrentUserOrAdmin],
            url_path='me/avatar',
            url_name='me-avatar',
            )
    @transaction.atomic
    def me_avatar(self, request):
        if request.method == 'DELETE':
            request.user.avatar = None
            request.user.save()
            return Response(status=status.HTTP_204_NO_CONTENT)
        serializer = AvatarSerializer(
            data=request.data, context={'request': request}
        )
        if serializer.is_valid():
            request.user.avatar = serializer.validated_data['avatar']
            request.user.save()
            return Response(
                {'avatar': request.user.avatar.url}, status=status.HTTP_200_OK
            )
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class RecipeViewSet(viewsets.ModelViewSet):
    queryset = Recipe.objects.all()
    pagination_class = PageNumberLimitPagination
    permission_classes = [IsAuthorOrReadOnly]
    filter_backends = (DjangoFilterBackend,)
    filterset_class = RecipeFilter
    http_method_names = ['get', 'post', 'patch', 'delete']

    def get_serializer_class(self):
        if self.action in ['list', 'retrieve']:
            return RecipeGetSerializer
        return RecipePostSerializer

    def recipe_relation(self, request, pk, serializer, model):
        recipe = get_object_or_404(Recipe, id=pk)
        if request.method == 'POST':
            serializer = serializer(
                data={'recipe': recipe.id, 'user': request.user.id},
                context={'request': request},
            )
            serializer.is_valid(raise_exception=True)
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        instance = model.objects.filter(recipe=recipe, user=request.user)
        if instance.exists():
            instance.delete()
            return Response(status=status.HTTP_204_NO_CONTENT)
        raise ValidationError({'errors': f'Рецепт не был добавлен в {model}'})

    @action(detail=True,
            methods=['post', 'delete'],
            permission_classes=[IsAuthenticated],
            )
    @transaction.atomic
    def favorite(self, request, pk=None):
        return self.recipe_relation(request, pk, FavoriteSerializer, Favorite)

    @action(detail=True,
            methods=['post', 'delete'],
            permission_classes=[IsAuthenticated],
            )
    @transaction.atomic
    def shopping_cart(self, request, pk=None):
        return self.recipe_relation(
            request, pk, ShoppingListSerializer, ShoppingList
        )

    @action(detail=False, permission_classes=[IsAuthenticated])
    def download_shopping_cart(self, request):
        shopping_list = IngredientInRecipe.objects.filter(
            recipe__shopping_list__user=request.user
        ).values_list(
            'ingredient__name', 'ingredient__measurement_unit'
        ).annotate(
            total_amount=Sum('amount')
        )
        data = 'Список покупок:\n'
        for name, measurement_unit, total_amount in shopping_list:
            data += f'{name} - {total_amount} ({measurement_unit})\n'
        return HttpResponse(data, headers={
            'Content-Type': 'text/plain',
            'Content-Disposition': 'attachment; filename="shopping_list.txt"'
        })

    @action(detail=True, url_path='get-link')
    def get_link(self, request, pk=None):
        get_object_or_404(Recipe, id=pk)
        long_url = request.build_absolute_uri()
        prefix = 'https://mytesthost.webhop.me/s/'
        short_link = shorten_url(long_url, is_permanent=True)
        return Response({'short-link': prefix + short_link})
