from rest_framework import serializers

from banking.models import Account, HumanReview, Transaction


class AccountSerializer(serializers.ModelSerializer):
    class Meta:
        model = Account
        fields = [
            'account_id', 'customer_name', 'account_type', 'status',
            'balance', 'daily_limit', 'currency', 'opened_date',
            'created_at', 'updated_at',
        ]


class TransactionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Transaction
        fields = [
            'transaction_id', 'timestamp', 'type', 'from_account', 'to_account',
            'amount', 'channel', 'description', 'created_at',
        ]


class HumanReviewSerializer(serializers.ModelSerializer):
    class Meta:
        model = HumanReview
        fields = [
            'id', 'entity_type', 'payload', 'reasons', 'status', 'source',
            'resolved_by', 'resolved_at', 'created_at', 'updated_at',
        ]
