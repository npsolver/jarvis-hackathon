from django.conf import settings
from django.db import models


class Account(models.Model):
    class AccountType(models.TextChoices):
        CHEQUING = 'CHEQUING'
        SAVINGS = 'SAVINGS'

    class Status(models.TextChoices):
        ACTIVE = 'ACTIVE'
        FROZEN = 'FROZEN'
        CLOSED = 'CLOSED'
        DORMANT = 'DORMANT'

    account_id = models.CharField(primary_key=True, max_length=32)
    customer_name = models.CharField(max_length=255)
    account_type = models.CharField(max_length=16, choices=AccountType.choices)
    status = models.CharField(max_length=16, choices=Status.choices)
    balance = models.DecimalField(max_digits=14, decimal_places=2)
    daily_limit = models.DecimalField(max_digits=14, decimal_places=2)
    currency = models.CharField(max_length=8, default='CAD')
    opened_date = models.DateField()

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f'{self.account_id} ({self.customer_name})'


class Transaction(models.Model):
    class Type(models.TextChoices):
        TRANSFER = 'TRANSFER'
        PURCHASE = 'PURCHASE'
        WITHDRAWAL = 'WITHDRAWAL'
        DEPOSIT = 'DEPOSIT'
        REVERSAL = 'REVERSAL'

    class Channel(models.TextChoices):
        ONLINE = 'ONLINE'
        POS = 'POS'
        ATM = 'ATM'
        PARTNER_FI = 'PARTNER_FI'

    transaction_id = models.CharField(primary_key=True, max_length=32)
    timestamp = models.DateTimeField()
    type = models.CharField(max_length=16, choices=Type.choices)
    from_account = models.ForeignKey(
        Account, null=True, blank=True, on_delete=models.PROTECT,
        related_name='outgoing_transactions',
    )
    to_account = models.ForeignKey(
        Account, null=True, blank=True, on_delete=models.PROTECT,
        related_name='incoming_transactions',
    )
    amount = models.DecimalField(max_digits=14, decimal_places=2)
    channel = models.CharField(max_length=16, choices=Channel.choices)
    description = models.CharField(max_length=255, blank=True, default='')

    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f'{self.transaction_id} {self.type} {self.amount}'


class HumanReview(models.Model):
    class EntityType(models.TextChoices):
        ACCOUNT = 'ACCOUNT'
        TRANSACTION = 'TRANSACTION'

    class Status(models.TextChoices):
        PENDING = 'PENDING'
        APPROVED = 'APPROVED'
        REJECTED = 'REJECTED'

    class Source(models.TextChoices):
        API = 'API'
        CSV_IMPORT = 'CSV_IMPORT'

    entity_type = models.CharField(max_length=16, choices=EntityType.choices)
    payload = models.JSONField()
    reasons = models.JSONField(default=list)
    status = models.CharField(max_length=16, choices=Status.choices, default=Status.PENDING)
    source = models.CharField(max_length=16, choices=Source.choices, default=Source.API)

    resolved_by = models.CharField(max_length=255, blank=True, default='')
    resolved_at = models.DateTimeField(null=True, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f'{self.entity_type} review #{self.pk} [{self.status}]'


class Profile(models.Model):
    """Links a login (Django User) to a role and, for regular users, the
    one bank Account they are allowed to act as."""

    class Role(models.TextChoices):
        USER = 'USER'
        ADMIN = 'ADMIN'

    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='profile')
    role = models.CharField(max_length=16, choices=Role.choices, default=Role.USER)
    account = models.OneToOneField(
        Account, null=True, blank=True, on_delete=models.SET_NULL, related_name='profile',
    )

    def __str__(self):
        return f'{self.user.username} [{self.role}]'
