from django.shortcuts import render, redirect,get_object_or_404
from .models import Team, Player, League, Round, Match, PlayerStatistics, TeamRanking, MatchEvent
from .forms import TeamForm, PlayerForm, LeagueForm, RoundForm, MatchForm, MatchEventForm
from django.contrib.auth import login
from django.contrib.auth.forms import AuthenticationForm
from django.contrib import messages
from django.db.models import Q
from django.http import JsonResponse
from django.core.paginator import Paginator
from django.contrib.auth.decorators import login_required
from datetime import date, datetime
from django.contrib.auth.models import User
from django.core.mail import send_mail
import random
from django.db import connection
import logging
from django.views.decorators.http import require_http_methods
from .forms import CustomUserCreationForm
from rest_framework import generics
from .serializers import TeamSerializer, PlayerSerializer, LeagueSerializer, MatchSerializer

logger = logging.getLogger(__name__)

# Widok głównej strony aplikacji
def index(request):
    return render(request, 'base.html')

# Widok listy drużyn
def team_list(request):
    sort_by = request.GET.get('sort', 'name') # Domyślne sortowanie po nazwie drużyny
    direction = request.GET.get('direction', 'asc') # Domyślny kierunek sortowania
    if direction == 'desc':
        sort_by = f'-{sort_by}' # Jeśli kierunek malejący, dodaj '-' do sortowania

    if request.user.is_authenticated:
        # Pokazuj tylko drużyny należące do zalogowanego użytkownika
        teams_qs = Team.objects.filter(owner=request.user).order_by(sort_by)
    else:
        # Pokazuj tylko drużyny stworzone przez organizatorów (czyli mają właściciela)
        teams_qs = Team.objects.filter(owner__isnull=False).order_by(sort_by)

    paginator = Paginator(teams_qs, 15)  # 15 drużyn na stronę (możesz zmienić liczbę)
    page_number = request.GET.get('page') # Pobierz numer strony z parametrów GET
    teams = paginator.get_page(page_number) # Pobierz stronę z drużynami

    return render(request, 'team_list.html', {
        'teams': teams,
        'sort_by': sort_by.lstrip('-'),
        'direction': direction,
    })

# Widok szczegółów drużyny
def team_detail(request, team_id):
    team = Team.objects.get(pk=team_id) # Pobranie drużyny na podstawie ID
    players = team.players.all()  # Pobranie składu drużyny
    return render(request, 'team_detail.html', {'team': team, 'players': players})

# Widok listy piłkarzy
def player_list(request):
    sort_by = request.GET.get('sort', 'last_name') # Domyślne sortowanie po nazwisku
    direction = request.GET.get('direction', 'asc') # Domyślny kierunek sortowania
    if direction == 'desc':
        sort_by = f'-{sort_by}' # Jeśli kierunek malejący, dodaj '-' do sortowania

    selected_positions = request.GET.getlist('position', []) # Pobierz zaznaczone pozycje z parametrów GET
    selected_teams = request.GET.getlist('team', []) # Pobierz zaznaczone drużyny z parametrów GET

    # Pobierz piłkarzy w zależności od tego, czy użytkownik jest zalogowany
    if request.user.is_authenticated:
        players = Player.objects.filter(owner=request.user)
        all_teams = Team.objects.filter(owner=request.user)
    else: 
        players = Player.objects.filter(owner__isnull=False)
        all_teams = Team.objects.filter(owner__isnull=False)  

    # Filtrowanie po zaznaczonych pozycjach i drużynach
    if selected_positions:
        players = players.filter(position__in=selected_positions)
    if selected_teams:
        players = players.filter(team__in=selected_teams)
    players = players.order_by(sort_by)

    # Pobierz wszystkie unikalne pozycje piłkarzy
    all_positions = Player.objects.values_list('position', flat=True).distinct()

    paginator = Paginator(players, 10) # 10 piłkarzy na stronę
    page_number = request.GET.get('page') # Pobierz numer strony z parametrów GET
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

# Widok szczegółów piłkarza
def player_detail(request, player_id):
    player = get_object_or_404(Player, pk=player_id) # Pobranie piłkarza na podstawie ID
    generate_statistics_for_player(player)  # Generowanie statystyk
    statistics = PlayerStatistics.objects.filter(player=player)  # Pobranie statystyk
    return render(request, 'player_detail.html', {'player': player, 'statistics': statistics})

