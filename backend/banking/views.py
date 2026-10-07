"""
2.1 User-facing APIs.

Account/Transaction creation does not write directly to the tables -- it is
handed to the intake service, which runs the data review script and either
migrates it or parks it in the human review table.

Access is scoped by role (see banking.permissions): admins see/manage
everything; a regular user only sees their own linked account and the
transactions touching it, and can only move money out of their own account.
"""

from django.db.models import Q
from rest_framework import generics, status
from rest_framework.exceptions import PermissionDenied
from rest_framework.response import Response
from rest_framework.views import APIView

from banking.models import Account, HumanReview, Transaction
from banking.permissions import is_admin, owned_account_id, require_admin
from banking.serializers import (
    AccountSerializer, HumanReviewSerializer, TransactionSerializer,
)
from banking.services import intake, resolution


def _intake_response(result):
    if result.status == 'MIGRATED':
        serializer_cls = AccountSerializer if isinstance(result.entity, Account) else TransactionSerializer
        return Response(serializer_cls(result.entity).data, status=status.HTTP_201_CREATED)
    return Response(
        {
            'status': 'PENDING_REVIEW',
            'review': HumanReviewSerializer(result.review).data,
            'reasons': result.reasons,
        },
        status=status.HTTP_202_ACCEPTED,
    )


class AccountListCreateView(APIView):
    def get(self, request):
        if is_admin(request.user):
            accounts = Account.objects.all().order_by('account_id')
        else:
            accounts = Account.objects.filter(pk=owned_account_id(request.user))
        return Response(AccountSerializer(accounts, many=True).data)

    def post(self, request):
        require_admin(request)
        result = intake.submit_account(request.data, source=HumanReview.Source.API)
        return _intake_response(result)


class AccountDetailView(generics.RetrieveAPIView):
    serializer_class = AccountSerializer
    lookup_field = 'pk'
    lookup_url_kwarg = 'account_id'

    def get_queryset(self):
        if is_admin(self.request.user):
            return Account.objects.all()
        return Account.objects.filter(pk=owned_account_id(self.request.user))


class TransactionListCreateView(APIView):
    def get(self, request):
        if is_admin(request.user):
            transactions = Transaction.objects.all().order_by('-timestamp')
        else:
            own_id = owned_account_id(request.user)
            transactions = Transaction.objects.filter(
                Q(from_account_id=own_id) | Q(to_account_id=own_id)
            ).order_by('-timestamp')
        return Response(TransactionSerializer(transactions, many=True).data)

    def post(self, request):
        if not is_admin(request.user):
            own_id = owned_account_id(request.user)
            from_account = str(request.data.get('fromAccount') or '').strip()
            if from_account and from_account != own_id:
                raise PermissionDenied('You can only send money from your own account.')
        result = intake.submit_transaction(request.data, source=HumanReview.Source.API)
        return _intake_response(result)


class TransactionDetailView(generics.RetrieveAPIView):
    serializer_class = TransactionSerializer
    lookup_field = 'pk'
    lookup_url_kwarg = 'transaction_id'

    def get_queryset(self):
        if is_admin(self.request.user):
            return Transaction.objects.all()
        own_id = owned_account_id(self.request.user)
        return Transaction.objects.filter(Q(from_account_id=own_id) | Q(to_account_id=own_id))


class HumanReviewListView(generics.ListAPIView):
    serializer_class = HumanReviewSerializer

    def get_queryset(self):
        require_admin(self.request)
        qs = HumanReview.objects.all().order_by('-created_at')
        status_filter = self.request.query_params.get('status')
        if status_filter:
            qs = qs.filter(status=status_filter.upper())
        return qs


class HumanReviewDetailView(generics.RetrieveAPIView):
    queryset = HumanReview.objects.all()
    serializer_class = HumanReviewSerializer

    def get_queryset(self):
        require_admin(self.request)
        return HumanReview.objects.all()


class HumanReviewAddView(APIView):
    """Admin approves (optionally with corrections) -> back through review script."""

    def post(self, request, pk):
        require_admin(request)
        review = generics.get_object_or_404(HumanReview, pk=pk)
        result = resolution.add_review(
            review,
            overrides=request.data.get('overrides'),
            resolved_by=request.data.get('resolved_by', '') or request.user.username,
        )
        if result.status == 'MIGRATED':
            serializer_cls = AccountSerializer if review.entity_type == HumanReview.EntityType.ACCOUNT else TransactionSerializer
            return Response(
                {'status': result.status, 'entity': serializer_cls(result.entity).data},
                status=status.HTTP_200_OK,
            )
        return Response(
            {'status': result.status, 'reasons': result.reasons, 'review': HumanReviewSerializer(review).data},
            status=status.HTTP_200_OK,
        )


class HumanReviewRemoveView(APIView):
    """Admin rejects the record outright -- discarded, never migrated."""

    def post(self, request, pk):
        require_admin(request)
        review = generics.get_object_or_404(HumanReview, pk=pk)
        result = resolution.remove_review(
            review, resolved_by=request.data.get('resolved_by', '') or request.user.username,
        )
        return Response({'status': result.status}, status=status.HTTP_200_OK)
