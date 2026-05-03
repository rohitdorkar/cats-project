# from django.urls import path
# from rest_framework_simplejwt.views import TokenRefreshView
# from .views import (
#     CustomTokenObtainPairView, RegisterView, MeView,
#     StaffCreateView, OfficerListView, SeniorOfficerListView, AllStaffListView
# )

# urlpatterns = [
#     path('login/', CustomTokenObtainPairView.as_view(), name='token_obtain_pair'),
#     path('refresh/', TokenRefreshView.as_view(), name='token_refresh'),
#     path('register/', RegisterView.as_view(), name='register'),
#     path('me/', MeView.as_view(), name='me'),
#     path('staff/create/', StaffCreateView.as_view(), name='staff-create'),
#     path('officers/', OfficerListView.as_view(), name='officer-list'),
#     path('senior-officers/', SeniorOfficerListView.as_view(), name='senior-officer-list'),
#     path('staff/', AllStaffListView.as_view(), name='all-staff'),
# ]



from django.urls import path
from rest_framework_simplejwt.views import TokenRefreshView
from .views import (
    CustomTokenObtainPairView, RegisterView, MeView,
    StaffCreateView, OfficerListView, SeniorOfficerListView,
    AllStaffListView, StaffUpdateView, StaffDeleteView,   # ← added
)

urlpatterns = [
    path('login/',           CustomTokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('refresh/',         TokenRefreshView.as_view(),          name='token_refresh'),
    path('register/',        RegisterView.as_view(),              name='register'),
    path('me/',              MeView.as_view(),                    name='me'),
    path('staff/create/',    StaffCreateView.as_view(),           name='staff-create'),
    path('officers/',        OfficerListView.as_view(),           name='officer-list'),
    path('senior-officers/', SeniorOfficerListView.as_view(),     name='senior-officer-list'),
    path('staff/',           AllStaffListView.as_view(),          name='all-staff'),
    path('staff/<int:pk>/update/', StaffUpdateView.as_view(),     name='staff-update'),   # ← new
    path('staff/<int:pk>/delete/', StaffDeleteView.as_view(),     name='staff-delete'),   # ← new
]