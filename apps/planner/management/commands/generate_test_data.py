# apps/planner/management/commands/generate_test_data.py
import random
from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from apps.planner.models import Team, Player, League, Round, Match, MatchEvent

class Command(BaseCommand):
    help = "Generuje testowe drużyny, zawodników, ligi, kolejki, mecze i wydarzenia"

    def handle(self, *args, **kwargs):
        user, _ = User.objects.get_or_create(username="testuser", defaults={"password": "testpassword"})
        teams = []
        for i in range(20):
            team, _ = Team.objects.get_or_create(name=f"Drużyna {i}", owner=user)
            teams.append(team)
            for j in range(11):
                Player.objects.get_or_create(
                    first_name=f"Imię{i}{j}",
                    last_name=f"Nazwisko{i}{j}",
                    position=random.choice(['GK', 'DEF', 'MID', 'FWD']),
                    team=team,
                    owner=user
                )

        leagues = []
        for l in range(3):
            league, _ = League.objects.get_or_create(name=f"Liga {l}", owner=user)
            league_teams = random.sample(teams, 6)
            league.teams.set(league_teams)
            leagues.append(league)

            for r in range(3):
                round_obj, _ = Round.objects.get_or_create(number=r+1, league=league, owner=user)
                matches = []
                used_pairs = set()
                for m in range(3):
                    t1, t2 = random.sample(league_teams, 2)
                    while (t1.pk, t2.pk) in used_pairs or (t2.pk, t1.pk) in used_pairs:
                        t1, t2 = random.sample(league_teams, 2)
                    used_pairs.add((t1.pk, t2.pk))
                    match, _ = Match.objects.get_or_create(
                        league=league,
                        team_1=t1,
                        team_2=t2,
                        match_date="2024-06-01",
                        match_time="18:00",
                        owner=user
                    )
                    matches.append(match)
                    # Dodaj wydarzenia do meczu
                    for e in range(5):
                        player = random.choice(list(Player.objects.filter(team__in=[t1, t2])))
                        MatchEvent.objects.get_or_create(
                            match=match,
                            minute=random.randint(1, 90),
                            event_type=random.choice(['goal', 'yellow_card', 'red_card']),
                            player=player,
                            owner=user
                        )
                round_obj.matches.set(matches)

        self.stdout.write(self.style.SUCCESS("Wygenerowano dane testowe: drużyny, zawodników, ligi, kolejki, mecze, wydarzenia."))