# Widok listy lig
def league_list(request):
    if request.user.is_authenticated:
        leagues_qs = League.objects.filter(owner=request.user) # Pobierz tylko ligi należące do zalogowanego użytkownika
    else:
        leagues_qs = League.objects.filter(owner__isnull=False)
    paginator = Paginator(leagues_qs, 24)  # 24 ligi na stronę
    page_number = request.GET.get('page') # Pobierz numer strony z parametrów GET
    leagues = paginator.get_page(page_number)
    return render(request, 'league_list.html', {'leagues': leagues})

# Widok listy kolejek
def round_list(request):
    selected_league_ids = request.GET.getlist('league') # Pobierz zaznaczone ligi z parametrów GET

    # Pobierz tylko niepuste ligi
    if request.user.is_authenticated:
        leagues = League.objects.filter(owner=request.user)
        rounds = Round.objects.filter(owner=request.user)
    else:
        leagues = League.objects.filter(owner__isnull=False)
        rounds = Round.objects.filter(owner__isnull=False)

    # Filtrowanie po wybranych ligach
    if selected_league_ids:
        rounds = rounds.filter(league_id__in=selected_league_ids)

    # Paginacja
    paginator = Paginator(rounds.select_related('league').prefetch_related('matches'), 5) # 5 rund na stronę
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    return render(request, 'round_list.html', {
        'rounds': page_obj,
        'leagues': leagues,
        'selected_league_ids': selected_league_ids,
    })

# Widok listy meczów
def match_list(request):
    sort_by = request.GET.get('sort', 'match_date') # Domyślne sortowanie po dacie meczu
    direction = request.GET.get('direction', 'asc') # Domyślny kierunek sortowania
    if direction == 'desc':
        sort_by = f'-{sort_by}' # Jeśli kierunek malejący, dodaj '-' do sortowania

    selected_teams = request.GET.getlist('team', []) # Pobierz zaznaczone drużyny z parametrów GET
    match_date = request.GET.get('match_date') # Pobierz datę meczu z parametrów GET

    # Pobierz mecze w zależności od tego, czy użytkownik jest zalogowany
    if request.user.is_authenticated:
        matches = Match.objects.filter(owner=request.user)
        all_teams = Team.objects.filter(owner=request.user)
    else:
        matches = Match.objects.filter(owner__isnull=False)
        all_teams = Team.objects.filter(owner__isnull=False)

    # Filtrowanie po zaznaczonych drużynach i dacie meczu
    if selected_teams:
        matches = matches.filter(Q(team_1__in=selected_teams) | Q(team_2__in=selected_teams))
    if match_date:
        matches = matches.filter(match_date=match_date)

    # Optymalizacja: pobierz powiązane drużyny i ligę jednym zapytaniem
    matches = matches.select_related('team_1', 'team_2', 'league').order_by(sort_by)

    paginator = Paginator(matches, 4) # 4 mecze na stronę
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

# Widok szczegółów meczu
def match_detail(request, match_id):
    match = get_object_or_404(Match, pk=match_id) # Pobranie meczu na podstawie ID
    events = MatchEvent.objects.filter(match=match) # Pobranie wydarzeń związanych z meczem

    # Zliczanie statystyk meczu
    goals_team_1 = events.filter(event_type='goal', player__team=match.team_1).count() # Zliczanie goli drużyny 1
    goals_team_2 = events.filter(event_type='goal', player__team=match.team_2).count() # Zliczanie goli drużyny 2
    yellow_cards = events.filter(event_type='yellow_card').count() # Zliczanie żółtych kartek
    red_cards = events.filter(event_type='red_card').count() # Zliczanie czerwonych kartek

    return render(request, 'match_detail.html', {
        'match': match,
        'events': events,
        'goals_team_1': goals_team_1,
        'goals_team_2': goals_team_2,
        'yellow_cards': yellow_cards,
        'red_cards': red_cards,
    })

