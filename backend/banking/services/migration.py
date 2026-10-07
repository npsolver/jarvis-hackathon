"""
2.3 Data migration script.

Takes a *cleaned* payload (the output of banking.services.review, once it is
valid) and writes it into the Account / Transaction tables.
"""

from django.db import transaction as db_transaction

from banking.models import Account, Transaction


def migrate_account(cleaned: dict) -> Account:
    account, _created = Account.objects.update_or_create(
        account_id=cleaned['accountId'],
        defaults={
            'customer_name': cleaned['customerName'],
            'account_type': cleaned['accountType'],
            'status': cleaned['status'],
            'balance': cleaned['balance'],
            'daily_limit': cleaned['dailyLimit'],
            'currency': cleaned['currency'],
            'opened_date': cleaned['openedDate'],
        },
    )
    return account


def _apply_balance_effects(tx_type, from_account, to_account, amount):
    if tx_type == Transaction.Type.DEPOSIT:
        to_account.balance += amount
        to_account.save(update_fields=['balance'])
    elif tx_type in (Transaction.Type.WITHDRAWAL, Transaction.Type.PURCHASE):
        from_account.balance -= amount
        from_account.save(update_fields=['balance'])
    elif tx_type == Transaction.Type.TRANSFER:
        from_account.balance -= amount
        to_account.balance += amount
        from_account.save(update_fields=['balance'])
        to_account.save(update_fields=['balance'])
    elif tx_type == Transaction.Type.REVERSAL:
        # A reversal undoes whichever side of the original movement is
        # present: refund the account that was debited, or claw back the
        # account that was credited.
        if from_account is not None:
            from_account.balance += amount
            from_account.save(update_fields=['balance'])
        elif to_account is not None:
            to_account.balance -= amount
            to_account.save(update_fields=['balance'])


def migrate_transaction(cleaned: dict) -> Transaction:
    transaction_id = cleaned['transactionId']

    with db_transaction.atomic():
        existing = Transaction.objects.filter(pk=transaction_id).first()
        if existing is not None:
            # Already migrated; treat as idempotent and skip re-applying
            # balance effects.
            return existing

        from_account = (
            Account.objects.select_for_update().get(pk=cleaned['fromAccount'])
            if cleaned.get('fromAccount') else None
        )
        to_account = (
            Account.objects.select_for_update().get(pk=cleaned['toAccount'])
            if cleaned.get('toAccount') else None
        )

        tx = Transaction.objects.create(
            transaction_id=transaction_id,
            timestamp=cleaned['timestamp'],
            type=cleaned['type'],
            from_account=from_account,
            to_account=to_account,
            amount=cleaned['amount'],
            channel=cleaned['channel'],
            description=cleaned.get('description', ''),
        )

        _apply_balance_effects(cleaned['type'], from_account, to_account, cleaned['amount'])

    return tx
