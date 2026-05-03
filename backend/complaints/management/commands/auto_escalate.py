"""
Auto-escalation command for overdue complaints.
Run this daily via Windows Task Scheduler or a cron job:
    python manage.py auto_escalate

Schedule it to run every day at midnight.
"""
from django.core.management.base import BaseCommand
from django.utils import timezone
from complaints.models import Complaint, ComplaintStatusHistory
from accounts.models import User
from complaints import sms_service


class Command(BaseCommand):
    help = 'Auto-escalate overdue complaints to senior officers'

    def handle(self, *args, **options):
        today = timezone.now().date()

        # Find all complaints that are overdue and not yet escalated/resolved/closed
        overdue_complaints = Complaint.objects.filter(
            deadline__lt=today,
            status__in=[
                Complaint.Status.ASSIGNED,
                Complaint.Status.IN_PROGRESS,
                Complaint.Status.PENDING,
            ]
        )

        if not overdue_complaints.exists():
            self.stdout.write('No overdue complaints found.')
            return

        # Get the first available senior officer
        # In production you might want to assign to a specific senior
        senior_officers = User.objects.filter(
            role=User.Role.SENIOR_OFFICER,
            is_active=True
        )

        if not senior_officers.exists():
            self.stdout.write(self.style.WARNING(
                'No senior officers found. Cannot auto-escalate.'
            ))
            return

        escalated_count = 0

        for complaint in overdue_complaints:
            # Pick senior officer - prefer one already handling escalations
            # or just pick the first available
            senior = senior_officers.first()

            old_status = complaint.status
            days_overdue = (today - complaint.deadline).days

            complaint.escalated_to = senior
            complaint.escalation_reason = (
                f"Auto-escalated: Complaint was not resolved within the deadline. "
                f"Overdue by {days_overdue} day(s). "
                f"Was assigned to: {complaint.assigned_officer.full_name if complaint.assigned_officer else 'No officer'}."
            )
            complaint.escalated_at = timezone.now()
            complaint.status = Complaint.Status.ESCALATED
            complaint.save()

            ComplaintStatusHistory.objects.create(
                complaint=complaint,
                changed_by=None,  # System action
                old_status=old_status,
                new_status=Complaint.Status.ESCALATED,
                old_officer=complaint.assigned_officer,
                new_officer=None,
                note=f"SYSTEM: Auto-escalated to {senior.full_name} after deadline passed by {days_overdue} day(s)."
            )

            sms_service.notify_escalated(complaint)

            self.stdout.write(self.style.SUCCESS(
                f"Escalated: {complaint.complaint_number} → {senior.full_name} "
                f"(overdue by {days_overdue} days)"
            ))
            escalated_count += 1

        self.stdout.write(self.style.SUCCESS(
            f'\n✅ Auto-escalation complete. {escalated_count} complaint(s) escalated.'
        ))