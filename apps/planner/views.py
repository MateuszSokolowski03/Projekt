from django.shortcuts import render, redirect
from django.http import HttpResponse
from .models import Team, Player, League, Round, Match, PlayerStatistics, TeamRanking, MatchEvent
from .forms import TeamForm, PlayerForm, LeagueForm, RoundForm, MatchForm, MatchEventForm
from django.contrib.auth import login, authenticate
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth.forms import UserCreationForm
from django.contrib import messages

def index(request):
    return render(request, 'base.html')

def team_list(request):
    sort_by = request.GET.get('sort', 'name')
    direction = request.GET.get('direction', 'asc')
    if direction == 'desc':
        sort_by = f'-{sort_by}'
    teams = Team.objects.all().order_by(sort_by)
    return render(request, 'team_list.html', {'teams': teams, 'sort_by': sort_by.lstrip('-'), 'direction': direction})

def team_detail(request, team_id):
    team = Team.objects.get(pk=team_id)
    players = team.players.all()  # Pobranie składu drużyny
    return render(request, 'team_detail.html', {'team': team, 'players': players})

def player_list(request):
    sort_by = request.GET.get('sort', 'last_name')
    direction = request.GET.get('direction', 'asc')
    if direction == 'desc':
        sort_by = f'-{sort_by}'

    # Pobierz wybrane pozycje z parametrów GET
    selected_positions = request.GET.getlist('position', [])

    # Filtrowanie wybranych pozycji
    if selected_positions:
        players = Player.objects.filter(position__in=selected_positions).order_by(sort_by)
    else:
        players = Player.objects.all().order_by(sort_by)

    # Pobierz wszystkie dostępne pozycje (unikalne wartości)
    all_positions = Player.objects.values_list('position', flat=True).distinct()

    return render(request, 'player_list.html', {
        'players': players,
        'sort_by': sort_by.lstrip('-'),
        'direction': direction,
        'all_positions': all_positions,
        'selected_positions': selected_positions
    })

def player_detail(request, player_id):
    player = Player.objects.get(pk=player_id)
    try:
        statistics = player.statistics # Pobranie statystyk piłkarza
    except PlayerStatistics.DoesNotExist:
        statistics = None
    return render(request, 'player_detail.html', {'player': player, 'statistics': statistics})
def league_list(request):
    leagues = League.objects.all()
    return render(request, 'league_list.html', {'leagues': leagues})

def round_list(request):
    rounds = Round.objects.all()
    return render(request, 'round_list.html', {'rounds': rounds})

def match_list(request):
    sort_by = request.GET.get('sort', 'match_date')
    direction = request.GET.get('direction', 'asc')
    if direction == 'desc':
        sort_by = f'-{sort_by}'
    matches = Match.objects.all().order_by(sort_by)
    return render(request, 'match_list.html', {'matches': matches, 'sort_by': sort_by.lstrip('-'), 'direction': direction})
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
            league = form.save(commit=False)
            league.save()
            form.save_m2m()  # Zapisz relacje ManyToMany (drużyny)
            return redirect('league_list')  # Zmień na odpowiednią nazwę widoku
    else:
        form = LeagueForm()
    return render(request, 'add_league.html', {'form': form})

def add_round(request):
    if request.method == 'POST':
        form = RoundForm(request.POST)
        if form.is_valid():
            round_instance = form.save(commit=False)
            round_instance.save()
            form.save_m2m()  # Zapisz relacje ManyToMany (mecze)
            return redirect('round_list')  # Zmień na odpowiednią nazwę widoku
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

    leagues = League.objects.all()  # Pobranie listy lig
    teams = Team.objects.all()  # Pobranie listy drużyn
    return render(request, 'add_match.html', {'form': form, 'leagues': leagues, 'teams': teams})

def add_event(request):
    if request.method == 'POST':
        form = MatchEventForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('event_list')
    else:
        form = MatchEventForm()

    matches = Match.objects.all()
    event_types = MatchEvent.EVENT_TYPES
    print("Matches:", matches)  # Debugowanie
    print("Event Types:", event_types)  # Debugowanie
    return render(request, 'add_event.html', {'form': form, 'matches': matches, 'event_types': event_types})

def register_view(request):
    if request.method == 'POST':
        form = UserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            messages.success(request, 'Konto zostało pomyślnie utworzone!')
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
