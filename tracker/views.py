import os
import shutil
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.core.exceptions import ValidationError
from django.db import IntegrityError
from django.http import HttpResponseRedirect
from django.shortcuts import render
from django.urls import reverse
from .models import Category, User
from django.shortcuts import render
from .forms import NewTransactionForm, UserForm, CategoryForm
from django.conf import settings


@login_required(login_url='login')
def index(request):
    context = {
        'transactions': request.user.transactions.all()[:5],
    }

    if request.method == 'GET':
        form = NewTransactionForm(request.user)

    if request.method == 'POST':
        form = NewTransactionForm(request.user, request.POST)
        if form.is_valid():
            transaction = form.save(commit=False)
            transaction.user = request.user
            try:
                transaction.save()
                messages.success(
                    request, 'Your transaction has been recorded.')
            except ValidationError as e:
                messages.error(request, e.message)
            return HttpResponseRedirect(reverse('index'))

    context['form'] = form
    return render(request, 'tracker/index.html', context)


@login_required(login_url='login')
def transactions(request):
    context = {
        'transactions': request.user.transactions.all()[:5],
        'form': NewTransactionForm(request.user)
    }
    return render(request, 'tracker/transactions.html', context)


@login_required(login_url='login')
def categories(request):
    form = CategoryForm()
    context = {'form': form}
    if request.method == 'POST':
        new_category_form = CategoryForm(request.POST)
        if new_category_form.is_valid():
            new_category = new_category_form.save(commit=False)
            new_category.user = request.user
            new_category.save()
            messages.success(
                request, 'Your new category has been created.')
            return HttpResponseRedirect(reverse('categories'))
    categories = Category.objects.filter(user=request.user).all()
    context['categories'] = categories
    return render(request, 'tracker/categories.html', context)


@login_required(login_url='login')
def category(request, id):
    cat = Category.objects.get(pk=id)
    context = {'transactions': request.user.transactions.filter(
        category=cat)}
    context['category'] = cat
    return render(request, 'tracker/category.html', context)


@login_required(login_url='login')
def reports(request):
    return render(request, 'tracker/reports.html')


@login_required(login_url='login')
def account(request):
    if request.method == 'POST':
        form = UserForm(request.POST, request.FILES, instance=request.user)
        if form.is_valid():
            changed_user = form.save(commit=False)
            if request.FILES:
                # Handle uploading avatar
                from .utils import crop_smart
                _, ext = os.path.splitext(changed_user.avatar.name)
                thumb_path = f'{settings.MEDIA_ROOT}/user_{request.user.id}/avatar/md{ext}'
                old_path = f'{settings.MEDIA_ROOT}/user_{request.user.id}/avatar'
                # Remove old avatar files
                if os.path.exists(old_path):
                    shutil.rmtree(old_path)
                # Save to DB and upload file
                changed_user.save()
                # Keep the original one
                shutil.copy(thumb_path,
                            f'{settings.MEDIA_ROOT}/user_{request.user.id}/avatar/full{ext}')
                # Crop and repalce the old file with new size
                crop_smart(
                    thumb_path, thumb_path, 128, 128)
            else:
                changed_user.save()

            messages.success(
                request, 'Your account is updated succesfully.')
            return HttpResponseRedirect(reverse('account'))

    else:
        form = UserForm(instance=request.user)
    context = {'form': form}
    return render(request, 'tracker/account.html', context)


def login_view(request):
    if request.method == 'POST':
        # Attempt to sign user in
        username = request.POST['username']
        password = request.POST['password']
        user = authenticate(request, username=username, password=password)

        # Check if authentication successful
        if user is not None:
            login(request, user)
            return HttpResponseRedirect(reverse('index'))
        else:
            return render(request, 'tracker/login.html', {
                'message': 'Invalid username and/or password.'
            })
    else:
        return render(request, 'tracker/login.html')


def logout_view(request):
    logout(request)
    return HttpResponseRedirect(reverse('index'))


def register(request):
    if request.method == 'POST':
        username = request.POST['username']
        email = request.POST['email']

        # Ensure password matches confirmation
        password = request.POST['password']
        confirmation = request.POST['confirmation']
        if password != confirmation:
            return render(request, 'tracker/register.html', {
                'message': 'Passwords must match.'
            })

        # Attempt to create new user
        try:
            user = User.objects.create_user(username, email, password)
            user.save()
        except IntegrityError as e:
            if str(e.__cause__).find('email') != -1:
                msg = 'Email already taken.'
            if str(e.__cause__).find('user') != -1:
                msg = 'Username already taken.'
            return render(request, 'tracker/register.html', {
                'message': msg
            })
        login(request, user)
        return HttpResponseRedirect(reverse('index'))
    else:
        return render(request, 'tracker/register.html')