# Widok listy statystyk piłkarzy
def player_statistics_list(request):
    if request.user.is_authenticated:
        leagues = League.objects.filter(owner=request.user) # Pobierz tylko ligi należące do zalogowanego użytkownika
    else:
        leagues = League.objects.filter(owner__isnull=False)
    selected_league_id = request.GET.get('league') # Pobierz ID wybranej ligi z parametrów GET
    sort_by = request.GET.get('sort', 'goals')  # Domyślne sortowanie po liczbie goli
    direction = request.GET.get('direction', 'desc') # Domyślny kierunek sortowania

    if direction == 'desc':
        order_by = f'-{sort_by}' # Jeśli kierunek malejący, dodaj '-' do sortowania
    else:
        order_by = sort_by

    best_scorer_id = None # Inicjalizacja zmiennej dla najlepszego strzelca

    # Sprawdź, czy wybrano ligę
    if selected_league_id:
        selected_league = get_object_or_404(League, pk=selected_league_id) # Pobierz wybraną ligę lub zwróć 404, jeśli nie istnieje
        generate_statistics(selected_league) # Generowanie statystyk dla wybranej ligi
        statistics = PlayerStatistics.objects.filter(league=selected_league).order_by(order_by) # Pobierz statystyki piłkarzy dla wybranej ligi i posortuj je

        # --- Król strzelców ---
        stats = list(PlayerStatistics.objects.filter(league=selected_league)) # Pobierz wszystkie statystyki piłkarzy dla wybranej ligi
        if stats: # Sprawdź, czy są jakieś statystyki
            max_goals = max(s.goals for s in stats) # Znajdź maksymalną liczbę goli
            top_scorers = [s for s in stats if s.goals == max_goals and max_goals > 0] # Filtruj piłkarzy, którzy mają maksymalną liczbę goli
            if top_scorers:
                clean_scorers = [s for s in top_scorers if s.yellow_cards == 0 and s.red_cards == 0] # Filtruj piłkarzy, którzy nie mają żadnych kartek
                candidates = clean_scorers if clean_scorers else top_scorers # Jeśli są piłkarze bez kartek, użyj ich jako kandydatów, w przeciwnym razie użyj wszystkich najlepszych strzelców

                # Ostatni gol
                if len(candidates) > 1:
                    # Pobierz ostatni czas gola dla każdego kandydata
                    last_goal_times = []
                    for s in candidates: # Pobierz statystyki dla każdego kandydata
                        last_goal = ( # Pobierz ostatnie wydarzenie gola dla danego piłkarza
                            MatchEvent.objects
                            .filter(player=s.player, event_type='goal', match__league=selected_league)
                            .order_by('-match__match_date', '-match__match_time', '-minute')
                            .first()
                        )
                        if last_goal: # Jeśli istnieje ostatni gol, dodaj jego czas do listy
                            last_goal_times.append((s, last_goal.match.match_date, last_goal.match.match_time, last_goal.minute))
                        else:
                            last_goal_times.append((s, None, None, None))
                    # Sortuj po dacie, godzinie, minucie
                    last_goal_times.sort(key=lambda x: (x[1] or '', x[2] or '', x[3] or 0), reverse=True)
                    best_scorer_id = last_goal_times[0][0].player.player_id
                else:
                    best_scorer_id = candidates[0].player.player_id
    else:
        statistics = PlayerStatistics.objects.none() # Jeśli nie wybrano ligi, ustaw statystyki na puste
        selected_league = None
        
    if (
        best_scorer_id
        and statistics.exists()
        and (not request.GET.get('sort') or request.GET.get('sort') == 'goals') # Sortowanie po liczbie goli
        and (not request.GET.get('direction') or request.GET.get('direction') == 'desc') # Kierunek sortowania malejący
    ):
        statistics = list(statistics)
        statistics.sort(key=lambda s: s.player.player_id != best_scorer_id) # Przenieś najlepszego strzelca na początek listy

    # PAGINACJA
    paginator = Paginator(statistics, 8) # 8 statystyk na stronę
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    return render(request, 'player_statistics_list.html', {
        'leagues': leagues,
        'statistics': page_obj,
        'page_obj': page_obj,
        'selected_league': selected_league,
        'sort_by': sort_by.lstrip('-'),
        'direction': direction,
        'best_scorer_id': best_scorer_id,
    })

# Widok listy rankingów drużyn
def team_ranking_list(request):
    if request.user.is_authenticated: # Sprawdź, czy użytkownik jest zalogowany
        leagues = League.objects.filter(owner=request.user)
    else:
        leagues = League.objects.filter(owner__isnull=False)

    selected_league_id = request.GET.get('league') # Pobierz ID wybranej ligi z parametrów GET

    # Sprawdź, czy wybrano ligę
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

# Widok listy wydarzeń meczowych
def event_list(request):
    events_qs = ( # Pobierz wszystkie wydarzenia meczowe
        MatchEvent.objects
        .select_related(
            'match',
            'match__team_1',
            'match__team_2',
            'player',
            'player__team'
        )
        .order_by('-match__match_date', '-match__match_time', '-minute')
    )
    paginator = Paginator(events_qs, 12)  # 12 wydarzeń na stronę
    page_number = request.GET.get('page')
    events = paginator.get_page(page_number)
    return render(request, 'event_list.html', {'events': events})
    
