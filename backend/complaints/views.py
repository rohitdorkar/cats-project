from rest_framework import generics, permissions, status, filters
from rest_framework.views import APIView
from rest_framework.response import Response
from django.utils import timezone
from django.db.models import Q
from django_filters.rest_framework import DjangoFilterBackend

from accounts.models import User
from .models import Complaint, ComplaintStatusHistory, Notification
from .serializers import (
    ComplaintListSerializer, ComplaintDetailSerializer, ComplaintCreateSerializer,
    ComplaintAssignSerializer, ComplaintStatusUpdateSerializer, ComplaintEscalateSerializer,
    ComplaintReassignSerializer, ComplaintResolveSerializer, NotificationSerializer
)
from . import sms_service


def log_history(complaint, changed_by, old_status, new_status, old_officer=None, new_officer=None, note=""):
    ComplaintStatusHistory.objects.create(
        complaint=complaint,
        changed_by=changed_by,
        old_status=old_status,
        new_status=new_status,
        old_officer=old_officer,
        new_officer=new_officer,
        note=note,
    )


class IsPoliceStaff(permissions.BasePermission):
    def has_permission(self, request, view):
        return request.user.is_authenticated and request.user.is_police_staff


class IsOperatorOrAbove(permissions.BasePermission):
    def has_permission(self, request, view):
        return request.user.is_authenticated and request.user.role in [
            User.Role.OPERATOR, User.Role.SENIOR_OFFICER, User.Role.SUPER_ADMIN
        ]


class IsSeniorOrAdmin(permissions.BasePermission):
    def has_permission(self, request, view):
        return request.user.is_authenticated and request.user.role in [
            User.Role.SENIOR_OFFICER, User.Role.SUPER_ADMIN
        ]


class ComplaintListCreateView(generics.ListCreateAPIView):
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['status', 'priority', 'category', 'assigned_officer']
    search_fields = ['complaint_number', 'title', 'complainant_name', 'complainant_phone']
    ordering_fields = ['created_at', 'deadline', 'priority']

    def get_serializer_class(self):
        if self.request.method == 'POST':
            return ComplaintCreateSerializer
        return ComplaintListSerializer

    def get_permissions(self):
        if self.request.method == 'POST':
            return [IsOperatorOrAbove()]
        return [permissions.IsAuthenticated()]

    def get_queryset(self):
        user = self.request.user
        if user.role == User.Role.CITIZEN:
            return Complaint.objects.filter(citizen=user)
        elif user.role == User.Role.POLICE_OFFICER:
            return Complaint.objects.filter(assigned_officer=user)
        elif user.role == User.Role.OPERATOR:
            return Complaint.objects.all()
        else:  # senior, admin
            return Complaint.objects.all()

    def perform_create(self, serializer):
        user = self.request.user
        complaint = serializer.save(
            submitted_by=user,
            citizen=user if user.role == User.Role.CITIZEN else None,
            status=Complaint.Status.PENDING,
        )
        log_history(complaint, user, '', Complaint.Status.PENDING, note="Complaint registered")
        sms_service.notify_complaint_registered(complaint)


class ComplaintDetailView(generics.RetrieveAPIView):
    serializer_class = ComplaintDetailSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        if user.role == User.Role.CITIZEN:
            return Complaint.objects.filter(citizen=user)
        return Complaint.objects.all()


