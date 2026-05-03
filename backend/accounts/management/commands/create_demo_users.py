"""
Management command: python manage.py create_demo_users

Creates demo accounts for testing all roles.
"""
from django.core.management.base import BaseCommand
from accounts.models import User


class Command(BaseCommand):
    help = 'Create demo users for all roles'

    def handle(self, *args, **options):
        users = [
            dict(email='admin@cats.gov.in', full_name='Super Admin', role=User.Role.SUPER_ADMIN,
                 password='admin123', station='HQ'),
            dict(email='senior@cats.gov.in', full_name='ACP Sharma', role=User.Role.SENIOR_OFFICER,
                 password='senior123', badge_number='ACP-001', station='Central Division'),
            dict(email='operator@cats.gov.in', full_name='Operator Patil', role=User.Role.OPERATOR,
                 password='operator123', badge_number='OP-001', station='Main Station'),
            dict(email='officer1@cats.gov.in', full_name='Constable Ravi Kumar', role=User.Role.POLICE_OFFICER,
                 password='officer123', badge_number='PC-101', station='Main Station'),
            dict(email='officer2@cats.gov.in', full_name='SI Priya Desai', role=User.Role.POLICE_OFFICER,
                 password='officer123', badge_number='SI-202', station='East Division'),
        ]

        for u in users:
            password = u.pop('password')
            if not User.objects.filter(email=u['email']).exists():
                User.objects.create_user(password=password, **u)
                self.stdout.write(self.style.SUCCESS(f"Created: {u['email']}"))
            else:
                self.stdout.write(f"Already exists: {u['email']}")

        self.stdout.write(self.style.SUCCESS('\n✅ Demo users ready!'))
        self.stdout.write('Credentials:\n'
                          '  admin@cats.gov.in / admin123\n'
                          '  senior@cats.gov.in / senior123\n'
                          '  operator@cats.gov.in / operator123\n'
                          '  officer1@cats.gov.in / officer123\n'
                          '  officer2@cats.gov.in / officer123\n')