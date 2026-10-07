"""
Creates demo logins on top of whatever accounts/transactions have already
been migrated: one admin login, and one user login per bank Account
(username = account_id) so each customer can log in as themselves.

Usage:
    python manage.py seed_users
    python manage.py seed_users --password mypassword --admin-password adminpw
"""

from django.contrib.auth.models import User
from django.core.management.base import BaseCommand

from banking.models import Account, Profile


class Command(BaseCommand):
    help = 'Seed an admin login and one user login per Account for demo purposes.'

    def add_arguments(self, parser):
        parser.add_argument('--password', default='password123', help='Password for seeded account-holder logins.')
        parser.add_argument('--admin-username', default='admin')
        parser.add_argument('--admin-password', default='admin123')

    def handle(self, *args, **options):
        admin_user, created = User.objects.get_or_create(
            username=options['admin_username'],
            defaults={'is_staff': True, 'is_superuser': True},
        )
        admin_user.set_password(options['admin_password'])
        admin_user.is_staff = True
        admin_user.save()
        Profile.objects.update_or_create(user=admin_user, defaults={'role': Profile.Role.ADMIN, 'account': None})
        self.stdout.write(self.style.SUCCESS(
            f'admin login: {options["admin_username"]} / {options["admin_password"]}'
        ))

        created_count = 0
        for account in Account.objects.all().order_by('account_id'):
            user, _ = User.objects.get_or_create(
                username=account.account_id,
                defaults={'first_name': account.customer_name},
            )
            user.set_password(options['password'])
            user.first_name = account.customer_name
            user.save()
            Profile.objects.update_or_create(user=user, defaults={'role': Profile.Role.USER, 'account': account})
            created_count += 1

        self.stdout.write(self.style.SUCCESS(
            f'{created_count} user login(s) seeded, username = accountId, password = {options["password"]!r}'
        ))
