"""
CSV migration script: loads accounts.csv and transactions.csv through the
exact same review -> migrate / send-to-review path used by the user APIs.

Usage:
    python manage.py import_csv --accounts ../accounts.csv --transactions ../transactions.csv
"""

import csv
from pathlib import Path

from django.conf import settings
from django.core.management.base import BaseCommand

from banking.models import HumanReview
from banking.services import intake

DEFAULT_ACCOUNTS_CSV = Path(settings.BASE_DIR).parent / 'accounts (1).csv'
DEFAULT_TRANSACTIONS_CSV = Path(settings.BASE_DIR).parent / 'transactions (1).csv'


class Command(BaseCommand):
    help = 'Migrate accounts.csv and transactions.csv through the data review script.'

    def add_arguments(self, parser):
        parser.add_argument('--accounts', default=str(DEFAULT_ACCOUNTS_CSV))
        parser.add_argument('--transactions', default=str(DEFAULT_TRANSACTIONS_CSV))

    def handle(self, *args, **options):
        self._import_rows(
            options['accounts'], intake.submit_account, 'accountId', 'account(s)',
        )
        self._import_rows(
            options['transactions'], intake.submit_transaction, 'transactionId', 'transaction(s)',
        )

    def _import_rows(self, csv_path, submit_fn, id_field, label):
        csv_path = Path(csv_path)
        if not csv_path.exists():
            self.stderr.write(self.style.ERROR(f'{csv_path} not found, skipping'))
            return

        migrated = 0
        sent_to_review = 0

        with csv_path.open(newline='', encoding='utf-8') as f:
            for row in csv.DictReader(f):
                result = submit_fn(row, source=HumanReview.Source.CSV_IMPORT)
                if result.status == 'MIGRATED':
                    migrated += 1
                else:
                    sent_to_review += 1
                    self.stdout.write(
                        f'  -> review #{result.review.pk} {row.get(id_field)}: {"; ".join(result.reasons)}'
                    )

        self.stdout.write(self.style.SUCCESS(
            f'{csv_path.name}: migrated {migrated} {label}, sent {sent_to_review} to human review'
        ))
