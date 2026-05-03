from rest_framework import serializers
from .models import Complaint, ComplaintStatusHistory, Notification
from accounts.serializers import UserSerializer


class ComplaintStatusHistorySerializer(serializers.ModelSerializer):
    changed_by_name = serializers.CharField(source='changed_by.full_name', read_only=True)
    new_officer_name = serializers.CharField(source='new_officer.full_name', read_only=True)
    old_officer_name = serializers.CharField(source='old_officer.full_name', read_only=True)

    class Meta:
        model = ComplaintStatusHistory
        fields = [
            'id', 'old_status', 'new_status', 'changed_by_name',
            'old_officer_name', 'new_officer_name', 'note', 'created_at'
        ]


class NotificationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Notification
        fields = ['id', 'message', 'channel', 'sent', 'created_at']


class ComplaintListSerializer(serializers.ModelSerializer):
    assigned_officer_name = serializers.CharField(source='assigned_officer.full_name', read_only=True)
    submitted_by_name = serializers.CharField(source='submitted_by.full_name', read_only=True)
    is_overdue = serializers.BooleanField(read_only=True)

    class Meta:
        model = Complaint
        fields = [
            'id', 'complaint_number', 'title', 'category', 'status', 'priority',
            'complainant_name', 'complainant_phone', 'incident_date',
            'assigned_officer_name', 'submitted_by_name', 'deadline',
            'created_at', 'updated_at', 'is_overdue'
        ]


class ComplaintDetailSerializer(serializers.ModelSerializer):
    history = ComplaintStatusHistorySerializer(many=True, read_only=True)
    notifications = NotificationSerializer(many=True, read_only=True)
    assigned_officer_detail = UserSerializer(source='assigned_officer', read_only=True)
    escalated_to_detail = UserSerializer(source='escalated_to', read_only=True)
    submitted_by_detail = UserSerializer(source='submitted_by', read_only=True)
    is_overdue = serializers.BooleanField(read_only=True)

    class Meta:
        model = Complaint
        fields = '__all__'


class ComplaintCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Complaint
        fields = [
            'id',                    
            'complaint_number',
            'title', 'description', 'category', 'incident_date', 'incident_location',
            'complainant_name', 'complainant_phone', 'complainant_address', 'complainant_email',
        ]
        read_only_fields = ['id', 'complaint_number']


class ComplaintAssignSerializer(serializers.Serializer):
    assigned_officer = serializers.IntegerField()
    priority = serializers.ChoiceField(choices=Complaint.Priority.choices)
    deadline = serializers.DateField()
    note = serializers.CharField(required=False, allow_blank=True)


class ComplaintStatusUpdateSerializer(serializers.Serializer):
    status = serializers.ChoiceField(choices=Complaint.Status.choices)
    note = serializers.CharField(required=False, allow_blank=True)


class ComplaintEscalateSerializer(serializers.Serializer):
    escalated_to = serializers.IntegerField()
    reason = serializers.CharField()


class ComplaintReassignSerializer(serializers.Serializer):
    assigned_officer = serializers.IntegerField()
    priority = serializers.ChoiceField(choices=Complaint.Priority.choices)
    deadline = serializers.DateField()
    note = serializers.CharField(required=False, allow_blank=True)


class ComplaintResolveSerializer(serializers.Serializer):
    resolution_notes = serializers.CharField()