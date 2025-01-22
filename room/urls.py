from django.urls import path
from . import views

urlpatterns = [
    path('', views.room_list_view, name='room_list'),
    path('create/', views.create_room_view, name='create_room'),
    path('<int:room_id>/leave/', views.leave_room_view, name='leave_room'),
    path('<int:room_id>/delete/', views.delete_room_view, name='delete_room'),
    path('<int:room_id>/', views.room_detail_view, name='room_detail'),
    path('<int:room_id>/send_message/', views.send_message, name='send_message'),
    path('<int:room_id>/get_messages/', views.get_messages, name='get_messages'),
    path('<int:room_id>/invite_user/', views.invite_user_view, name='invite_user'),
    path('<int:room_id>/invite/search_users', views.search_users, name='search_users'),
    path('respond_to_invitation/', views.respond_to_invitation_view, name='respond_to_invitation'),
    path('invitation_popover/', views.invitation_popover_view, name='invitation_popover'),
    path('<int:room_id>/user_role_popover/', views.user_role_popover, name='user_role_popover'),
    path('<int:room_id>/update_user_role/', views.update_user_role, name='update_user_role'),
    path('<int:message_id>/delete-message/', views.delete_message, name="delete-message"),
    path('<int:message_id>/edit-message/', views.edit_message, name='edit_message'),

]
