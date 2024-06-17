from django.contrib.auth import get_user_model
from django.contrib.auth.models import AbstractUser
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models

from .constants import (MAX_LENGTH_MAIL, MAX_LENGTH_NAME,
                        MAX_LENGTH_RECIPE_NAME, MAX_LENGTH_TAG,
                        MAX_LENGTH_UNIT, MAX_LENGTH_USER_NAME, MAX_VALUE,
                        MIN_VALUE)


class FoodgramUser(AbstractUser):
    email = models.EmailField('@', max_length=MAX_LENGTH_MAIL, unique=True)
    first_name = models.CharField('Имя', max_length=MAX_LENGTH_USER_NAME)
    last_name = models.CharField('Фамилия', max_length=MAX_LENGTH_USER_NAME)
    avatar = models.ImageField('Аватар',
                               upload_to='users/',
                               null=True,
                               default=None)
    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['first_name', 'last_name', 'username']

    class Meta:
        verbose_name = 'Пользователь'
        verbose_name_plural = 'Пользователи'
        ordering = ('username',)


User = get_user_model()


class Ingredient(models.Model):
    name = models.CharField('Название', max_length=MAX_LENGTH_NAME)
    measurement_unit = models.CharField('Единица измерения',
                                        max_length=MAX_LENGTH_UNIT)

    class Meta:
        verbose_name = 'Ингредиент'
        verbose_name_plural = 'Ингредиенты'
        ordering = ('name',)

    def __str__(self):
        return self.name


class Tag(models.Model):
    name = models.CharField('Тег', max_length=MAX_LENGTH_TAG, unique=True)
    slug = models.SlugField('Слаг', max_length=MAX_LENGTH_TAG, unique=True)

    class Meta:
        verbose_name = 'Тег'
        verbose_name_plural = 'Теги'
        ordering = ('name',)

    def __str__(self):
        return self.name


class Recipe(models.Model):
    ingredients = models.ManyToManyField(
        Ingredient,
        verbose_name='Ингредиенты',
        through='IngredientInRecipe'
    )
    tags = models.ManyToManyField(Tag, verbose_name='Тег')
    image = models.ImageField('Изображение', upload_to='recipes/')
    name = models.CharField('Название', max_length=MAX_LENGTH_RECIPE_NAME)
    text = models.TextField('Описание')
    cooking_time = models.PositiveSmallIntegerField(
        'Время приготовления',
        validators=[MinValueValidator(MIN_VALUE), MaxValueValidator(MAX_VALUE)]
    )
    author = models.ForeignKey(
        User,
        verbose_name='Автор',
        on_delete=models.CASCADE,
    )
    pub_date = models.DateTimeField('Дата публикации', auto_now_add=True)

    class Meta:
        verbose_name = 'Рецепт'
        verbose_name_plural = 'Рецепты'
        default_related_name = 'recipes'
        ordering = ('-pub_date',)

    def __str__(self):
        return self.name


class IngredientInRecipe(models.Model):
    recipe = models.ForeignKey(
        Recipe,
        verbose_name='Рецепт',
        on_delete=models.CASCADE
    )
    ingredient = models.ForeignKey(
        Ingredient,
        verbose_name='Ингредиент',
        on_delete=models.CASCADE
    )
    amount = models.PositiveSmallIntegerField(
        'Количество',
        validators=[MinValueValidator(MIN_VALUE), MaxValueValidator(MAX_VALUE)]
    )

    class Meta:
        verbose_name = 'Ингредиенты рецепта'
        verbose_name_plural = 'Ингредиенты рецептов'
        default_related_name = 'ingridients_in_recipe'
        ordering = ('recipe',)
        constraints = [
            models.UniqueConstraint(
                fields=['recipe', 'ingredient'],
                name='unique_ingridients_in_recipe'
            )
        ]

    def __str__(self):
        return f'{self.ingredient} {self.amount}'


class Subscription(models.Model):
    user = models.ForeignKey(
        User,
        verbose_name='Пользователь',
        on_delete=models.CASCADE,
        related_name='subscriptions'
    )
    author = models.ForeignKey(
        User,
        verbose_name='Автор',
        on_delete=models.CASCADE,
        related_name='subscribers'
    )

    class Meta:
        verbose_name = 'Подписки'
        verbose_name_plural = 'Подписки'
        ordering = ('author',)
        constraints = [
            models.UniqueConstraint(
                fields=['user', 'author'], name='unique_subscription'
            ),
            models.CheckConstraint(
                check=~models.Q(user=models.F('author')),
                name='not_match_user_author'
            )
        ]

    def __str__(self):
        return f'{self.user} {self.author}'


class BaseRelation(models.Model):
    user = models.ForeignKey(
        User,
        verbose_name='Пользователь',
        on_delete=models.CASCADE,
    )
    recipe = models.ForeignKey(
        Recipe,
        verbose_name='Рецепт',
        on_delete=models.CASCADE,
    )

    class Meta:
        abstract = True
        ordering = ('user',)
        constraints = [
            models.UniqueConstraint(
                fields=['user', 'recipe'], name='unique_%(class)s'
            )
        ]

    def __str__(self):
        return f'{self.user} {self.recipe}'


class Favorite(BaseRelation):
    class Meta(BaseRelation.Meta):
        verbose_name = 'Избранное'
        verbose_name_plural = 'Избранное'
        default_related_name = 'favorites'


class ShoppingList(BaseRelation):
    class Meta(BaseRelation.Meta):
        verbose_name = 'Список покупок'
        verbose_name_plural = 'Список покупок'
        default_related_name = 'shopping_list'
