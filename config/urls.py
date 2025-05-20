"""
URL configuration for PlanerApp project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path
from django.contrib.auth.views import LogoutView
from apps.planner import views
from apps.planner.views import register_view, login_view
from django.contrib.auth import views as auth_views
from django.conf.urls.static import static
from django.conf import settings

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', views.index, name='index'),
    path('teams/', views.team_list, name='team_list'),
    path('teams/add/', views.add_team, name='add_team'),
    path('teams/<int:team_id>/', views.team_detail, name='team_detail'),
    path('players/', views.player_list, name='player_list'),
    path('players/add/', views.add_player, name='add_player'),
    path('players/<int:player_id>/', views.player_detail, name='player_detail'),
    path('leagues/', views.league_list, name='league_list'),
    path('leagues/add/', views.add_league, name='add_league'),
    path('rounds/', views.round_list, name='round_list'),
    path('rounds/add/', views.add_round, name='add_round'),
    path('matches/', views.match_list, name='match_list'),
    path('match/<int:match_id>/', views.match_detail, name='match_detail'),
    path('matches/add/', views.add_match, name='add_match'),
    path('player-statistics/', views.player_statistics_list, name='player_statistics_list'),
    path('team-rankings/', views.team_ranking_list, name='team_ranking_list'),
    path('events/', views.event_list, name='event_list'),
    path('events/add/', views.add_event, name='add_event'),
    path('register/', register_view, name='register'),
    path('login/', login_view, name='login'),
    path('logout/', LogoutView.as_view(next_page='login'), name='logout'),
    path('password-reset/', auth_views.PasswordResetView.as_view(template_name='password_reset.html'), name='password_reset'),
    path('password-reset/done/', auth_views.PasswordResetDoneView.as_view(template_name='password_reset_done.html'), name='password_reset_done'),
    path('reset/<uidb64>/<token>/', auth_views.PasswordResetConfirmView.as_view(template_name='password_reset_confirm.html'), name='password_reset_confirm'),
    path('reset/done/', auth_views.PasswordResetCompleteView.as_view(template_name='password_reset_complete.html'), name='password_reset_complete'),
    path('api/match_players/<int:match_id>/', views.match_players, name='match_players'),
    path('get_teams_by_league/<int:league_id>/', views.get_teams_by_league, name='get_teams_by_league'),
    path('get_matches_by_league/<int:league_id>/', views.get_matches_by_league, name='get_matches_by_league'),
]

urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)