# Widok dodawania drużyny
def add_team(request):
    if request.method == 'POST':
        form = TeamForm(request.POST, request.FILES, user=request.user) # Przekaż użytkownika do formularza
        if form.is_valid():
            team = form.save(commit=False) # Utwórz instancję drużyny, ale nie zapisuj jeszcze do bazy danych
            team.owner = request.user # Ustaw właściciela drużyny na zalogowanego użytkownika
            team.logo = request.FILES.get('logo') # Pobierz logo z przesłanych plików
            team.save() # Zapisz drużynę do bazy danych
            logger.info(f'Utworzono drużynę: {team.name} przez użytkownika: {request.user.username}')
            return redirect('team_list')
        else:
            logger.warning(f'Błąd podczas tworzenia drużyny przez {request.user.username}: {form.errors}')
    else:
        form = TeamForm(user=request.user)
    return render(request, 'add_team.html', {'form': form})

# Widok dodawania piłkarza
def add_player(request):
    if request.method == 'POST':
        form = PlayerForm(request.POST, request.FILES) # Przekaż dane z formularza
        if form.is_valid():
            try:
                player = form.save(commit=False) # Utwórz instancję piłkarza, ale nie zapisuj jeszcze do bazy danych
                player.owner = request.user # Ustaw właściciela piłkarza na zalogowanego użytkownika
                player.save() # Zapisz piłkarza do bazy danych
                logger.info(f'Utworzono piłkarza: {player.first_name} {player.last_name} w drużynie: {player.team.name} przez użytkownika: {request.user.username}')
                return redirect('player_list')
            except Exception as e:
                logger.error(f'Błąd podczas tworzenia piłkarza przez {request.user.username}: {e}')
                error_msg = str(e)
                if "więcej niż 11 zawodników" in error_msg: # Sprawdź, czy błąd dotyczy przekroczenia limitu zawodników
                    error_msg = "Nie można dodać więcej niż 11 zawodników do jednej drużyny."
                messages.error(request, error_msg)
        else:
            logger.warning(f'Błąd podczas tworzenia piłkarza przez {request.user.username}: {form.errors}')
    else:
        form = PlayerForm()
        form.fields['team'].queryset = Team.objects.filter(owner=request.user)

    return render(request, 'add_player.html', {'form': form})

# Widok dodawania ligi
def add_league(request):
    if request.method == 'POST':
        form = LeagueForm(request.POST) # Przekaż dane z formularza
        if form.is_valid():
            league = form.save(commit=False) # Utwórz instancję ligi, ale nie zapisuj jeszcze do bazy danych
            league.owner = request.user # Ustaw właściciela ligi na zalogowanego użytkownika
            league.save() # Zapisz ligę do bazy danych
            form.save_m2m() # Zapisz relację wiele-do-wielu z drużynami
            logger.info(f'Utworzono ligę: {league.name} przez użytkownika: {request.user.username}')
            return redirect('league_list')
        else:
            logger.warning(f'Błąd podczas tworzenia ligi przez {request.user.username}: {form.errors}')
    else:
        form = LeagueForm()
        form.fields['teams'].queryset = Team.objects.filter(owner=request.user)
    return render(request, 'add_league.html', {'form': form})

# Widok dodawania rundy
def add_round(request):
    if request.method == 'POST':
        form = RoundForm(request.POST) # Przekaż dane z formularza
        if form.is_valid():
            # Sprawdź, czy wybrano przynajmniej jeden mecz
            matches = form.cleaned_data.get('matches')
            if not matches or matches.count() == 0:
                messages.error(request, "Kolejka musi zawierać przynajmniej jeden mecz.")
                # Przekaż ponownie formularz z błędem
                return render(request, 'add_round.html', {'form': form})
            round_instance = form.save(commit=False) # Utwórz instancję rundy, ale nie zapisuj jeszcze do bazy danych
            round_instance.owner = request.user # Ustaw właściciela rundy na zalogowanego użytkownika
            round_instance.save() # Zapisz rundę do bazy danych
            form.save_m2m() # Zapisz relację wiele-do-wielu z meczami
            logger.info(f'Utworzono rundę: {round_instance.number} w lidze: {round_instance.league.name} przez użytkownika: {request.user.username}')
            return redirect('round_list')
        else:
            logger.warning(f'Błąd podczas tworzenia rundy przez {request.user.username}: {form.errors}')
    else:
        form = RoundForm() # Utwórz nowy formularz
        form.fields['league'].queryset = League.objects.filter(owner=request.user) # Ogranicz ligi do tych, których owner to aktualny użytkownik
        form.fields['matches'].queryset = Match.objects.filter(owner=request.user) # Ogranicz mecze do tych, których owner to aktualny użytkownik
    return render(request, 'add_round.html', {'form': form})

