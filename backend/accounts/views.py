# from rest_framework import generics, permissions, status
# from rest_framework.response import Response
# from rest_framework.views import APIView
# from rest_framework_simplejwt.views import TokenObtainPairView
# from .models import User
# from .serializers import (
#     RegisterSerializer, UserSerializer, StaffCreateSerializer,
#     CustomTokenObtainPairSerializer, OfficerListSerializer
# )


# class CustomTokenObtainPairView(TokenObtainPairView):
#     serializer_class = CustomTokenObtainPairSerializer


# class RegisterView(generics.CreateAPIView):
#     queryset = User.objects.all()
#     serializer_class = RegisterSerializer
#     permission_classes = [permissions.AllowAny]


# class MeView(APIView):
#     def get(self, request):
#         serializer = UserSerializer(request.user)
#         return Response(serializer.data)

#     def patch(self, request):
#         serializer = UserSerializer(request.user, data=request.data, partial=True)
#         if serializer.is_valid():
#             serializer.save()
#             return Response(serializer.data)
#         return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


# class StaffCreateView(generics.CreateAPIView):
#     """Only super admin can create staff accounts."""
#     serializer_class = StaffCreateSerializer
#     permission_classes = [permissions.IsAuthenticated]

#     def perform_create(self, serializer):
#         if self.request.user.role not in [User.Role.SUPER_ADMIN]:
#             from rest_framework.exceptions import PermissionDenied
#             raise PermissionDenied("Only admins can create staff accounts.")
#         serializer.save()


# class OfficerListView(generics.ListAPIView):
#     """List all police officers (for assignment)."""
#     serializer_class = OfficerListSerializer
#     permission_classes = [permissions.IsAuthenticated]

#     def get_queryset(self):
#         return User.objects.filter(role=User.Role.POLICE_OFFICER, is_active=True)


# class SeniorOfficerListView(generics.ListAPIView):
#     """List senior officers (for escalation)."""
#     serializer_class = OfficerListSerializer
#     permission_classes = [permissions.IsAuthenticated]

#     def get_queryset(self):
#         return User.objects.filter(role=User.Role.SENIOR_OFFICER, is_active=True)


# class AllStaffListView(generics.ListAPIView):
#     """List all staff."""
#     serializer_class = UserSerializer
#     permission_classes = [permissions.IsAuthenticated]

#     def get_queryset(self):
#         user = self.request.user
#         if user.role in [User.Role.SUPER_ADMIN, User.Role.SENIOR_OFFICER]:
#             return User.objects.filter(is_police_staff=True) if False else User.objects.exclude(role=User.Role.CITIZEN)
#         return User.objects.none()





from rest_framework import generics, permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.views import TokenObtainPairView
from .models import User
from .serializers import (
    RegisterSerializer, UserSerializer, StaffCreateSerializer,
    CustomTokenObtainPairSerializer, OfficerListSerializer
)


class CustomTokenObtainPairView(TokenObtainPairView):
    serializer_class = CustomTokenObtainPairSerializer


class RegisterView(generics.CreateAPIView):
    queryset = User.objects.all()
    serializer_class = RegisterSerializer
    permission_classes = [permissions.AllowAny]


class MeView(APIView):
    def get(self, request):
        serializer = UserSerializer(request.user)
        return Response(serializer.data)

    def patch(self, request):
        serializer = UserSerializer(request.user, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class StaffCreateView(generics.CreateAPIView):
    """Only super admin can create staff accounts."""
    serializer_class = StaffCreateSerializer
    permission_classes = [permissions.IsAuthenticated]

    def perform_create(self, serializer):
        if self.request.user.role not in [User.Role.SUPER_ADMIN]:
            from rest_framework.exceptions import PermissionDenied
            raise PermissionDenied("Only admins can create staff accounts.")
        serializer.save()


class OfficerListView(generics.ListAPIView):
    """List all police officers (for assignment)."""
    serializer_class = OfficerListSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return User.objects.filter(role=User.Role.POLICE_OFFICER, is_active=True)


class SeniorOfficerListView(generics.ListAPIView):
    """List senior officers (for escalation)."""
    serializer_class = OfficerListSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return User.objects.filter(role=User.Role.SENIOR_OFFICER, is_active=True)


class AllStaffListView(generics.ListAPIView):
    """List all staff."""
    serializer_class = UserSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        if user.role in [User.Role.SUPER_ADMIN, User.Role.SENIOR_OFFICER]:
            return User.objects.filter(is_police_staff=True) if False else User.objects.exclude(role=User.Role.CITIZEN)
        return User.objects.none()


# ── NEW: Edit & Delete ──────────────────────────────────────

class StaffUpdateView(generics.UpdateAPIView):
    """Admin can edit any staff member."""
    serializer_class = StaffCreateSerializer
    permission_classes = [permissions.IsAuthenticated]
    http_method_names = ['patch']

    def get_object(self):
        if self.request.user.role not in [User.Role.SUPER_ADMIN]:
            from rest_framework.exceptions import PermissionDenied
            raise PermissionDenied("Only admins can edit staff accounts.")
        return generics.get_object_or_404(User, pk=self.kwargs['pk'])

    def partial_update(self, request, *args, **kwargs):
        instance = self.get_object()
        data = request.data.copy()
        # If password not provided, remove it so it stays unchanged
        if not data.get('password'):
            data.pop('password', None)
        serializer = StaffCreateSerializer(instance, data=data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(UserSerializer(instance).data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class StaffDeleteView(generics.DestroyAPIView):
    """Admin can delete any staff member."""
    permission_classes = [permissions.IsAuthenticated]

    def get_object(self):
        if self.request.user.role not in [User.Role.SUPER_ADMIN]:
            from rest_framework.exceptions import PermissionDenied
            raise PermissionDenied("Only admins can delete staff accounts.")
        return generics.get_object_or_404(User, pk=self.kwargs['pk'])