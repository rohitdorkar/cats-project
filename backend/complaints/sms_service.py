import logging
from django.conf import settings

logger = logging.getLogger(__name__)


def send_sms(to_phone: str, message: str) -> tuple:
    """
    Send SMS via Twilio.
    Falls back to console mock if credentials not configured.
    """
    # Clean phone number - add India country code
    phone = to_phone.strip()
    if not phone.startswith('+'):
        if phone.startswith('0'):
            phone = '+91' + phone[1:]
        else:
            phone = '+91' + phone

    # If no credentials configured, use mock mode (prints to terminal)
    if not settings.TWILIO_ACCOUNT_SID or not settings.TWILIO_AUTH_TOKEN:
        logger.info(f"[SMS MOCK] To: {phone} | Message: {message}")
        print(f"\n📱 [SMS MOCK] To: {phone}\nMessage: {message}\n")
        return True, ""

    try:
        from twilio.rest import Client
        client = Client(settings.TWILIO_ACCOUNT_SID, settings.TWILIO_AUTH_TOKEN)

        msg = client.messages.create(
            body=message,
            from_=settings.TWILIO_PHONE_NUMBER,
            to=phone
        )

        logger.info(f"SMS sent successfully to {phone}, SID: {msg.sid}")
        return True, ""

    except Exception as e:
        logger.error(f"SMS failed to {phone}: {e}")
        return False, str(e)


def notify_complaint_registered(complaint):
    message = (
        f"Dear {complaint.complainant_name}, "
        f"your complaint has been registered successfully. "
        f"Complaint No: {complaint.complaint_number}. "
        f"Track status using this number. "
        f"- CATS Police System"
    )
    _save_and_send(complaint, message)


def notify_complaint_assigned(complaint):
    officer_name = (
        complaint.assigned_officer.full_name
        if complaint.assigned_officer else "an officer"
    )
    message = (
        f"Complaint {complaint.complaint_number}: "
        f"Assigned to {officer_name}. "
        f"Priority: {complaint.get_priority_display()}. "
        f"Deadline: {complaint.deadline}. "
        f"- CATS Police System"
    )
    _save_and_send(complaint, message)


def notify_status_update(complaint, note=""):
    message = (
        f"Complaint {complaint.complaint_number} status: "
        f"{complaint.get_status_display()}. "
        f"{note + '. ' if note else ''}"
        f"- CATS Police System"
    )
    _save_and_send(complaint, message)


def notify_complaint_resolved(complaint):
    message = (
        f"Dear {complaint.complainant_name}, "
        f"complaint {complaint.complaint_number} is RESOLVED. "
        f"Thank you for your patience. "
        f"- CATS Police System"
    )
    _save_and_send(complaint, message)


def notify_escalated(complaint):
    message = (
        f"Complaint {complaint.complaint_number} has been escalated "
        f"to senior authorities for faster resolution. "
        f"We regret the delay. "
        f"- CATS Police System"
    )
    _save_and_send(complaint, message)


def _save_and_send(complaint, message):
    """Save notification record to database and send SMS."""
    from complaints.models import Notification

    phone = complaint.complainant_phone.strip()

    # Save notification record first
    notif = Notification.objects.create(
        complaint=complaint,
        recipient_phone=phone,
        message=message,
        channel=Notification.Channel.SMS,
    )

    # Send SMS
    success, error = send_sms(phone, message)

    # Update record with result
    notif.sent = success
    notif.error = error
    notif.save()

    if success:
        logger.info(f"Notification saved and sent for {complaint.complaint_number}")
    else:
        logger.error(f"Notification failed for {complaint.complaint_number}: {error}")