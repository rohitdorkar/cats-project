import logging
from apscheduler.schedulers.background import BackgroundScheduler
from django.utils import timezone

logger = logging.getLogger(__name__)


def auto_escalate_overdue_complaints():
    """
    Automatically escalates overdue complaints to senior officers.
    Runs daily at 11:59 PM inside the Django process.
    """
    from complaints.models import Complaint, ComplaintStatusHistory
    from accounts.models import User
    from complaints import sms_service

    today = timezone.now().date()

    overdue_complaints = Complaint.objects.filter(
        deadline__lt=today,
        status__in=[
            Complaint.Status.ASSIGNED,
            Complaint.Status.IN_PROGRESS,
            Complaint.Status.PENDING,
        ]
    )

    if not overdue_complaints.exists():
        logger.info('Auto-escalation check: No overdue complaints found.')
        return

    senior_officers = User.objects.filter(
        role=User.Role.SENIOR_OFFICER,
        is_active=True
    )

    if not senior_officers.exists():
        logger.warning('Auto-escalation: No senior officers found.')
        return

    senior = senior_officers.first()
    escalated_count = 0

    for complaint in overdue_complaints:
        old_status = complaint.status
        days_overdue = (today - complaint.deadline).days

        complaint.escalated_to = senior
        complaint.escalation_reason = (
            f"Auto-escalated by system: Complaint was not resolved within deadline. "
            f"Overdue by {days_overdue} day(s). "
            f"Previously assigned to: "
            f"{complaint.assigned_officer.full_name if complaint.assigned_officer else 'No officer'}."
        )
        complaint.escalated_at = timezone.now()
        complaint.status = Complaint.Status.ESCALATED
        complaint.save()

        ComplaintStatusHistory.objects.create(
            complaint=complaint,
            changed_by=None,
            old_status=old_status,
            new_status=Complaint.Status.ESCALATED,
            old_officer=complaint.assigned_officer,
            new_officer=None,
            note=(
                f"SYSTEM: Auto-escalated to Senior Officer {senior.full_name} "
                f"after deadline passed by {days_overdue} day(s)."
            )
        )

        sms_service.notify_escalated(complaint)
        escalated_count += 1
        logger.info(f"Auto-escalated: {complaint.complaint_number} → {senior.full_name}")

    logger.info(f"Auto-escalation complete: {escalated_count} complaint(s) escalated.")


def start_scheduler():
    scheduler = BackgroundScheduler(timezone='Asia/Kolkata')

    scheduler.add_job(
        auto_escalate_overdue_complaints,
        trigger='cron',
        hour=23,
        minute=59,
        id='auto_escalate',
        replace_existing=True,
        misfire_grace_time=3600
    )

    scheduler.start()
    logger.info("✅ Background scheduler started — auto-escalation active at 11:59 PM daily.")
    print("✅ Background scheduler started — auto-escalation active at 11:59 PM daily.")