# Widok szczegółów rundy
def round_detail(request, round_id):
    round_obj = get_object_or_404(Round, pk=round_id) # Pobranie rundy na podstawie ID
    matches = round_obj.matches.all() # Pobranie meczów przypisanych do tej rundy
    return render(request, 'round_detail.html', {
        'round': round_obj,
        'matches': matches,
    })

# Widok dodawania meczu
def add_match(request):
    if request.method == 'POST':
        form = MatchForm(request.POST) # Przekaż dane z formularza
        if form.is_valid():
            try:
                match = form.save(commit=False) # Utwórz instancję meczu, ale nie zapisuj jeszcze do bazy danych
                match.owner = request.user # Ustaw właściciela meczu na zalogowanego użytkownika
                match.save() # Zapisz mecz do bazy danych
                logger.info(f'Utworzono mecz: {match.team_1.name} vs {match.team_2.name} w lidze: {match.league.name} przez użytkownika: {request.user.username}')
                return redirect('match_list')
            except Exception as e:
                logger.error(f'Błąd podczas tworzenia meczu przez {request.user.username}: {e}')
                error_msg = str(e)
                if "co najmniej 7 zawodników" in error_msg: # Sprawdź, czy błąd dotyczy braku wystarczającej liczby zawodników
                    error_msg = "Nie można utworzyć meczu: obie drużyny muszą mieć co najmniej 7 zawodników. Uzupełnij składy przed dodaniem meczu."
                messages.error(request, error_msg)
        else:
            logger.warning(f'Błąd podczas tworzenia meczu przez {request.user.username}: {form.errors}')
    else:
        form = MatchForm() # Utwórz nowy formularz
        form.fields['team_1'].queryset = Team.objects.filter(owner=request.user) # Ogranicz drużyny do tych, których owner to aktualny użytkownik
        form.fields['team_2'].queryset = Team.objects.filter(owner=request.user) # Ogranicz ligi do tych, których owner to aktualny użytkownik
        form.fields['league'].queryset = League.objects.filter(owner=request.user) # Ogranicz ligi do tych, których owner to aktualny użytkownik
    leagues = League.objects.filter(owner=request.user) # Pobierz wszystkie ligi należące do zalogowanego użytkownika
    return render(request, 'add_match.html', {'form': form, 'leagues': leagues})

# Widok dodawania wydarzenia do meczu
def add_event(request):
    match_id = request.GET.get('match_id') # Pobierz ID meczu z parametrów GET
    if request.method == 'POST':
        form = MatchEventForm(request.POST) # Przekaż dane z formularza
        if form.is_valid():
            event = form.save(commit=False) # Utwórz instancję wydarzenia, ale nie zapisuj jeszcze do bazy danych
            # Sprawdź, czy mecz jest przypisany do jakiejkolwiek kolejki
            if not event.match.rounds.exists():
                messages.error(request, "Nie można dodać wydarzenia do meczu, który nie jest przypisany do żadnej kolejki!")
                logger.warning(f'Próba dodania wydarzenia do meczu bez kolejki przez {request.user.username}')
                # Ponownie wyświetl formularz z komunikatem
                matches = Match.objects.filter(owner=request.user, is_finished=False) # Ogranicz dostępne mecze do tych, które należą do użytkownika
                event_types = MatchEvent.EVENT_TYPES
                return render(request, 'add_event.html', {'form': form, 'matches': matches, 'event_types': event_types})
            event.owner = request.user # Ustaw właściciela wydarzenia na zalogowanego użytkownika
            event.save() # Zapisz wydarzenie do bazy danych
            logger.info(f'Utworzono wydarzenie: {event.event_type} w meczu: {event.match.team_1.name} vs {event.match.team_2.name} przez użytkownika: {request.user.username}')
            return redirect('event_list')
        else:
            logger.warning(f'Błąd podczas tworzenia wydarzenia przez {request.user.username}: {form.errors}')
    else:
        form = MatchEventForm() # Utwórz nowy formularz
        # Ogranicz dostępne mecze do tych, które należą do użytkownika
        form.fields['match'].queryset = Match.objects.filter(owner=request.user, is_finished=False) # Pobierz tylko mecze, które nie są zakończone
    matches = Match.objects.filter(owner=request.user, is_finished=False) # Pobierz wszystkie mecze należące do zalogowanego użytkownika, które nie są zakończone
    event_types = MatchEvent.EVENT_TYPES # Pobierz dostępne typy wydarzeń

    return render(request, 'add_event.html', {'form': form, 'matches': matches, 'event_types': event_types,'selected_match_id': int(match_id) if match_id else None})

