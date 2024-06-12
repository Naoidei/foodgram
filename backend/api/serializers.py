import base64

from django.contrib.auth import get_user_model
from django.core.files.base import ContentFile
from django.db import transaction
from djoser.serializers import UserSerializer
from rest_framework import serializers

from recipes.models import (Favorite, Ingredient, IngredientInRecipe, Recipe,
                            ShoppingList, Subscription, Tag)


User = get_user_model()


class Base64ImageField(serializers.ImageField):
    def to_internal_value(self, data):
        if isinstance(data, str) and data.startswith('data:image'):
            format, imgstr = data.split(';base64,')
            ext = format.split('/')[-1]
            data = ContentFile(base64.b64decode(imgstr), name='temp.' + ext)
        return super().to_internal_value(data)


class FoodgramUserSerializer(UserSerializer):
    is_subscribed = serializers.SerializerMethodField()
    avatar = Base64ImageField(read_only=True)

    class Meta:
        model = User
        fields = ('id', 'username', 'email', 'first_name', 'last_name',
                  'avatar', 'is_subscribed')

    def get_is_subscribed(self, obj):
        user = self.context.get('request').user
        return (
            Subscription.objects.filter(user=user.id, author=obj.id).exists()
            and user.is_authenticated
        )


class AvatarSerializer(serializers.ModelSerializer):
    avatar = Base64ImageField()

    class Meta:
        model = User
        fields = ('avatar', )


class IngredientSerializer(serializers.ModelSerializer):
    class Meta:
        model = Ingredient
        fields = '__all__'


class TagSerializer(serializers.ModelSerializer):
    class Meta:
        model = Tag
        fields = '__all__'


class IngredientInRecipeGetSerializer(serializers.ModelSerializer):
    id = serializers.IntegerField(source='ingredient.id')
    name = serializers.CharField(source='ingredient.name')
    measurement_unit = serializers.CharField(
        source='ingredient.measurement_unit'
    )

    class Meta:
        model = IngredientInRecipe
        fields = ('id', 'name', 'measurement_unit', 'amount')


class IngredientInRecipePostSerializer(serializers.ModelSerializer):
    id = serializers.PrimaryKeyRelatedField(
        queryset=Ingredient.objects.all()
    )
    amount = serializers.IntegerField(min_value=1)

    class Meta:
        model = IngredientInRecipe
        fields = ('id', 'amount')


class RecipeShortSerializer(serializers.ModelSerializer):
    image = Base64ImageField()

    class Meta:
        model = Recipe
        fields = ('id', 'name', 'image', 'cooking_time')


class RecipeGetSerializer(serializers.ModelSerializer):
    ingredients = IngredientInRecipeGetSerializer(
        source='ingridients_in_recipe', many=True
    )
    tags = TagSerializer(many=True)
    author = FoodgramUserSerializer()
    image = Base64ImageField()
    is_favorited = serializers.SerializerMethodField()
    is_in_shopping_cart = serializers.SerializerMethodField()

    class Meta:
        model = Recipe
        fields = ('id', 'name', 'ingredients', 'tags', 'image', 'text',
                  'cooking_time', 'author', 'is_favorited',
                  'is_in_shopping_cart')

    def get_is_favorited(self, obj):
        user = self.context.get('request').user
        return (
            Favorite.objects.filter(user=user.id, recipe=obj.id).exists()
            and user.is_authenticated
        )

    def get_is_in_shopping_cart(self, obj):
        user = self.context.get('request').user
        return (
            ShoppingList.objects.filter(user=user.id, recipe=obj.id).exists()
            and user.is_authenticated
        )


