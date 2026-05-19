from django.urls import path
from . import views

app_name = 'users'

urlpatterns = [
    path('login/',                views.login_view,         name='login'),
    path('logout/',               views.logout_view,        name='logout'),
    path('register/',             views.register_view,      name='register'),
    path('',                      views.user_list_view,     name='user-list'),
    path('<int:pk>/',             views.user_detail_view,   name='user-detail'),
    path('<int:pk>/edit/',        views.user_edit_view,     name='user-update'),
    path('<int:pk>/deactivate/',  views.user_deactivate_view, name='user-deactivate'),
    path('<int:pk>/delete/',      views.user_delete_view,   name='user-delete'),
    path('profile/',              views.profile_view,       name='profile'),
]