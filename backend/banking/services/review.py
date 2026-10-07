"""
2.2 Data review script.

Validates a raw account/transaction record (same shape whether it came from
a user API call or a row of a CSV file) and reports whether it is safe to
migrate straight into the tables, or whether it needs to go to human review.

Records use the CSV column names as their wire format (accountId,
fromAccount, etc.) so the same validation code serves both the API and the
CSV migration script.
"""

from dataclasses import dataclass, field
from datetime import datetime
from decimal import Decimal, InvalidOperation

from django.utils import timezone

from banking.models import Account, Transaction


@dataclass
class ReviewResult:
    is_valid: bool
    reasons: list = field(default_factory=list)
    # Parsed/normalized values, only fully populated when is_valid is True.
    cleaned: dict = field(default_factory=dict)


def _parse_decimal(value, reasons, field_name, *, allow_zero=True):
    try:
        amount = Decimal(str(value).strip())
    except (InvalidOperation, AttributeError, TypeError):
        reasons.append(f'{field_name} "{value}" is not a valid number')
        return None
    if amount < 0 or (amount == 0 and not allow_zero):
        reasons.append(f'{field_name} {amount} must be {"non-negative" if allow_zero else "positive"}')
        return None
    return amount


def review_account(payload: dict) -> ReviewResult:
    reasons = []
    cleaned = {}

    account_id = str(payload.get('accountId') or '').strip()
    if not account_id:
        reasons.append('accountId is required')
    cleaned['accountId'] = account_id

    customer_name = str(payload.get('customerName') or '').strip()
    if not customer_name:
        reasons.append('customerName is required')
    cleaned['customerName'] = customer_name

    account_type = str(payload.get('accountType') or '').strip().upper()
    if account_type not in Account.AccountType.values:
        reasons.append(f'accountType "{payload.get("accountType")}" is not one of {Account.AccountType.values}')
    cleaned['accountType'] = account_type

    status = str(payload.get('status') or '').strip().upper()
    if status not in Account.Status.values:
        reasons.append(f'status "{payload.get("status")}" is not one of {Account.Status.values}')
    cleaned['status'] = status

    cleaned['balance'] = _parse_decimal(payload.get('balance'), reasons, 'balance')
    cleaned['dailyLimit'] = _parse_decimal(payload.get('dailyLimit'), reasons, 'dailyLimit')

    currency = str(payload.get('currency') or '').strip().upper()
    if len(currency) != 3:
        reasons.append(f'currency "{payload.get("currency")}" is not a 3-letter currency code')
    cleaned['currency'] = currency

    opened_date_raw = str(payload.get('openedDate') or '').strip()
    try:
        cleaned['openedDate'] = datetime.strptime(opened_date_raw, '%Y-%m-%d').date()
    except ValueError:
        reasons.append(f'openedDate "{opened_date_raw}" is not a valid YYYY-MM-DD date')
        cleaned['openedDate'] = None

    return ReviewResult(is_valid=len(reasons) == 0, reasons=reasons, cleaned=cleaned)


_DEBIT_TYPES = {Transaction.Type.WITHDRAWAL, Transaction.Type.PURCHASE, Transaction.Type.TRANSFER}
_REQUIRES_FROM = {Transaction.Type.WITHDRAWAL, Transaction.Type.PURCHASE, Transaction.Type.TRANSFER}
_REQUIRES_TO = {Transaction.Type.DEPOSIT, Transaction.Type.TRANSFER}


def _lookup_account(account_id, role, reasons):
    """Look up an account referenced by a transaction, flagging missing/inactive accounts."""
    if not account_id:
        return None
    try:
        account = Account.objects.get(pk=account_id)
    except Account.DoesNotExist:
        reasons.append(f'{role} "{account_id}" does not exist')
        return None
    if account.status != Account.Status.ACTIVE:
        reasons.append(f'{role} "{account_id}" is {account.status}, not ACTIVE')
    return account


def review_transaction(payload: dict, *, exclude_transaction_id=None) -> ReviewResult:
    reasons = []
    cleaned = {}

    transaction_id = str(payload.get('transactionId') or '').strip()
    if not transaction_id:
        reasons.append('transactionId is required')
    cleaned['transactionId'] = transaction_id

    existing = Transaction.objects.filter(pk=transaction_id).exclude(pk=exclude_transaction_id).first() if transaction_id else None
    if existing is not None:
        reasons.append(f'transactionId "{transaction_id}" already exists')

    timestamp_raw = str(payload.get('timestamp') or '').strip()
    try:
        parsed_timestamp = datetime.fromisoformat(timestamp_raw)
        if timezone.is_naive(parsed_timestamp):
            parsed_timestamp = timezone.make_aware(parsed_timestamp)
        cleaned['timestamp'] = parsed_timestamp
    except ValueError:
        reasons.append(f'timestamp "{timestamp_raw}" is not a valid ISO-8601 timestamp')
        cleaned['timestamp'] = None

    tx_type = str(payload.get('type') or '').strip().upper()
    if tx_type not in Transaction.Type.values:
        reasons.append(f'type "{payload.get("type")}" is not one of {Transaction.Type.values}')
        tx_type = None
    cleaned['type'] = tx_type

    channel = str(payload.get('channel') or '').strip().upper()
    if channel not in Transaction.Channel.values:
        reasons.append(f'channel "{payload.get("channel")}" is not one of {Transaction.Channel.values}')
    cleaned['channel'] = channel

    amount = _parse_decimal(payload.get('amount'), reasons, 'amount', allow_zero=False)
    cleaned['amount'] = amount

    from_account_id = str(payload.get('fromAccount') or '').strip()
    to_account_id = str(payload.get('toAccount') or '').strip()

    if tx_type in _REQUIRES_FROM and not from_account_id:
        reasons.append(f'{tx_type} requires fromAccount')
    if tx_type in _REQUIRES_TO and not to_account_id:
        reasons.append(f'{tx_type} requires toAccount')
    if tx_type == Transaction.Type.REVERSAL and not from_account_id and not to_account_id:
        reasons.append('REVERSAL requires fromAccount and/or toAccount')
    if from_account_id and to_account_id and from_account_id == to_account_id:
        reasons.append('fromAccount and toAccount must not be the same account')

    from_account = _lookup_account(from_account_id, 'fromAccount', reasons)
    to_account = _lookup_account(to_account_id, 'toAccount', reasons)
    cleaned['fromAccount'] = from_account_id
    cleaned['toAccount'] = to_account_id

    if amount is not None and tx_type in _DEBIT_TYPES and from_account is not None:
        if amount > from_account.balance:
            reasons.append(f'amount {amount} exceeds fromAccount balance {from_account.balance}')
        if amount > from_account.daily_limit:
            reasons.append(f'amount {amount} exceeds fromAccount dailyLimit {from_account.daily_limit}')

    cleaned['description'] = str(payload.get('description') or '').strip()

    return ReviewResult(is_valid=len(reasons) == 0, reasons=reasons, cleaned=cleaned)
