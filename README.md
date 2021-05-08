# Expensify

[![Expensify](https://github.com/infantiablue/expensify/actions/workflows/django.yml/badge.svg)](https://github.com/infantiablue/expensify/actions/workflows/django.yml) [![codecov](https://codecov.io/gh/infantiablue/expensify/branch/main/graph/badge.svg?token=T9JT3Y71PO)](https://codecov.io/gh/infantiablue/expensify)

## The Application

The main idea of the project is to build a personal expense/income tracker. It's pretty straight forward with some core functions:

- Add expense/income transaction
- Remove transaction (AJAX)
- Create category for transactions
- Remove category (AJAX)
- The user can see transactions per category
- The user can check balance, total income, total expense at a glance
- There are pretty charts to review past transactions
- Mobile friendly

It may not be the most complex capstone project you ever seen but I still got some nice techincal challenges to solve (and learnt) such as:

- Separeate controllers and views, all logic functions such as update balance, calculate sum of income/expense ... and validators are handled in model classes as object methods. As the result, the views only handle user input and presentation layer.
- All the user interface is written in vanilla javascript. The reason is not because I can't implement React (you can check out the project 4 - Network to see my implementation of Reat with Babel) or I dislike the framework. The thing is I want to understand 100% what I've written in the front end. Many concepts in React is interesting and useful but it's really challenging to comprehend (even easy to use).
- Last but not least, I've reached to coverage 100% all code with unit test. It's not an huge achievement but this result took me a lot of efforts, but I really enjoyed the approach Test Driven Developemnt. This approach help me more confident to add more features as well as understanding deeply what's going on with my code base.

## The Big Lesson

In this final project, I've learnt many things yet the most crucial lesson is how to separate business logic (Models) with the views. At the beginning, in order to initialize new balance and validate the input amount is income or expense, I've processed in the `views.py` file like this:

```python
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
            ###BAD PRACTICE BEGIN###
            balance = Balance(user=user)
            balance.save()
            ###END OF BAD PRACTICE###
            user.save()
        except IntegrityError:
            return render(request, 'tracker/register.html', {
                'message': 'Username already taken.'
            })
        login(request, user)
        return HttpResponseRedirect(reverse('index'))
    else:
        return render(request, 'tracker/register.html')

@login_required(login_url='login')
def index(request):
    form = NewTransactionForm(request)
    transactions = request.user.transactions
    context = {'transactions': transactions.all(), 'form': form}
    if request.method == 'POST':
        new_form = NewTransactionForm(request, request.POST)
        if new_form.is_valid():
            transaction = new_form.save(commit=False)
            transaction.user = request.user
            source = ''
            ###BAD PRACTICE BEGIN###
            if transaction.category.source == 'income':
                source = 'income'
                if transaction.amount < 0:
                    transaction.amount = -transaction.amount
            elif transaction.category.source == 'expense':
                source = 'expense'
                if transaction.amount > 0:
                    transaction.amount = -transaction.amount
            else:
                if transaction.amount > 0:
                    source = 'income'
                elif transaction.amount < 0:
                    source = 'expense'
            ###END OF BAD PRACTICE###
            transaction.source = source
            try:
                transaction.save()
                messages.success(
                    request, 'Your transaction has been recorded.')
            except ValidationError as e:
                messages.error(request, e.message)
            return HttpResponseRedirect(reverse('index'))

    return render(request, 'tracker/index.html', context)
```

Turns out, this is the bad practice. I just realized this scenario when make test case for new transaction as below

```python
def test_transactions_with_category(self):
        cat_income = Category(title='Interest', user=self.user)
        cat_expense = Category(
            title='Utilities', source='expense', user=self.user)
        cat_income.save()
        cat_expense.save()
        transaction1 = Transaction(
            text='income_1', amount=500, category=cat_income, user=self.user)
        transaction2 = Transaction(
            text='expense_1', amount=200, category=cat_expense, user=self.user)
        transaction1.save()
        transaction2.save()
        self.assertEqual(self.user.get_balance(), 300)
```

As the unit test deal directly with business logic in Model layer, so the balance has not been updated as exptected. Of course, we can make this works by posting directly to the form yet it is not the proper way. Fortunately, Django gives us very powerful mechanism to hook up post or pre update/insert/delete database with `Signals` After examining [the official Django documentation](https://docs.djangoproject.com/en/3.2/topics/signals/), it's prettys straigt forward to move all business logic into Model layer with `post_save` and `pre_save` signals

```python
@receiver(post_save, sender=User)
def initialize_balance(sender, instance, created, **kwargs):
    if created:
          balance = Balance(user=instance)
          balance.save()

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
```

The first function `initialize_balance` create a new `Balance` object whenever a new user is created. The `created` param is critical, and needed to be passed in order to check if the user is created or updated. Without it, many `Balance` object will be created.

After implementing this approach, my code base is cleaner and more coherent, and it's easier for me to make tests among business logic and views.