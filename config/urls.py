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
    path('admin/', admin.site.urls), # Admin panel URL
    path('', views.index, name='index'), # Home page URL
    path('teams/', views.team_list, name='team_list'), # List of teams URL
    path('teams/add/', views.add_team, name='add_team'), # Add new team URL
    path('teams/<int:team_id>/', views.team_detail, name='team_detail'), # Team detail URL
    path('players/', views.player_list, name='player_list'), # List of players URL
    path('players/add/', views.add_player, name='add_player'), # Add new player URL
    path('players/<int:player_id>/', views.player_detail, name='player_detail'), # Player detail URL
    path('leagues/', views.league_list, name='league_list'), # List of leagues URL
    path('leagues/add/', views.add_league, name='add_league'), # Add new league URL
    path('rounds/', views.round_list, name='round_list'), # List of rounds URL
    path('rounds/add/', views.add_round, name='add_round'), # Add new round URL
    path('matches/', views.match_list, name='match_list'), # List of matches URL
    path('match/<int:match_id>/', views.match_detail, name='match_detail'), # Match detail URL
    path('matches/add/', views.add_match, name='add_match'), # Add new match URL
    path('player-statistics/', views.player_statistics_list, name='player_statistics_list'), # List of player statistics URL
    path('team-rankings/', views.team_ranking_list, name='team_ranking_list'), # List of team rankings URL
    path('events/', views.event_list, name='event_list'), # List of match events URL
    path('events/add/', views.add_event, name='add_event'), # Add new match event URL
    path('register/', register_view, name='register'), # User registration URL
    path('login/', views.two_step_login_view, name='login'), #two step login
    path('logout/', LogoutView.as_view(next_page='login'), name='logout'), # User logout URL
    path('password-reset/', auth_views.PasswordResetView.as_view(template_name='password_reset.html'), name='password_reset'), # Password reset URL
    path('password-reset/done/', auth_views.PasswordResetDoneView.as_view(template_name='password_reset_done.html'), name='password_reset_done'), # Password reset done URL
    path('reset/<uidb64>/<token>/', auth_views.PasswordResetConfirmView.as_view(template_name='password_reset_confirm.html'), name='password_reset_confirm'), # Password reset confirm URL
    path('reset/done/', auth_views.PasswordResetCompleteView.as_view(template_name='password_reset_complete.html'), name='password_reset_complete'), # Password reset complete URL
    path('api/match_players/<int:match_id>/', views.match_players, name='match_players'), # API to get players in a match
    path('get_teams_by_league/<int:league_id>/', views.get_teams_by_league, name='get_teams_by_league'), # API to get teams by league
    path('get_matches_by_league/<int:league_id>/', views.get_matches_by_league, name='get_matches_by_league'), # API to get matches by league
    path('finish_match/<int:match_id>/', views.finish_match, name='finish_match'), # Finish match URL
    path('generate_matches/', views.generate_matches, name='generate_matches'), # Generate matches URL
    path('round/<int:round_id>/', views.round_detail, name='round_detail'), # Round detail URL

]
# Obsługa plików statycznych i multimedialnych w trybie deweloperskim
urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT) # Static files URL
urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT) # Media files URL