import os
import json
from PIL import Image
from django.contrib.auth.models import AbstractUser
from django.db import models
from django.core.exceptions import ValidationError
from django.dispatch import receiver
from django.db.models.signals import pre_save, pre_delete, post_save


# Custom validator for minimum size of images
def validate_image_size(image):
    img = Image.open(image)
    fw, fh = img.size
    if image.file.size > 2 * 1024 * 1024:
        raise ValidationError(
            'Image size is larger than what is allowed (2048 KBs)')
    if fw < 128 or fh < 128:
        raise ValidationError(
            'Height or Width is smaller than what is allowed (128x128)')
    if fw > 1920 or fh > 1920:
        raise ValidationError(
            'Height or Width is larger than what is allowed (1920x1920)')


# Create directory for each user to upload files
def user_avatar_path(instance, filename):
    _, file_ext = os.path.splitext(filename)
    return f'user_{instance.id}/avatar/md{file_ext}'


class User(AbstractUser):
    avatar = models.ImageField(
        upload_to=user_avatar_path, default='avatar.jpg', validators=[validate_image_size])
    email = models.EmailField(unique=True, blank=True, null=False)

    # def __str__(self):
    #     return self.username

    # def get_avatar(self):
    #     if self.avatar.name:
    #         _, file_ext = os.path.splitext(self.avatar.name)
    #         return f'user_{self.id}/avatar/full{file_ext}'
    #     return False

    def get_total_transactions(self):
        return self.transactions.count()

    def get_balance(self):
        return self.balance.first().amount

    def get_total_income(self):
        income = self.transactions.filter(
            source='income').aggregate(models.Sum('amount'))
        if income['amount__sum'] == None:
            return 0.0
        else:
            return income['amount__sum']

    def get_total_expense(self):
        income = self.transactions.filter(
            source='expense').aggregate(models.Sum('amount'))
        if income['amount__sum'] == None:
            return 0.0
        else:
            return income['amount__sum']

    def get_report_amount_from_category(self, source):
        categories = Category.objects.filter(user=self, source=source).all()
        categories_titles = []
        categories_amounts = []
        category_report = {}
        for c in categories:
            categories_titles.append(c.title)
            categories_amounts.append(c.get_balance_from_category())
        category_report['titles'] = categories_titles
        category_report['amounts'] = categories_amounts
        return category_report


class Category(models.Model):
    INCOME = 'income'
    EXPENSE = 'expense'

    TYPES = (
        (INCOME, INCOME),
        (EXPENSE, EXPENSE),
    )

    class Meta:
        ordering = ['title']
        verbose_name_plural = "categories"

    title = models.CharField(max_length=128)
    source = models.CharField(max_length=255, choices=TYPES, default=INCOME)
    user = models.ForeignKey(
        User, related_name='categories', on_delete=models.CASCADE)
    created = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        if self.source == 'income':
            return f'(+) {self.title}'
        if self.source == 'expense':
            return f'(-) {self.title}'

    def get_balance_from_category(self):
        amount = Transaction.objects.filter(category=self, user=self.user).aggregate(
            models.Sum('amount'))['amount__sum']
        if amount:
            return amount
        else:
            return 0.0


class Transaction(models.Model):
    INCOME = 'income'
    EXPENSE = 'expense'

    TYPES = (
        (INCOME, INCOME),
        (EXPENSE, EXPENSE),
    )
    text = models.CharField(max_length=255)
    source = models.CharField(max_length=255, choices=TYPES, default=INCOME)
    category = models.ForeignKey(
        Category, related_name='category', blank=True, null=True, on_delete=models.CASCADE)
    amount = models.FloatField()
    user = models.ForeignKey(
        User, related_name='transactions', on_delete=models.CASCADE)
    created = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ('-created',)

    # def __str__(self):
    #     words = self.text.split(' ')
    #     if len(words) > 10:
    #         return ' '.join(words[0:10]) + ' ...'
    #     else:
    #         return ' '.join(words[0:10])


@receiver(pre_save, sender=Transaction)
def update_balance(sender, instance, **kwargs):
    #  Auto convert minus/plus in conjunction with category
    if instance.category:
        if instance.category.source == 'income':
            instance.source = 'income'
            if instance.amount < 0:
                instance.amount = -instance.amount
        elif instance.category.source == 'expense':
            instance.source = 'expense'
            if instance.amount > 0:
                instance.amount = -instance.amount
    else:
        if instance.amount > 0:
            instance.source = 'income'
        elif instance.amount < 0:
            instance.source = 'expense'

    balance = instance.user.balance.first()
    balance.amount = balance.amount + instance.amount

    if balance.amount == 0:
        raise ValidationError(
            'The ammount should be different from 0.')
    if balance.amount < 0:
        raise ValidationError(
            'Your balance is insufficient.')
    balance.save()


@receiver(pre_delete, sender=Transaction)
def pre_deleted_transaction(sender, instance, using, **kwargs):
    balance = instance.user.balance.first()
    balance.amount = balance.amount - instance.amount
    if balance.amount < 0:
        raise ValidationError(
            'Your balance is insufficient.')
    balance.save()


class Balance(models.Model):
    amount = models.FloatField(default=0.0)
    created = models.DateTimeField(auto_now_add=True)
    user = models.ForeignKey(
        User, related_name='balance', on_delete=models.CASCADE)
    updated = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f'$ {self.amount}'


@receiver(post_save, sender=User)
def initialize_balance(sender, instance, created, **kwargs):
    if created:
        balance = Balance(user=instance)
        balance.save()