# Widok rejestracji użytkownika
def register_view(request):
    if request.method == 'POST':
        form = CustomUserCreationForm(request.POST) # Przekaż dane z formularza
        if form.is_valid():
            user = form.save(commit=False) # Utwórz instancję użytkownika, ale nie zapisuj jeszcze do bazy danych
            user.email = form.cleaned_data['email'] # Pobierz email z formularza
            user.save() # Zapisz użytkownika do bazy danych
            messages.success(request, 'Konto zostało pomyślnie utworzone! Możesz się teraz zalogować.')
            logger.info(f"Zarejestrowano konto dla użytkownika: {user.username} ({user.email})")
            return redirect('login') # Przekieruj na stronę logowania
        else:
            logger.warning(f"Błąd podczas rejestracji użytkownika: {form.errors}")
    else:
        form = CustomUserCreationForm() # Utwórz nowy formularz rejestracji
    return render(request, 'register.html', {'form': form})

# Widok logowania użytkownika
def login_view(request):
    if request.method == 'POST':
        form = AuthenticationForm(data=request.POST) # Przekaż dane z formularza logowania
        if form.is_valid():
            user = form.get_user() # Pobierz użytkownika z formularza
            login(request, user) # Zaloguj użytkownika
            logger.info(f"Użytkownik {user.username} zalogowany pomyślnie.")
            return redirect('team_list')
        else:
            logger.warning(f"Błąd logowania: {form.errors}")
    else:
        form = AuthenticationForm() # Utwórz nowy formularz logowania
    return render(request, 'login.html', {'form': form})

# Model piłkarza, powiązany z drużyną i właścicielem (użytkownikiem)
def team_ranking_list(request):
    if request.user.is_authenticated:
        leagues = League.objects.filter(owner=request.user) # Pobierz tylko ligi należące do zalogowanego użytkownika
    else:
        leagues = League.objects.filter(owner__isnull=False)

    selected_league_id = request.GET.get('league') # Pobierz ID wybranej ligi z parametrów GET

    # Sprawdź, czy wybrano ligę
    if selected_league_id:
        selected_league = get_object_or_404(League, pk=selected_league_id)
        generate_rankings(selected_league)
        rankings_qs = TeamRanking.objects.filter(league=selected_league).order_by('position')

        # dynamiczne dane
        matches = Match.objects.filter(league=selected_league, is_finished=True)  # Pobierz zakończone mecze w wybranej lidze
        enriched_rankings = [] # Lista słowników do przechowywania wzbogaconych rankingów
        for ranking in rankings_qs:
            team = ranking.team # Pobierz drużynę z rankingu
            team_matches = matches.filter(Q(team_1=team) | Q(team_2=team)) # Pobierz mecze, w których drużyna brała udział
            matches_played = team_matches.count() # Liczba rozegranych meczów przez drużynę
            wins = draws = losses = goals_for = goals_against = 0  # Inicjalizacja statystyk

            for match in team_matches:
                goals_team_1 = match.events.filter(player__team=match.team_1, event_type='goal').count() # Zliczanie goli drużyny 1
                goals_team_2 = match.events.filter(player__team=match.team_2, event_type='goal').count() # Zliczanie goli drużyny 2

                if match.team_1 == team:
                    gf, ga = goals_team_1, goals_team_2 # Gole dla drużyny 1 i przeciwko drużynie 2
                else:
                    gf, ga = goals_team_2, goals_team_1 # Gole dla drużyny 2 i przeciwko drużynie 1

                goals_for += gf # Gole zdobyte przez drużynę
                goals_against += ga # Gole stracone przez drużynę

                if gf > ga: # Jeśli drużyna zdobyła więcej goli niż przeciwnik
                    wins += 1 # Zwycięstwa
                elif gf == ga: # Jeśli drużyna zdobyła tyle samo goli co przeciwnik
                    draws += 1 # Remisy
                else:
                    losses += 1 # Przegrane

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
        enriched_rankings = [] # Pusta lista, jeśli nie wybrano ligi
        selected_league = None

    return render(request, 'team_ranking_list.html', {
        'leagues': leagues,
        'selected_league': selected_league,
        'rankings': enriched_rankings,  # ← teraz lista słowników z pełnymi danymi
    })

# Funkcja do generowania rankingów drużyn w lidze
def generate_rankings(league):
    with connection.cursor() as cursor: # Użyj kursora do wykonania zapytania SQL
        cursor.execute("SELECT update_team_rankings(%s);", [league.pk])  # Wywołaj funkcję SQL do aktualizacji rankingów drużyn

