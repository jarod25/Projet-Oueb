from django.urls import path
from . import views

urlpatterns = [
    path('', views.room_list_view, name='room_list'),
    path('create/', views.create_room_view, name='create_room'),
    path('<int:room_id>/delete/', views.delete_room_view, name='delete_room'),
    path('<int:room_id>/', views.room_detail_view, name='room_detail'),
    path('<int:room_id>/send_message/', views.send_message, name='send_message'),
    path('<int:room_id>/get_messages/', views.get_messages, name='get_messages'),
    path('<int:room_id>/invite/', views.invite_user_view, name='invite_user'),
    path('<int:room_id>/invite/search_users', views.search_users, name='search_users'),
    path('invitations/<int:invitation_id>/manage/', views.manage_invitation_view, name='manage_invitation'),
    path('invitations/', views.invitations_list_view, name='invitations_list'),
    path('<int:message_id>/delete-message/', views.delete_message, name="delete-message"),
    path('<int:message_id>/edit-message/', views.edit_message, name='edit_message'),
]
