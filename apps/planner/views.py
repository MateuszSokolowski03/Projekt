from django.shortcuts import render, redirect,get_object_or_404
from django.http import HttpResponse
from .models import Team, Player, League, Round, Match, PlayerStatistics, TeamRanking, MatchEvent
from .forms import TeamForm, PlayerForm, LeagueForm, RoundForm, MatchForm, MatchEventForm,CustomUserCreationForm,TeamRankingForm
from django.contrib.auth import login, authenticate
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth.forms import UserCreationForm
from django.contrib import messages
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.db.models import Count, Sum, Q
import logging
from django.http import JsonResponse
from django.views.decorators.cache import cache_page
from django.core.paginator import Paginator
from django.contrib.auth.decorators import login_required
from datetime import date, datetime
from django.contrib.auth.models import User
from django.core.mail import send_mail
import random
from django.db import connection
import logging
from django.db import DatabaseError
from psycopg2 import Error as Psycopg2Error
from django.views.decorators.http import require_http_methods
from datetime import timedelta
from collections import defaultdict
from .forms import CustomUserCreationForm

logger = logging.getLogger(__name__)

def index(request):
    return render(request, 'base.html')

def team_list(request):
    sort_by = request.GET.get('sort', 'name')
    direction = request.GET.get('direction', 'asc')
    if direction == 'desc':
        sort_by = f'-{sort_by}'

    if request.user.is_authenticated:
        # Pokazuj tylko drużyny należące do zalogowanego użytkownika
        teams = Team.objects.filter(owner=request.user).order_by(sort_by)
    else:
        # Pokazuj tylko drużyny stworzone przez organizatorów (czyli mają właściciela)
        teams = Team.objects.filter(owner__isnull=False).order_by(sort_by)

    return render(request, 'team_list.html', {
        'teams': teams,
        'sort_by': sort_by.lstrip('-'),
        'direction': direction,
    })
def team_detail(request, team_id):
    team = Team.objects.get(pk=team_id)
    players = team.players.all()  # Pobranie składu drużyny
    return render(request, 'team_detail.html', {'team': team, 'players': players})

