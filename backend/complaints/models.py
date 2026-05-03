from django.db import models
from django.conf import settings
from django.utils import timezone


class Complaint(models.Model):
    class Status(models.TextChoices):
        PENDING = 'pending', 'Pending'
        ASSIGNED = 'assigned', 'Assigned'
        IN_PROGRESS = 'in_progress', 'In Progress'
        ESCALATED = 'escalated', 'Escalated'
        RESOLVED = 'resolved', 'Resolved'
        CLOSED = 'closed', 'Closed'
        REJECTED = 'rejected', 'Rejected'

    class Priority(models.TextChoices):
        LOW = 'low', 'Low'
        MEDIUM = 'medium', 'Medium'
        HIGH = 'high', 'High'
        URGENT = 'urgent', 'Urgent'

    class Category(models.TextChoices):
        THEFT = 'theft', 'Theft'
        ASSAULT = 'assault', 'Assault'
        FRAUD = 'fraud', 'Fraud'
        HARASSMENT = 'harassment', 'Harassment'
        ACCIDENT = 'accident', 'Accident'
        MISSING_PERSON = 'missing_person', 'Missing Person'
        CYBERCRIME = 'cybercrime', 'Cybercrime'
        DOMESTIC_VIOLENCE = 'domestic_violence', 'Domestic Violence'
        OTHER = 'other', 'Other'

    # Complaint identification
    complaint_number = models.CharField(max_length=20, unique=True, editable=False)

    # Complainant info
    citizen = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True,
        related_name='complaints_filed'
    )
    # Submitted by operator on behalf of citizen
    submitted_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True,
        related_name='complaints_submitted'
    )
    # Citizen details (in case walk-in)
    complainant_name = models.CharField(max_length=150)
    complainant_phone = models.CharField(max_length=15)
    complainant_address = models.TextField()
    complainant_email = models.EmailField(blank=True)

    # Complaint details
    title = models.CharField(max_length=255)
    description = models.TextField()
    category = models.CharField(max_length=30, choices=Category.choices, default=Category.OTHER)
    incident_date = models.DateField()
    incident_location = models.TextField()

    # Assignment & tracking
    assigned_officer = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True,
        related_name='complaints_assigned'
    )
    priority = models.CharField(max_length=10, choices=Priority.choices, default=Priority.MEDIUM)
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.PENDING)
    deadline = models.DateField(null=True, blank=True)

    # Escalation
    escalated_to = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True,
        related_name='escalated_complaints'
    )
    escalation_reason = models.TextField(blank=True)
    escalated_at = models.DateTimeField(null=True, blank=True)

    # Resolution
    resolution_notes = models.TextField(blank=True)
    resolved_at = models.DateTimeField(null=True, blank=True)

    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.complaint_number} - {self.title}"

    def save(self, *args, **kwargs):
        if not self.complaint_number:
            self.complaint_number = self._generate_complaint_number()
        super().save(*args, **kwargs)

    def _generate_complaint_number(self):
        import random
        year = timezone.now().year
        rand_num = random.randint(10000, 99999)
        return f"CMP-{year}-{rand_num}"

    @property
    def is_overdue(self):
        if self.deadline and self.status not in [self.Status.RESOLVED, self.Status.CLOSED]:
            return timezone.now().date() > self.deadline
        return False


class ComplaintStatusHistory(models.Model):
    """Audit trail of every status change."""
    complaint = models.ForeignKey(Complaint, on_delete=models.CASCADE, related_name='history')
    changed_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True)
    old_status = models.CharField(max_length=20, blank=True)
    new_status = models.CharField(max_length=20)
    old_officer = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True,
        related_name='history_old_officer'
    )
    new_officer = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True,
        related_name='history_new_officer'
    )
    note = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.complaint.complaint_number} → {self.new_status}"


class Notification(models.Model):
    """SMS/system notifications sent to citizen."""
    class Channel(models.TextChoices):
        SMS = 'sms', 'SMS'
        SYSTEM = 'system', 'System'

    complaint = models.ForeignKey(Complaint, on_delete=models.CASCADE, related_name='notifications')
    recipient_phone = models.CharField(max_length=15)
    message = models.TextField()
    channel = models.CharField(max_length=10, choices=Channel.choices, default=Channel.SMS)
    sent = models.BooleanField(default=False)
    error = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Notif for {self.complaint.complaint_number} via {self.channel}"