from django.contrib import admin
from .models import Complaint, ComplaintStatusHistory, Notification


@admin.register(Complaint)
class ComplaintAdmin(admin.ModelAdmin):
    list_display = ['complaint_number', 'title', 'status', 'priority', 'category', 'assigned_officer', 'deadline', 'created_at']
    list_filter = ['status', 'priority', 'category']
    search_fields = ['complaint_number', 'title', 'complainant_name', 'complainant_phone']
    readonly_fields = ['complaint_number', 'created_at', 'updated_at']


@admin.register(ComplaintStatusHistory)
class HistoryAdmin(admin.ModelAdmin):
    list_display = ['complaint', 'old_status', 'new_status', 'changed_by', 'created_at']
    readonly_fields = ['created_at']


@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    list_display = ['complaint', 'recipient_phone', 'channel', 'sent', 'created_at']
    list_filter = ['sent', 'channel']