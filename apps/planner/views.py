from django.shortcuts import render, redirect
from django.http import HttpResponse
from .models import Team, Player, League, Round, Match, PlayerStatistics, TeamRanking, MatchEvent
from .forms import TeamForm, PlayerForm, LeagueForm, RoundForm, MatchForm, MatchEventForm
from django.contrib.auth import login, authenticate
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth.forms import UserCreationForm

def index(request):
    return render(request, 'base.html')

def team_list(request):
    teams = Team.objects.all()
    return render(request, 'team_list.html', {'teams': teams})

def player_list(request):
    players = Player.objects.all()
    return render(request, 'player_list.html', {'players': players})

def league_list(request):
    leagues = League.objects.all()
    return render(request, 'league_list.html', {'leagues': leagues})

def round_list(request):
    rounds = Round.objects.all()
    return render(request, 'round_list.html', {'rounds': rounds})

def match_list(request):
    matches = Match.objects.all()
    return render(request, 'match_list.html', {'matches': matches})

def player_statistics_list(request):
    statistics = PlayerStatistics.objects.all()
    return render(request, 'player_statistics_list.html', {'statistics': statistics})

def team_ranking_list(request):
    rankings = TeamRanking.objects.all()
    return render(request, 'team_ranking_list.html', {'rankings': rankings})

def event_list(request):
    events = MatchEvent.objects.all()
    return render(request, 'event_list.html', {'events': events})

def add_team(request):
    if request.method == 'POST':
        form = TeamForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('team_list')
    else:
        form = TeamForm()
    return render(request, 'add_team.html', {'form': form})

def add_player(request):
    if request.method == 'POST':
        form = PlayerForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('player_list')
    else:
        form = PlayerForm()
    return render(request, 'add_player.html', {'form': form})

def add_league(request):
    if request.method == 'POST':
        form = LeagueForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('league_list')
    else:
        form = LeagueForm()
    return render(request, 'add_league.html', {'form': form})

def add_round(request):
    if request.method == 'POST':
        form = RoundForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('round_list')
    else:
        form = RoundForm()
    return render(request, 'add_round.html', {'form': form})

def add_match(request):
    if request.method == 'POST':
        form = MatchForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('match_list')
    else:
        form = MatchForm()
    return render(request, 'add_match.html', {'form': form})

def add_event(request):
    if request.method == 'POST':
        form = MatchEventForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('event_list')
    else:
        form = MatchEventForm()
    return render(request, 'add_event.html', {'form': form})

def register_view(request):
    if request.method == 'POST':
        form = UserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            return redirect('team_list')
    else:
        form = UserCreationForm()
    return render(request, 'register.html', {'form': form})

def login_view(request):
    if request.method == 'POST':
        form = AuthenticationForm(data=request.POST)
        if form.is_valid():
            user = form.get_user()
            login(request, user)
            return redirect('team_list')
    else:
        form = AuthenticationForm()
    return render(request, 'login.html', {'form': form})

# Create your views here.
