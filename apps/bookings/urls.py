from django.urls import path
from . import views

app_name = 'bookings'

urlpatterns = [
    path('', views.CalendarView.as_view(), name='calendar'),
    path('list/', views.BookingListView.as_view(), name='booking_list'),
    path('create/', views.BookingCreateView.as_view(), name='booking_create'),
    path('<int:pk>/', views.BookingDetailView.as_view(), name='booking_detail'),
    path('<int:pk>/edit/', views.BookingUpdateView.as_view(), name='booking_update'),
    path('<int:pk>/cancel/', views.BookingCancelView.as_view(), name='booking_cancel'),
    path('<int:pk>/delete/', views.BookingDeleteView.as_view(), name='booking_delete'),
    path('api/events/', views.api_bookings_json, name='api_bookings'),
]
