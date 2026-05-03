# from django.urls import path
# from .views import (
#     ComplaintListCreateView, ComplaintDetailView, ComplaintTrackView,
#     AssignComplaintView, UpdateStatusView, EscalateComplaintView,
#     ReassignComplaintView, DashboardStatsView
# )

# urlpatterns = [
#     path('complaints/', ComplaintListCreateView.as_view(), name='complaint-list-create'),
#     path('complaints/<int:pk>/', ComplaintDetailView.as_view(), name='complaint-detail'),
#     path('complaints/track/', ComplaintTrackView.as_view(), name='complaint-track'),
#     path('complaints/<int:pk>/assign/', AssignComplaintView.as_view(), name='complaint-assign'),
#     path('complaints/<int:pk>/status/', UpdateStatusView.as_view(), name='complaint-status-update'),
#     path('complaints/<int:pk>/escalate/', EscalateComplaintView.as_view(), name='complaint-escalate'),
#     path('complaints/<int:pk>/reassign/', ReassignComplaintView.as_view(), name='complaint-reassign'),
#     path('dashboard/stats/', DashboardStatsView.as_view(), name='dashboard-stats'),
# ]
from django.urls import path
from .views import (
    ComplaintListCreateView, ComplaintDetailView, ComplaintTrackView,
    AssignComplaintView, UpdateStatusView, EscalateComplaintView,
    ReassignComplaintView, DashboardStatsView
)

urlpatterns = [
    path('complaints/track/', ComplaintTrackView.as_view(), name='complaint-track'),
    path('complaints/', ComplaintListCreateView.as_view(), name='complaint-list-create'),
    path('complaints/<int:pk>/', ComplaintDetailView.as_view(), name='complaint-detail'),
    path('complaints/<int:pk>/assign/', AssignComplaintView.as_view(), name='complaint-assign'),
    path('complaints/<int:pk>/status/', UpdateStatusView.as_view(), name='complaint-status-update'),
    path('complaints/<int:pk>/escalate/', EscalateComplaintView.as_view(), name='complaint-escalate'),
    path('complaints/<int:pk>/reassign/', ReassignComplaintView.as_view(), name='complaint-reassign'),
    path('dashboard/stats/', DashboardStatsView.as_view(), name='dashboard-stats'),
]