def player_list(request):
    sort_by = request.GET.get('sort', 'last_name')
    direction = request.GET.get('direction', 'asc')
    if direction == 'desc':
        sort_by = f'-{sort_by}'

    selected_positions = request.GET.getlist('position', [])
    selected_teams = request.GET.getlist('team', [])

    if request.user.is_authenticated:
        players = Player.objects.filter(owner=request.user)
        all_teams = Team.objects.filter(owner=request.user)
    else: 
        players = Player.objects.filter(owner__isnull=False)
        all_teams = Team.objects.filter(owner__isnull=False)  

    if selected_positions:
        players = players.filter(position__in=selected_positions)
    if selected_teams:
        players = players.filter(team__in=selected_teams)
    players = players.order_by(sort_by)

    all_positions = Player.objects.values_list('position', flat=True).distinct()

    paginator = Paginator(players, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    return render(request, 'player_list.html', {
        'players': page_obj,
        'sort_by': sort_by.lstrip('-'),
        'direction': direction,
        'all_positions': all_positions,
        'selected_positions': selected_positions,
        'all_teams': all_teams,
        'selected_teams': selected_teams,
        'page_obj': page_obj,
    })



def player_detail(request, player_id):
    player = get_object_or_404(Player, pk=player_id)
    generate_statistics_for_player(player)  # Generowanie statystyk
    statistics = PlayerStatistics.objects.filter(player=player)  # Pobranie statystyk
    return render(request, 'player_detail.html', {'player': player, 'statistics': statistics})

def league_list(request):
    if request.user.is_authenticated:
        leagues = League.objects.filter(owner=request.user)
    else:
        leagues = League.objects.filter(owner__isnull=False)
    return render(request, 'league_list.html', {'leagues': leagues})

def round_list(request):
    selected_league_ids = request.GET.getlist('league')
    if request.user.is_authenticated:
        leagues = League.objects.filter(owner=request.user)
        if selected_league_ids:
            rounds = Round.objects.filter(owner=request.user, league_id__in=selected_league_ids)
        else:
            rounds = Round.objects.filter(owner=request.user)
    else:
        leagues = League.objects.filter(owner__isnull=False)
        if selected_league_ids:
            rounds = Round.objects.filter(owner__isnull=False, league_id__in=selected_league_ids)
        else:
            rounds = Round.objects.filter(owner__isnull=False)   

    paginator = Paginator(rounds, 5)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    return render(request, 'round_list.html', {
        'rounds': page_obj,
        'leagues': leagues,
        'selected_league_ids': selected_league_ids,
    })

def match_list(request):
    sort_by = request.GET.get('sort', 'match_date')
    direction = request.GET.get('direction', 'asc')
    if direction == 'desc':
        sort_by = f'-{sort_by}'

    selected_teams = request.GET.getlist('team', [])
    match_date = request.GET.get('match_date')

    if request.user.is_authenticated:
        matches = Match.objects.filter(owner=request.user)
        all_teams = Team.objects.filter(owner=request.user)
    else:
        matches = Match.objects.filter(owner__isnull=False)
        all_teams = Team.objects.filter(owner__isnull=False)

    if selected_teams:
        matches = matches.filter(Q(team_1__in=selected_teams) | Q(team_2__in=selected_teams))
    if match_date:
        matches = matches.filter(match_date=match_date)

    matches = matches.order_by(sort_by)

    paginator = Paginator(matches, 4)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    return render(request, 'match_list.html', {
        'matches': page_obj,
        'page_obj': page_obj,
        'sort_by': sort_by.lstrip('-'),
        'direction': direction,
        'all_teams': all_teams,
        'selected_teams': selected_teams,
        'match_date': match_date,
        'today': date.today(),
        'now': datetime.now().time(),        
    })

def match_detail(request, match_id):
    match = get_object_or_404(Match, pk=match_id)
    events = MatchEvent.objects.filter(match=match)

    # Zliczanie statystyk meczu
    goals_team_1 = events.filter(event_type='goal', player__team=match.team_1).count()
    goals_team_2 = events.filter(event_type='goal', player__team=match.team_2).count()
    yellow_cards = events.filter(event_type='yellow_card').count()
    red_cards = events.filter(event_type='red_card').count()

    return render(request, 'match_detail.html', {
        'match': match,
        'events': events,
        'goals_team_1': goals_team_1,
        'goals_team_2': goals_team_2,
        'yellow_cards': yellow_cards,
        'red_cards': red_cards,
    })

def player_statistics_list(request):
    if request.user.is_authenticated:
        leagues = League.objects.filter(owner=request.user)
    else:
        leagues = League.objects.filter(owner__isnull=False)
    selected_league_id = request.GET.get('league')
    sort_by = request.GET.get('sort', 'player__last_name')
    direction = request.GET.get('direction', 'desc' if sort_by == 'goals' else 'asc')  # domyślnie gole malejąco

    if direction == 'desc':
        order_by = f'-{sort_by}'
    else:
        order_by = sort_by

    best_scorer_id = None

    if selected_league_id:
        selected_league = get_object_or_404(League, pk=selected_league_id)
        generate_statistics(selected_league)
        statistics = PlayerStatistics.objects.filter(league=selected_league).order_by(order_by)

        # --- Król strzelców ---
        stats = list(PlayerStatistics.objects.filter(league=selected_league))
        if stats:
            max_goals = max(s.goals for s in stats)
            top_scorers = [s for s in stats if s.goals == max_goals and max_goals > 0]
            if top_scorers:
                # Bez kartek
                clean_scorers = [s for s in top_scorers if s.yellow_cards == 0 and s.red_cards == 0]
                candidates = clean_scorers if clean_scorers else top_scorers

                # Ostatni gol
                if len(candidates) > 1:
                    # Pobierz ostatni czas gola dla każdego kandydata
                    last_goal_times = []
                    for s in candidates:
                        last_goal = (
                            MatchEvent.objects
                            .filter(player=s.player, event_type='goal', match__league=selected_league)
                            .order_by('-match__match_date', '-match__match_time', '-minute')
                            .first()
                        )
                        if last_goal:
                            last_goal_times.append((s, last_goal.match.match_date, last_goal.match.match_time, last_goal.minute))
                        else:
                            last_goal_times.append((s, None, None, None))
                    # Sortuj po dacie, godzinie, minucie
                    last_goal_times.sort(key=lambda x: (x[1] or '', x[2] or '', x[3] or 0), reverse=True)
                    best_scorer_id = last_goal_times[0][0].player.player_id
                else:
                    best_scorer_id = candidates[0].player.player_id
    else:
        statistics = PlayerStatistics.objects.none()
        selected_league = None

    # Krol strzelcow zawsze na gorze listy
    if best_scorer_id and statistics.exists():
        statistics = list(statistics)
        statistics.sort(key=lambda s: s.player.player_id != best_scorer_id)

    # PAGINACJA
    paginator = Paginator(statistics, 8)  # 8 statystyk na stronę
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    return render(request, 'player_statistics_list.html', {
    'leagues': leagues,
    'statistics': page_obj,  # zamienione!
    'page_obj': page_obj,
    'selected_league': selected_league,
    'sort_by': sort_by.lstrip('-'),
    'direction': direction,
    'best_scorer_id': best_scorer_id,
})

def team_ranking_list(request):
    if request.user.is_authenticated:
        leagues = League.objects.filter(owner=request.user)
    else:
        leagues = League.objects.filter(owner__isnull=False)

    selected_league_id = request.GET.get('league')

    if selected_league_id:
        selected_league = get_object_or_404(League, pk=selected_league_id)

        # Wygeneruj ranking dynamicznie
        generate_rankings(selected_league)

        # Pobierz zaktualizowane rankingi
        rankings = TeamRanking.objects.filter(league=selected_league).order_by('position')
    else:
        rankings = TeamRanking.objects.none()
        selected_league = None

    return render(request, 'team_ranking_list.html', {
        'leagues': leagues,
        'rankings': rankings,
        'selected_league': selected_league,
    })

def event_list(request):
    events = MatchEvent.objects.all()
    return render(request, 'event_list.html', {'events': events})

def add_team(request):
    if request.method == 'POST':
        form = TeamForm(request.POST, request.FILES, user=request.user)
        if form.is_valid():
            team = form.save(commit=False)
            team.owner = request.user
            team.save()
            logger.info(f'Utworzono drużynę: {team.name} przez użytkownika: {request.user.username}')
            return redirect('team_list')
        else:
            logger.warning(f'Błąd podczas tworzenia drużyny przez {request.user.username}: {form.errors}')
    else:
        form = TeamForm(user=request.user)
    return render(request, 'add_team.html', {'form': form})

def add_player(request):
    if request.method == 'POST':
        form = PlayerForm(request.POST)
        if form.is_valid():
            try:
                player = form.save(commit=False)
                player.owner = request.user
                player.save()
                logger.info(f'Utworzono piłkarza: {player.first_name} {player.last_name} w drużynie: {player.team.name} przez użytkownika: {request.user.username}')
                return redirect('player_list')
            except Exception as e:
                logger.error(f'Błąd podczas tworzenia piłkarza przez {request.user.username}: {e}')
                error_msg = str(e)
                if "więcej niż 11 zawodników" in error_msg:
                    error_msg = "Nie można dodać więcej niż 11 zawodników do jednej drużyny."
                messages.error(request, error_msg)
        else:
            logger.warning(f'Błąd podczas tworzenia piłkarza przez {request.user.username}: {form.errors}')
    else:
        form = PlayerForm()
        form.fields['team'].queryset = Team.objects.filter(owner=request.user)

    return render(request, 'add_player.html', {'form': form})

def add_league(request):
    if request.method == 'POST':
        form = LeagueForm(request.POST)
        if form.is_valid():
            league = form.save(commit=False)
            league.owner = request.user
            league.save()
            form.save_m2m()
            logger.info(f'Utworzono ligę: {league.name} przez użytkownika: {request.user.username}')
            return redirect('league_list')
        else:
            logger.warning(f'Błąd podczas tworzenia ligi przez {request.user.username}: {form.errors}')
    else:
        form = LeagueForm()
        form.fields['teams'].queryset = Team.objects.filter(owner=request.user)
    return render(request, 'add_league.html', {'form': form})

def add_round(request):
    if request.method == 'POST':
        form = RoundForm(request.POST)
        if form.is_valid():
            # Sprawdź, czy wybrano przynajmniej jeden mecz
            matches = form.cleaned_data.get('matches')
            if not matches or matches.count() == 0:
                messages.error(request, "Kolejka musi zawierać przynajmniej jeden mecz.")
                # Przekaż ponownie formularz z błędem
                return render(request, 'add_round.html', {'form': form})
            round_instance = form.save(commit=False)
            round_instance.owner = request.user
            round_instance.save()
            form.save_m2m()
            logger.info(f'Utworzono rundę: {round_instance.number} w lidze: {round_instance.league.name} przez użytkownika: {request.user.username}')
            return redirect('round_list')
        else:
            logger.warning(f'Błąd podczas tworzenia rundy przez {request.user.username}: {form.errors}')
    else:
        form = RoundForm()
        form.fields['league'].queryset = League.objects.filter(owner=request.user)
        form.fields['matches'].queryset = Match.objects.filter(owner=request.user)
    return render(request, 'add_round.html', {'form': form})
def add_match(request):
    if request.method == 'POST':
        form = MatchForm(request.POST)
        if form.is_valid():
            try:
                match = form.save(commit=False)
                match.owner = request.user
                match.save()
                logger.info(f'Utworzono mecz: {match.team_1.name} vs {match.team_2.name} w lidze: {match.league.name} przez użytkownika: {request.user.username}')
                return redirect('match_list')
            except Exception as e:
                logger.error(f'Błąd podczas tworzenia meczu przez {request.user.username}: {e}')
                error_msg = str(e)
                if "co najmniej 7 zawodników" in error_msg:
                    error_msg = "Nie można utworzyć meczu: obie drużyny muszą mieć co najmniej 7 zawodników. Uzupełnij składy przed dodaniem meczu."
                messages.error(request, error_msg)
        else:
            logger.warning(f'Błąd podczas tworzenia meczu przez {request.user.username}: {form.errors}')
    else:
        form = MatchForm()
        # Ogranicz ligi do tych, których owner to aktualny użytkownik
        form.fields['team_1'].queryset = Team.objects.filter(owner=request.user)
        form.fields['team_2'].queryset = Team.objects.filter(owner=request.user)
        form.fields['league'].queryset = League.objects.filter(owner=request.user)
    leagues = League.objects.filter(owner=request.user)
    return render(request, 'add_match.html', {'form': form, 'leagues': leagues})

def add_event(request):
    if request.method == 'POST':
        form = MatchEventForm(request.POST)
        if form.is_valid():
            event = form.save(commit=False)
            # Sprawdź, czy mecz jest przypisany do jakiejkolwiek kolejki
            if not event.match.rounds.exists():
                messages.error(request, "Nie można dodać wydarzenia do meczu, który nie jest przypisany do żadnej kolejki!")
                logger.warning(f'Próba dodania wydarzenia do meczu bez kolejki przez {request.user.username}')
                # Ponownie wyświetl formularz z komunikatem
                matches = Match.objects.filter(owner=request.user, is_finished=False)
                event_types = MatchEvent.EVENT_TYPES
                return render(request, 'add_event.html', {'form': form, 'matches': matches, 'event_types': event_types})
            event.owner = request.user
            event.save()
            logger.info(f'Utworzono wydarzenie: {event.event_type} w meczu: {event.match.team_1.name} vs {event.match.team_2.name} przez użytkownika: {request.user.username}')
            return redirect('event_list')
        else:
            logger.warning(f'Błąd podczas tworzenia wydarzenia przez {request.user.username}: {form.errors}')
    else:
        form = MatchEventForm()
        # Ogranicz dostępne mecze do tych, które należą do użytkownika
        form.fields['match'].queryset = Match.objects.filter(owner=request.user, is_finished=False)
    matches = Match.objects.filter(owner=request.user, is_finished=False)
    event_types = MatchEvent.EVENT_TYPES
    return render(request, 'add_event.html', {'form': form, 'matches': matches, 'event_types': event_types})

from .forms import CustomUserCreationForm

def register_view(request):
    if request.method == 'POST':
        form = CustomUserCreationForm(request.POST)
        if form.is_valid():
            user = form.save(commit=False)
            user.email = form.cleaned_data['email']
            user.save()
            login(request, user)
            messages.success(request, 'Konto zostało pomyślnie utworzone!')
            logger.info(f"Zarejestrowano konto dla użytkownika: {user.username} ({user.email})")
            return redirect('team_list')
        else:
            logger.warning(f"Błąd podczas rejestracji użytkownika: {form.errors}")
    else:
        form = CustomUserCreationForm()
    return render(request, 'register.html', {'form': form})

def login_view(request):
    if request.method == 'POST':
        form = AuthenticationForm(data=request.POST)
        if form.is_valid():
            user = form.get_user()
            login(request, user)
            logger.info(f"Użytkownik {user.username} zalogowany pomyślnie.")
            return redirect('team_list')
        else:
            logger.warning(f"Błąd logowania: {form.errors}")
    else:
        form = AuthenticationForm()
    return render(request, 'login.html', {'form': form})

def team_ranking_list(request):
    if request.user.is_authenticated:
        leagues = League.objects.filter(owner=request.user)
    else:
        leagues = League.objects.filter(owner__isnull=False)

    selected_league_id = request.GET.get('league')

    if selected_league_id:
        selected_league = get_object_or_404(League, pk=selected_league_id)
        generate_rankings(selected_league)
        rankings_qs = TeamRanking.objects.filter(league=selected_league).order_by('position')

        # dynamiczne dane
        matches = Match.objects.filter(league=selected_league, is_finished=True)
        enriched_rankings = []
        for ranking in rankings_qs:
            team = ranking.team
            team_matches = matches.filter(Q(team_1=team) | Q(team_2=team))
            matches_played = team_matches.count()
            wins = draws = losses = goals_for = goals_against = 0

            for match in team_matches:
                goals_team_1 = match.events.filter(player__team=match.team_1, event_type='goal').count()
                goals_team_2 = match.events.filter(player__team=match.team_2, event_type='goal').count()

                if match.team_1 == team:
                    gf, ga = goals_team_1, goals_team_2
                else:
                    gf, ga = goals_team_2, goals_team_1

                goals_for += gf
                goals_against += ga

                if gf > ga:
                    wins += 1
                elif gf == ga:
                    draws += 1
                else:
                    losses += 1

            enriched_rankings.append({
                'team': team,
                'position': ranking.position,
                'points': ranking.points,
                'matches_played': matches_played,
                'wins': wins,
                'draws': draws,
                'losses': losses,
                'goals_for': goals_for,
                'goals_against': goals_against,
            })
    else:
        enriched_rankings = []
        selected_league = None

    return render(request, 'team_ranking_list.html', {
        'leagues': leagues,
        'selected_league': selected_league,
        'rankings': enriched_rankings,  # ← teraz lista słowników z pełnymi danymi
    })



def generate_rankings(league):
    with connection.cursor() as cursor:
        cursor.execute("SELECT update_team_rankings(%s);", [league.pk])

#@receiver(post_save, sender=Match)
#def update_rankings_after_match(sender, instance, **kwargs):
#    if instance.is_finished:
#        league = instance.league
#        generate_rankings(league)

def generate_statistics(league):
    try:
        with connection.cursor() as cursor:
            cursor.execute("SELECT update_player_statistics(%s);", [league.pk])
        logger.info(f"Statystyki zawodników zaktualizowane przez funkcję SQL dla ligi {league.name}.")
    except Exception as e:
        logger.error(f"Optymalizacja statystyk nie powiodła się: {str(e)}")


def generate_statistics_for_player(player):
    try:
        leagues = League.objects.filter(teams__players=player).distinct()

        for league in leagues:
            # Liczba meczów rozegranych przez drużynę piłkarza w danej lidze (tylko zakończone mecze)
            matches_played = Match.objects.filter(
                (Q(team_1=player.team) | Q(team_2=player.team)),
                league=league,
                is_finished=True
            ).count()

            # Domyślne wartości statystyk
            goals = 0
            yellow_cards = 0
            red_cards = 0

            # Aktualizacja statystyk tylko jeśli istnieją wydarzenia w zakończonych meczach
            events = MatchEvent.objects.filter(
                player=player,
                match__league=league,
                match__is_finished=True
            )
            if events.exists():
                goals = events.filter(event_type='goal').count()
                yellow_cards = events.filter(event_type='yellow_card').count()
                red_cards = events.filter(event_type='red_card').count()

            # Tworzenie lub aktualizacja statystyk
            PlayerStatistics.objects.update_or_create(
                player=player,
                league=league,
                defaults={
                    'matches_played': matches_played,
                    'goals': goals,
                    'yellow_cards': yellow_cards,
                    'red_cards': red_cards,
                }
            )
    except Exception as e:
        print(f"Błąd podczas generowania statystyk dla piłkarza: {str(e)}")

def match_players(request, match_id):
    match = get_object_or_404(Match, pk=match_id)
    players_team_1 = Player.objects.filter(team=match.team_1)
    players_team_2 = Player.objects.filter(team=match.team_2)
    players = list(players_team_1) + list(players_team_2)
    data = {
        'players': [{'id': p.pk, 'name': str(p)} for p in players]
    }
    return JsonResponse(data)


def get_teams_by_league(request, league_id):
    league = League.objects.get(pk=league_id)
    teams = league.teams.all()
    data = {'teams': [{'id': t.pk, 'name': t.name} for t in teams]}
    return JsonResponse(data)

def get_matches_by_league(request, league_id):
    # Pokazuj tylko mecze z tej ligi, które nie są przypisane do żadnej kolejki
    matches = Match.objects.filter(league_id=league_id, rounds=None)
    data = [
        {
            'id': m.pk,
            'team_1': m.team_1.name,
            'team_2': m.team_2.name,
            'date': str(m.match_date)
        }
        for m in matches
    ]
    return JsonResponse({'matches': data})


@login_required
def finish_match(request, match_id):
    match = get_object_or_404(Match, pk=match_id)
    # Sprawdź czy mecz jest przypisany do kolejki
    if not match.rounds.exists():
        messages.error(request, "Nie można zakończyć meczu, który nie jest przypisany do żadnej kolejki!")
        return redirect('match_detail', match_id=match_id)
    # Sprawdź czy można zakończyć mecz (czy już się rozpoczął)
    match_datetime = datetime.combine(match.match_date, match.match_time)
    if datetime.now() < match_datetime:
        messages.error(request, "Nie można zakończyć meczu przed jego rozpoczęciem!")
        return redirect('match_detail', match_id=match_id)
    if request.method == "POST":
        match.is_finished = True
        match.save()
    return redirect('match_detail', match_id=match_id)

#@receiver(post_save, sender=MatchEvent)
#def update_match_score(sender, instance, **kwargs):
#    match = instance.match
#    goals_team_1 = MatchEvent.objects.filter(match=match, event_type='goal', player__team=match.team_1).count()
#    goals_team_2 = MatchEvent.objects.filter(match=match, event_type='goal', player__team=match.team_2).count()
#    match.score_team_1 = goals_team_1
#    match.score_team_2 = goals_team_2
#    match.save()

def two_step_login_view(request):
    step = request.session.get('login_step', 1)
    email = request.session.get('login_email')
    error = None

    if request.method == 'POST':
        if step == 1:
            email = request.POST.get('email')
            try:
                user = User.objects.get(email=email)
                code = ''.join([str(random.randint(0, 9)) for _ in range(6)])
                request.session['login_code'] = code
                request.session['login_email'] = email
                request.session['login_step'] = 2
                # Wyślij kod na email
                send_mail(
                    'Twój kod logowania',
                    f'Twój kod logowania: {code}',
                    'planer.zawodow@wp.pl',  
                    [email],
                    fail_silently=False,
                )
                logger.info(f"Wysłano kod logowania na email: {email}")
                step = 2
            except User.DoesNotExist:
                error = "Nie znaleziono użytkownika z tym adresem email."
                logger.warning(f"Nieudana próba logowania dwustopniowego: nie znaleziono emaila {email}")
        elif step == 2:
            code = ''.join([request.POST.get(f'code_{i}', '') for i in range(6)])
            password = request.POST.get('password')
            session_code = request.session.get('login_code')
            email = request.session.get('login_email')
            try:
                user = User.objects.get(email=email)
                if code == session_code and user.check_password(password):
                    login(request, user)
                    logger.info(f"Użytkownik {user.username} zalogowany dwustopniowo pomyślnie.")
                    # Wyczyść sesję
                    request.session.pop('login_code', None)
                    request.session.pop('login_email', None)
                    request.session.pop('login_step', None)
                    return redirect('team_list')
                else:
                    error = "Nieprawidłowy kod lub hasło."
                    logger.warning(f"Nieudana próba logowania dwustopniowego: nieprawidłowy kod lub hasło dla emaila {email}")
            except User.DoesNotExist:
                error = "Coś poszło nie tak. Spróbuj ponownie."
                logger.error(f"Błąd podczas logowania dwustopniowego: nie znaleziono emaila {email}")
    else:
        request.session['login_step'] = 1
        step = 1

    return render(request, 'two_step_login.html', {
        'step': step,
        'email': email,
        'error': error,
    })




@login_required
@require_http_methods(["GET", "POST"])
def generate_matches(request):
    leagues = League.objects.filter(owner=request.user)
    if request.method == 'POST':
        league_id = request.POST.get('league')
        match_type = request.POST.get('match_type')
        start_date = request.POST.get('start_date')
        interval_days = request.POST.get('interval_days')
        match_time = request.POST.get('match_time')

        if not (league_id and match_type and start_date and interval_days and match_time):
            messages.error(request, "Wszystkie pola są wymagane.")
            return render(request, 'generate_matches.html', {'leagues': leagues})

        try:
            league = League.objects.get(pk=league_id, owner=request.user)
            teams = list(league.teams.all())
            if len(teams) < 2:
                messages.error(request, "Liga musi mieć co najmniej 2 drużyny.")
                return render(request, 'generate_matches.html', {'leagues': leagues})

            # Przygotuj parametry daty i czasu
            match_date = datetime.strptime(start_date, "%Y-%m-%d").date()
            match_time_obj = datetime.strptime(match_time, "%H:%M").time()
            interval_days = int(interval_days)
            matches_to_create = []

            # Generuj pary drużyn
            from itertools import combinations, permutations

            if match_type == "single":
                pairs = list(combinations(teams, 2))
            else:  # double (mecz + rewanż)
                pairs = list(permutations(teams, 2))

            for idx, (team1, team2) in enumerate(pairs):
                # Sprawdź, czy taki mecz już istnieje
                if Match.objects.filter(
                    league=league, team_1=team1, team_2=team2
                ).exists():
                    continue
                matches_to_create.append(
                    Match(
                        league=league,
                        team_1=team1,
                        team_2=team2,
                        match_date=match_date + timedelta(days=interval_days * idx),
                        match_time=match_time_obj,
                        owner=request.user
                    )
                )

            Match.objects.bulk_create(matches_to_create)
            return redirect('match_list')
        except League.DoesNotExist:
            messages.error(request, "Wybrana liga nie istnieje lub nie masz do niej dostępu.")
        except Exception as e:
            logger.error(f'Błąd podczas generowania meczów przez {request.user.username}: {e}')
            error_msg = str(e)
            if "co najmniej 7 zawodników" in error_msg or "powyżej 7 zawodnik" in error_msg:
                error_msg = "Nie można utworzyć meczu: obie drużyny muszą mieć powyżej 7 zawodników. Uzupełnij składy przed generowaniem meczów."
            messages.error(request, error_msg)

    return render(request, 'generate_matches.html', {'leagues': leagues})