
import json
from datetime import timedelta
from django.utils import timezone
from django.http import JsonResponse
from django.db.models import Sum
from .models import Category, Transaction
from .utils import login_required_ajax
from django.core.serializers import serialize


@ login_required_ajax
def transaction(request):
    if request.method == 'DELETE':
        data = json.loads(request.body)
        transaction = Transaction.objects.get(pk=data['transaction_id'])
        if transaction.user == request.user:
            transaction.delete()
            return JsonResponse({'message': 'Your transaction is removed.'})
        else:
            return JsonResponse({'error': 'You are not authorized.'})

    return JsonResponse({'error': 'You are not authorized.'})


@ login_required_ajax
def reports(request):
    if request.method == 'GET':
        today = timezone.now()
        days_ago = today - timedelta(days=7)
        params = dict(request.GET)
        source = 'expense'
        if 'source' in params:
            source = params['source'][0]
        transactions = Transaction.objects.filter(
            source=source, user=request.user, created__gte=days_ago, created__lte=today).values('created__date').order_by('created__date').annotate(sum_amount=Sum('amount'))

        result = {'amounts': [], 'time': []}

        if transactions.count() > 0:
            for t in transactions:
                result['amounts'].append(t['sum_amount'])
                result['time'].append(t['created__date'])
        return JsonResponse(result)

    return JsonResponse({'error': 'You are not authorized.'})


@ login_required_ajax
def transactions(request):
    TRANSACTIONS_PER_PAGE = 5
    if request.method == 'GET':
        params = dict(request.GET)
        page = 1
        if 'page' in params:
            page = int(params['page'][0])
        transactions = request.user.transactions.all()[
            (page*TRANSACTIONS_PER_PAGE-TRANSACTIONS_PER_PAGE):((page+1)*TRANSACTIONS_PER_PAGE-TRANSACTIONS_PER_PAGE)]
        if transactions.count() > 0:
            return JsonResponse(list(transactions.values()), safe=False)
        else:
            return JsonResponse({'error': 'End of transactions.'})
    return JsonResponse({'error': 'You are not authorized.'})


@ login_required_ajax
def category(request):
    if request.method == 'DELETE':
        data = json.loads(request.body)
        category = Category.objects.get(pk=data['category_id'])
        if category.user == request.user:
            category.delete()
            return JsonResponse({'message': 'Your category is removed.'})
        else:
            return JsonResponse({'error': 'You are not authorized.'})

    if request.method == 'GET':
        params = dict(request.GET)
        source = 'expense'
        if 'source' in params:
            source = params['source'][0]
        return JsonResponse(request.user.get_report_amount_from_category(source))

    return JsonResponse({'error': 'You are not authorized.'})


@ login_required_ajax
def balance(request):
    if request.method == 'GET':
        return JsonResponse({'balance': request.user.get_balance()})
