from django.urls import path
from . import views

app_name = 'rooms'

urlpatterns = [
    path('', views.RoomListView.as_view(), name='room_list'),
    path('<int:pk>/', views.RoomDetailView.as_view(), name='room_detail'),
    path('create/', views.RoomCreateView.as_view(), name='room_create'),
    path('<int:pk>/edit/', views.RoomUpdateView.as_view(), name='room_update'),
    path('<int:pk>/delete/', views.RoomDeleteView.as_view(), name='room_delete'),

    path('equipment/', views.EquipmentListView.as_view(), name='equipment_list'),
    path('equipment/create/', views.EquipmentCreateView.as_view(), name='equipment_create'),
    path('equipment/<int:pk>/edit/', views.EquipmentUpdateView.as_view(), name='equipment_update'),
    path('equipment/<int:pk>/delete/', views.EquipmentDeleteView.as_view(), name='equipment_delete'),

    path('types/', views.RoomTypeListView.as_view(), name='roomtype_list'),
    path('types/create/', views.RoomTypeCreateView.as_view(), name='roomtype_create'),
    path('types/<int:pk>/edit/', views.RoomTypeUpdateView.as_view(), name='roomtype_update'),
    path('types/<int:pk>/delete/', views.RoomTypeDeleteView.as_view(), name='roomtype_delete'),

    path('building-settings/', views.BuildingSettingsUpdateView.as_view(), name='building_settings'),
]
