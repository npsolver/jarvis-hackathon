from django.contrib import admin

from banking.models import Account, HumanReview, Profile, Transaction


@admin.register(Account)
class AccountAdmin(admin.ModelAdmin):
    list_display = ('account_id', 'customer_name', 'account_type', 'status', 'balance', 'daily_limit', 'currency')
    search_fields = ('account_id', 'customer_name')
    list_filter = ('account_type', 'status', 'currency')


@admin.register(Transaction)
class TransactionAdmin(admin.ModelAdmin):
    list_display = ('transaction_id', 'timestamp', 'type', 'from_account', 'to_account', 'amount', 'channel')
    search_fields = ('transaction_id',)
    list_filter = ('type', 'channel')


@admin.register(HumanReview)
class HumanReviewAdmin(admin.ModelAdmin):
    list_display = ('id', 'entity_type', 'status', 'source', 'created_at', 'resolved_by')
    list_filter = ('entity_type', 'status', 'source')
    readonly_fields = ('created_at', 'updated_at')


@admin.register(Profile)
class ProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'role', 'account')
    list_filter = ('role',)