class ComplaintTrackView(APIView):
    """Public tracking by complaint number + phone number."""
    permission_classes = [permissions.AllowAny]

    def get(self, request):
        complaint_number = request.query_params.get('complaint_number')
        phone = request.query_params.get('phone')

        if not complaint_number or not phone:
            return Response(
                {'error': 'complaint_number and phone are required'},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            complaint = Complaint.objects.get(
                complaint_number=complaint_number,
                complainant_phone=phone
            )
            serializer = ComplaintDetailSerializer(complaint)
            return Response(serializer.data)
        except Complaint.DoesNotExist:
            return Response({'error': 'Complaint not found'}, status=status.HTTP_404_NOT_FOUND)


# class AssignComplaintView(APIView):
#     """Operator assigns officer, priority, deadline."""
#     permission_classes = [IsOperatorOrAbove]

#     def post(self, request, pk):
#         try:
#             complaint = Complaint.objects.get(pk=pk)
#         except Complaint.DoesNotExist:
#             return Response({'error': 'Not found'}, status=status.HTTP_404_NOT_FOUND)

#         serializer = ComplaintAssignSerializer(data=request.data)
#         if not serializer.is_valid():
#             return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

#         data = serializer.validated_data
#         try:
#             officer = User.objects.get(pk=data['assigned_officer'], role=User.Role.POLICE_OFFICER)
#         except User.DoesNotExist:
#             return Response({'error': 'Officer not found'}, status=status.HTTP_404_NOT_FOUND)

#         old_status = complaint.status
#         old_officer = complaint.assigned_officer

#         complaint.assigned_officer = officer
#         complaint.priority = data['priority']
#         complaint.deadline = data['deadline']
#         complaint.status = Complaint.Status.ASSIGNED
#         complaint.save()

#         log_history(
#             complaint, request.user, old_status, Complaint.Status.ASSIGNED,
#             old_officer=old_officer, new_officer=officer,
#             note=data.get('note', f"Assigned to {officer.full_name}")
#         )
#         sms_service.notify_complaint_assigned(complaint)

#         return Response({'message': 'Complaint assigned successfully', 'complaint_number': complaint.complaint_number})

class AssignComplaintView(APIView):
    """Operator assigns officer, priority, deadline."""
    permission_classes = [IsOperatorOrAbove]

    def post(self, request, pk):
        try:
            complaint = Complaint.objects.get(pk=pk)
        except Complaint.DoesNotExist:
            return Response({'error': 'Not found'}, status=status.HTTP_404_NOT_FOUND)

        serializer = ComplaintAssignSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        data = serializer.validated_data
        try:
            officer = User.objects.get(pk=data['assigned_officer'], role=User.Role.POLICE_OFFICER)
        except User.DoesNotExist:
            return Response({'error': 'Officer not found'}, status=status.HTTP_404_NOT_FOUND)

        old_status = complaint.status
        old_officer = complaint.assigned_officer

        complaint.assigned_officer = officer
        complaint.priority = data['priority']
        complaint.deadline = data['deadline']
        complaint.status = Complaint.Status.ASSIGNED
        complaint.save()

        log_history(
            complaint, request.user, old_status, Complaint.Status.ASSIGNED,
            old_officer=old_officer, new_officer=officer,
            note=data.get('note', '') or f"Assigned to {officer.full_name} with {data['priority']} priority. Deadline: {data['deadline']}"
        )
        sms_service.notify_complaint_assigned(complaint)

        return Response({
            'message': 'Complaint assigned successfully',
            'complaint_number': complaint.complaint_number
        })



class UpdateStatusView(APIView):
    """Officer updates complaint status."""
    permission_classes = [IsPoliceStaff]

    def post(self, request, pk):
        try:
            complaint = Complaint.objects.get(pk=pk)
        except Complaint.DoesNotExist:
            return Response({'error': 'Not found'}, status=status.HTTP_404_NOT_FOUND)

        # Officers can only update their own assigned complaints
        user = request.user
        if user.role == User.Role.POLICE_OFFICER and complaint.assigned_officer != user:
            return Response({'error': 'Not your assigned complaint'}, status=status.HTTP_403_FORBIDDEN)

        serializer = ComplaintStatusUpdateSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        old_status = complaint.status
        new_status = serializer.validated_data['status']
        note = serializer.validated_data.get('note', '')

        complaint.status = new_status
        if new_status == Complaint.Status.RESOLVED:
            complaint.resolved_at = timezone.now()
        complaint.save()

        log_history(complaint, request.user, old_status, new_status, note=note)

        if new_status == Complaint.Status.RESOLVED:
            sms_service.notify_complaint_resolved(complaint)
        else:
            sms_service.notify_status_update(complaint, note)

        return Response({'message': f'Status updated to {new_status}'})


# class EscalateComplaintView(APIView):
#     """Escalate unresolved complaint to senior officer."""
#     permission_classes = [IsOperatorOrAbove]

#     def post(self, request, pk):
#         try:
#             complaint = Complaint.objects.get(pk=pk)
#         except Complaint.DoesNotExist:
#             return Response({'error': 'Not found'}, status=status.HTTP_404_NOT_FOUND)

#         serializer = ComplaintEscalateSerializer(data=request.data)
#         if not serializer.is_valid():
#             return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

#         data = serializer.validated_data
#         try:
#             senior = User.objects.get(pk=data['escalated_to'], role=User.Role.SENIOR_OFFICER)
#         except User.DoesNotExist:
#             return Response({'error': 'Senior officer not found'}, status=status.HTTP_404_NOT_FOUND)

#         old_status = complaint.status
#         complaint.escalated_to = senior
#         complaint.escalation_reason = data['reason']
#         complaint.escalated_at = timezone.now()
#         complaint.status = Complaint.Status.ESCALATED
#         complaint.save()

#         log_history(
#             complaint, request.user, old_status, Complaint.Status.ESCALATED,
#             note=f"Escalated to {senior.full_name}. Reason: {data['reason']}"
#         )
#         sms_service.notify_escalated(complaint)

#         return Response({'message': 'Complaint escalated successfully'})

class EscalateComplaintView(APIView):
    """Manually escalate complaint to senior officer."""
    permission_classes = [IsOperatorOrAbove]

    def post(self, request, pk):
        try:
            complaint = Complaint.objects.get(pk=pk)
        except Complaint.DoesNotExist:
            return Response({'error': 'Not found'}, status=status.HTTP_404_NOT_FOUND)

        if complaint.status in [Complaint.Status.RESOLVED, Complaint.Status.CLOSED]:
            return Response(
                {'error': 'Cannot escalate a resolved or closed complaint'},
                status=status.HTTP_400_BAD_REQUEST
            )

        serializer = ComplaintEscalateSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        data = serializer.validated_data
        try:
            senior = User.objects.get(pk=data['escalated_to'], role=User.Role.SENIOR_OFFICER)
        except User.DoesNotExist:
            return Response({'error': 'Senior officer not found'}, status=status.HTTP_404_NOT_FOUND)

        old_status = complaint.status
        complaint.escalated_to = senior
        complaint.escalation_reason = data['reason']
        complaint.escalated_at = timezone.now()
        complaint.status = Complaint.Status.ESCALATED
        complaint.save()

        log_history(
            complaint, request.user, old_status, Complaint.Status.ESCALATED,
            note=f"Manually escalated to Senior Officer {senior.full_name}. Reason: {data['reason']}"
        )
        sms_service.notify_escalated(complaint)

        return Response({'message': 'Complaint escalated successfully'})

class ReassignComplaintView(APIView):
    """Senior officer reassigns after escalation."""
    permission_classes = [IsSeniorOrAdmin]

    def post(self, request, pk):
        try:
            complaint = Complaint.objects.get(pk=pk)
        except Complaint.DoesNotExist:
            return Response({'error': 'Not found'}, status=status.HTTP_404_NOT_FOUND)

        serializer = ComplaintReassignSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        data = serializer.validated_data
        try:
            officer = User.objects.get(pk=data['assigned_officer'], role=User.Role.POLICE_OFFICER)
        except User.DoesNotExist:
            return Response({'error': 'Officer not found'}, status=status.HTTP_404_NOT_FOUND)

        old_status = complaint.status
        old_officer = complaint.assigned_officer

        complaint.assigned_officer = officer
        complaint.priority = data['priority']
        complaint.deadline = data['deadline']
        complaint.status = Complaint.Status.ASSIGNED
        complaint.save()

        log_history(
            complaint, request.user, old_status, Complaint.Status.ASSIGNED,
            old_officer=old_officer, new_officer=officer,
            note=data.get('note', f"Reassigned by Senior Officer to {officer.full_name}")
        )
        sms_service.notify_complaint_assigned(complaint)

        return Response({'message': 'Complaint reassigned successfully'})


class DashboardStatsView(APIView):
    """Dashboard statistics for admin/senior officer."""
    permission_classes = [IsPoliceStaff]

    def get(self, request):
        user = request.user

        if user.role == User.Role.POLICE_OFFICER:
            base_qs = Complaint.objects.filter(assigned_officer=user)
        else:
            base_qs = Complaint.objects.all()

        today = timezone.now().date()
        stats = {
            'total': base_qs.count(),
            'pending': base_qs.filter(status=Complaint.Status.PENDING).count(),
            'assigned': base_qs.filter(status=Complaint.Status.ASSIGNED).count(),
            'in_progress': base_qs.filter(status=Complaint.Status.IN_PROGRESS).count(),
            'escalated': base_qs.filter(status=Complaint.Status.ESCALATED).count(),
            'resolved': base_qs.filter(status=Complaint.Status.RESOLVED).count(),
            'overdue': base_qs.filter(
                deadline__lt=today
            ).exclude(status__in=[Complaint.Status.RESOLVED, Complaint.Status.CLOSED]).count(),
            'by_category': {},
            'by_priority': {},
        }

        for cat in Complaint.Category:
            stats['by_category'][cat.value] = base_qs.filter(category=cat).count()

        for pri in Complaint.Priority:
            stats['by_priority'][pri.value] = base_qs.filter(priority=pri).count()

        return Response(stats)