#@receiver(post_save, sender=Match)
#def update_rankings_after_match(sender, instance, **kwargs):
#    if instance.is_finished:
#        league = instance.league
#        generate_rankings(league)

# Funkcja do generowania statystyk piłkarzy w lidze
def generate_statistics(league):
    try:
        with connection.cursor() as cursor: # Użyj kursora do wykonania zapytania SQL
            cursor.execute("SELECT update_player_statistics(%s);", [league.pk]) # Wywołaj funkcję SQL do aktualizacji statystyk piłkarzy
        logger.info(f"Statystyki zawodników zaktualizowane przez funkcję SQL dla ligi {league.name}.")
    except Exception as e:
        logger.error(f"Optymalizacja statystyk nie powiodła się: {str(e)}")

# Funkcja do generowania statystyk dla pojedynczego piłkarza
def generate_statistics_for_player(player):
    try:
        leagues = League.objects.filter(teams__players=player).distinct() # Pobierz wszystkie ligi, w których gra piłkarz

        for league in leagues:
            # Liczba meczów rozegranych przez drużynę piłkarza w danej lidze (tylko zakończone mecze)
            matches_played = Match.objects.filter(
                (Q(team_1=player.team) | Q(team_2=player.team)), # Sprawdź, czy piłkarz jest w drużynie 1 lub 2
                league=league, # Sprawdź, czy mecz należy do danej ligi
                is_finished=True # Sprawdź, czy mecz jest zakończony
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
            if events.exists(): # Sprawdź, czy istnieją wydarzenia dla piłkarza w danej lidze
                goals = events.filter(event_type='goal').count() # Zliczanie goli
                yellow_cards = events.filter(event_type='yellow_card').count() # Zliczanie żółtych kartek
                red_cards = events.filter(event_type='red_card').count() # Zliczanie czerwonych kartek

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

# Widok do pobierania piłkarzy dla meczu
def match_players(request, match_id):
    match = get_object_or_404(Match, pk=match_id) # Pobranie meczu na podstawie ID
    players_team_1 = Player.objects.filter(team=match.team_1) # Pobranie piłkarzy z drużyny 1
    players_team_2 = Player.objects.filter(team=match.team_2) # Pobranie piłkarzy z drużyny 2
    players = list(players_team_1) + list(players_team_2) # Połączenie obu list piłkarzy
    data = {
        'players': [{'id': p.pk, 'name': str(p)} for p in players]
    }
    return JsonResponse(data)

# Widok do pobierania drużyn dla ligi
def get_teams_by_league(request, league_id):
    league = League.objects.get(pk=league_id) # Pobranie ligi na podstawie ID
    teams = league.teams.all() # Pobranie wszystkich drużyn przypisanych do tej ligi
    data = {'teams': [{'id': t.pk, 'name': t.name} for t in teams]} # Przygotowanie danych w formacie JSON
    return JsonResponse(data)

# Widok do pobierania meczów dla ligi
def get_matches_by_league(request, league_id):
    # Pokazuj tylko mecze z tej ligi, które nie są przypisane do żadnej kolejki
    matches = Match.objects.filter(league_id=league_id, rounds=None) # Pobranie meczów z danej ligi, które nie są przypisane do żadnej kolejki
    data = [ # Przygotowanie danych w formacie JSON
        {
            'id': m.pk,
            'team_1': m.team_1.name,
            'team_2': m.team_2.name,
            'date': str(m.match_date)
        }
        for m in matches
    ]
    return JsonResponse({'matches': data})

# Widok do pobierania meczów dla kolejki
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

# Widok do logowania dwustopniowego
def two_step_login_view(request):
    step = request.session.get('login_step', 1) # Pobierz aktualny krok logowania z sesji, domyślnie 1
    email = request.session.get('login_email') # Pobierz email z sesji, jeśli jest ustawiony
    error = None

    if request.method == 'POST':
        if step == 1:
            email = request.POST.get('email') # Pobierz email z formularza
            password = request.POST.get('password') # Pobierz hasło z formularza
            try:
                user = User.objects.get(email=email) # Pobierz użytkownika na podstawie emaila
                if user.check_password(password):
                    code = ''.join([str(random.randint(0, 9)) for _ in range(6)]) # Wygeneruj 6-cyfrowy kod logowania
                    request.session['login_code'] = code # Zapisz kod w sesji
                    request.session['login_email'] = email # Zapisz email w sesji
                    request.session['login_step'] = 2 # Ustaw krok logowania na 2
                    send_mail( # Wyślij email z kodem logowania
                        'Twój kod logowania',  # Temat emaila
                        f'Twój kod logowania: {code}', # Treść emaila
                        'planer.zawodow@wp.pl', # Adres nadawcy
                        [email], # Adres odbiorcy
                        fail_silently=False,
                    )
                    logger.info(f"Wysłano kod logowania na email: {email}")
                    step = 2
                else:
                    error = "Nieprawidłowy email lub hasło."
            except User.DoesNotExist:
                error = "Nieprawidłowy email lub hasło."
        elif step == 2:
            code = ''.join([request.POST.get(f'code_{i}', '') for i in range(6)]) # Pobierz kod z formularza, zakładając, że jest podzielony na 6 pól
            session_code = request.session.get('login_code') # Pobierz kod z sesji
            email = request.session.get('login_email') # Pobierz email z sesji
            try:
                user = User.objects.get(email=email) # Pobierz użytkownika na podstawie emaila
                if code == session_code:
                    login(request, user) # Zaloguj użytkownika, jeśli kod jest poprawny
                    logger.info(f"Użytkownik {user.username} zalogowany dwustopniowo pomyślnie.")
                    # Wyczyść sesję
                    request.session.pop('login_code', None) # Usuń kod logowania z sesji
                    request.session.pop('login_email', None) # Usuń email z sesji
                    request.session.pop('login_step', None) # Usuń krok logowania z sesji
                    return redirect('team_list') # Przekieruj do listy drużyn po pomyślnym zalogowaniu
                else:
                    error = "Nieprawidłowy kod."
            except User.DoesNotExist:
                error = "Coś poszło nie tak. Spróbuj ponownie."
    else:
        request.session['login_step'] = 1 # Jeśli żądanie nie jest POST, ustaw krok logowania na 1
        step = 1 # Zresetuj krok logowania

    return render(request, 'two_step_login.html', {
        'step': step,
        'email': email,
        'error': error,
    })

# Widok do generowania meczów w lidze
@login_required
@require_http_methods(["GET", "POST"])
def generate_matches(request):
    leagues = League.objects.filter(owner=request.user) # Pobierz wszystkie ligi należące do zalogowanego użytkownika

    if request.method == 'POST':
        league_id = request.POST.get('league') # ID wybranej ligi z formularza
        match_type = request.POST.get('match_type')  # 'single' lub 'double'
        start_date = request.POST.get('start_date') # Data rozpoczęcia generowania meczów
        interval_days = request.POST.get('interval_days') # Liczba dni między meczami
        match_time = request.POST.get('match_time') # Czas rozpoczęcia meczów

        if not (league_id and match_type and start_date and interval_days and match_time):
            messages.error(request, "Wszystkie pola są wymagane.")
            return render(request, 'generate_matches.html', {'leagues': leagues})

        try:
            league = League.objects.get(pk=league_id, owner=request.user) # Pobierz ligę na podstawie ID i sprawdź, czy należy do zalogowanego użytkownika

            with connection.cursor() as cursor: # Użyj kursora do wykonania zapytania SQL
                cursor.execute(
                    "CALL generate_matches_for_league(%s, %s, %s, %s, %s, %s)", # Wywołanie procedury SQL do generowania meczów
                    [
                        int(league_id), # ID ligi
                        start_date, # Data rozpoczęcia generowania meczów
                        match_time, # Czas rozpoczęcia meczów
                        int(interval_days), # Liczba dni między meczami
                        match_type, # Typ meczu ('single' lub 'double')
                        request.user.pk # ID zalogowanego użytkownika (owner ligi, który generuje mecze)
                    ]
                )

            messages.success(request, "Mecze zostały wygenerowane.")
            return redirect('match_list')

        except League.DoesNotExist: # Sprawdź, czy liga istnieje
            messages.error(request, "Wybrana liga nie istnieje lub nie masz do niej dostępu.")
        except Exception as e:
            logger.error(f'Błąd podczas generowania meczów przez {request.user.username}: {e}')
            messages.error(request, "Wystąpił błąd podczas generowania meczów: " + str(e))

    return render(request, 'generate_matches.html', {'leagues': leagues})

class TeamListAPI(generics.ListAPIView):
    queryset = Team.objects.all()
    serializer_class = TeamSerializer

class PlayerListAPI(generics.ListAPIView):
    queryset = Player.objects.all()
    serializer_class = PlayerSerializer

class LeagueListAPI(generics.ListAPIView):
    queryset = League.objects.all()
    serializer_class = LeagueSerializer

class MatchListAPI(generics.ListAPIView):
    queryset = Match.objects.all()
    serializer_class = MatchSerializer
