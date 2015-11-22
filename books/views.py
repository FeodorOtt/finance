from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.core.urlresolvers import reverse
from django.db.models import Sum
from django.shortcuts import redirect
from django.shortcuts import render

from books.models import Transaction
from books import forms


@login_required
def transaction_list(request):
    user_id = request.user.id
    user = User.objects.get(id=user_id)
    user_transactions = Transaction.objects \
        .filter(user=user) \
        .order_by('-id')

    ctx = {}
    ctx['user'] = user
    ctx['transactions'] = user_transactions
    ctx['negative_transaction_sum'] = user_transactions \
        .filter(category=Transaction.EXPENSE) \
        .aggregate(Sum('amount')).get('amount__sum')
    ctx['positive_transaction_sum'] = user_transactions \
        .filter(category=Transaction.INCOME) \
        .aggregate(Sum('amount')).get('amount__sum')
    print(ctx['positive_transaction_sum'], ctx['negative_transaction_sum'])
    return render(request, 'transaction_list.html', context=ctx)


@login_required
def transaction_create(request):
    if request.method == "POST":
        form = forms.TransactionForm(request.POST)
        if form.is_valid():
            form.instance.user = request.user
            form.save()
            return redirect(reverse('transaction_list'))
    else:
        form = forms.TransactionForm()

    return render(request, 'transaction_create.html', {'form': form})