class RecipePostSerializer(serializers.ModelSerializer):
    ingredients = IngredientInRecipePostSerializer(many=True)
    tags = serializers.PrimaryKeyRelatedField(many=True,
                                              queryset=Tag.objects.all())
    author = FoodgramUserSerializer(read_only=True)
    image = Base64ImageField()
    cooking_time = serializers.IntegerField(min_value=1)

    class Meta:
        model = Recipe
        fields = ('id', 'name', 'ingredients', 'tags', 'image', 'text',
                  'cooking_time', 'author')

    def validate_field(self, field, value):
        if not field:
            raise serializers.ValidationError(
                {'errors': f'Укажите минимум 1 значение {value}'}
            )
        if value == 'ingredients':
            field = [ingredient.get('id') for ingredient in field]
        if len(field) != len(set(field)):
            raise serializers.ValidationError(
                {'errors': f'Значения {value} должны быть уникалньными'}
            )

    def validate(self, data):
        self.validate_field(data.get('tags'), 'tags')
        self.validate_field(data.get('ingredients'), 'ingredients')
        return data

    def create_ingredients(self, recipe, ingredients_data):
        IngredientInRecipe.objects.bulk_create(
            [IngredientInRecipe(
                recipe=recipe,
                ingredient=Ingredient.objects.get(id=ingredient['id'].id),
                amount=ingredient.get('amount')
            ) for ingredient in ingredients_data]
        )

    @transaction.atomic
    def create(self, validated_data):
        ingredients_data = validated_data.pop('ingredients')
        tags_data = validated_data.pop('tags')
        author = self.context['request'].user
        recipe = Recipe.objects.create(author=author, **validated_data)
        recipe.tags.set(tags_data)
        self.create_ingredients(recipe, ingredients_data)
        return recipe

    @transaction.atomic
    def update(self, instance, validated_data):
        ingredients_data = validated_data.pop('ingredients')
        tags_data = validated_data.pop('tags')
        instance.name = validated_data.get('name', instance.name)
        instance.text = validated_data.get('text', instance.text)
        instance.image = validated_data.get('image', instance.image)
        instance.cooking_time = validated_data.get(
            'cooking_time', instance.cooking_time
        )
        IngredientInRecipe.objects.filter(recipe=instance).delete()
        self.create_ingredients(instance, ingredients_data)
        instance.tags.set(tags_data)
        instance.save()
        return instance

    def to_representation(self, instance):
        return RecipeGetSerializer(
            instance, context={'request': self.context.get('request')}
        ).data


class SubscriptionGetSerializer(serializers.ModelSerializer):
    is_subscribed = serializers.SerializerMethodField()
    recipes = serializers.SerializerMethodField()
    recipes_count = serializers.SerializerMethodField()
    avatar = Base64ImageField()

    class Meta:
        model = User
        fields = ('email', 'id', 'username', 'first_name', 'last_name',
                  'is_subscribed', 'recipes', 'recipes_count', 'avatar')

    def get_recipes(self, obj):
        request = self.context.get('request')
        recipes_limit = request.query_params.get('recipes_limit')
        recipes = obj.recipes.all()
        if recipes_limit:
            recipes = recipes[:int(recipes_limit)]
        serializer = RecipeShortSerializer(
            recipes,
            many=True,
            context={'request': request}
        )
        return serializer.data

    def get_is_subscribed(self, obj):
        user = self.context.get('request').user
        return (
            Subscription.objects.filter(user=user.id, author=obj.id).exists()
            and user.is_authenticated
        )

    def get_recipes_count(self, obj):
        return obj.recipes.count()


class SubscriptionPostSerializer(serializers.ModelSerializer):
    user = serializers.HiddenField(default=serializers.CurrentUserDefault())
    author = serializers.PrimaryKeyRelatedField(
        queryset=User.objects.all())

    class Meta:
        model = Subscription
        fields = ('user', 'author')

    def to_representation(self, instance):
        return SubscriptionGetSerializer(
            instance.author, context={'request': self.context.get('request')}
        ).data

    def validate(self, data):
        if Subscription.objects.filter(
            user=data['user'], author=data['author']
        ).exists():
            raise serializers.ValidationError(
                {'errors': f'Вы уже подписаны на {data["author"]}!'}
            )
        if data['user'] == data['author']:
            raise serializers.ValidationError(
                {'errors': 'Вы не можете подписаться на себя!'}
            )
        return data


class BaseSerializer(serializers.ModelSerializer):
    user = serializers.HiddenField(default=serializers.CurrentUserDefault())

    class Meta:
        abstract = True
        fields = ('user', 'recipe')

    def to_representation(self, instance):
        return RecipeShortSerializer(
            instance.recipe, context={'request': self.context.get('request')}
        ).data

    def validate(self, data):
        if self.Meta.model.objects.filter(
            user=data['user'], recipe=data['recipe']
        ).exists():
            raise serializers.ValidationError(
                {'errors': f'Рецепт уже добавлен в '
                 f'{self.Meta.model._meta.verbose_name}!'}
            )
        return data


class FavoriteSerializer(BaseSerializer):
    class Meta(BaseSerializer.Meta):
        model = Favorite


class ShoppingListSerializer(BaseSerializer):
    class Meta(BaseSerializer.Meta):
        model = ShoppingList
