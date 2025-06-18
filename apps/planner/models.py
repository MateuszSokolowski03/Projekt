from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
from django.contrib.auth.models import User
import logging
from django.shortcuts import render

logger = logging.getLogger(__name__)

# Model drużyny piłkarskiej
class Team(models.Model):
    team_id = models.AutoField(primary_key=True)  # Klucz główny
    name = models.CharField(max_length=255, unique=True) # Unikalna nazwa drużyny
    logo = models.ImageField(upload_to='team_logos/', null=True, blank=True) # Logo drużyny, opcjonalne
    owner = models.ForeignKey(User, on_delete=models.CASCADE, related_name='teams')  # Właściciel drużyny, powiązany z użytkownikiem

    def __str__(self):
        return self.name

    # Metoda do zwrócenia nazwy drużyny
    def save(self, *args, **kwargs):
        if self.pk:
            logger.info(f"Aktualizowano drużynę: {self.name} (ID: {self.pk})")
        else:
            logger.info(f"Utworzono drużynę: {self.name}")
        super().save(*args, **kwargs)

    # Metoda do usuwania drużyny, loguje informację o usunięciu
    def delete(self, *args, **kwargs):
        logger.warning(f"Usunięto drużynę: {self.name} (ID: {self.pk})")
        super().delete(*args, **kwargs)

# Model piłkarza, powiązany z drużyną i właścicielem (użytkownikiem)
class Player(models.Model):
    player_id = models.AutoField(primary_key=True)  # Klucz główny
    first_name = models.CharField(max_length=100) # Imię piłkarza
    last_name = models.CharField(max_length=100) # Nazwisko piłkarza
    POSITION_CHOICES = [ # Wybór pozycji piłkarza
        ('GK', 'Goalkeeper'),
        ('DEF', 'Defender'),
        ('MID', 'Midfielder'),
        ('FWD', 'Forward'),
    ]
    position = models.CharField(max_length=3, choices=POSITION_CHOICES) # Pole wyboru pozycji
    team = models.ForeignKey('Team', on_delete=models.CASCADE, related_name='players') # Powiązanie z drużyną
    owner = models.ForeignKey(User, on_delete=models.CASCADE, related_name='players') # Właściciel piłkarza, powiązany z użytkownikiem
    profile_picture = models.ImageField(upload_to='player_profiles/', null=True, blank=True) # Zdjęcie profilowe piłkarza, opcjonalne

    def __str__(self):
        return f"{self.first_name} {self.last_name} ({self.get_position_display()}, {self.team.name})"

    # Metoda do zwrócenia pełnej nazwy piłkarza
    def save(self, *args, **kwargs):
        if self.pk:
            logger.info(f"Aktualizowano piłkarza: {self.first_name} {self.last_name} (ID: {self.pk})")
        else:
            logger.info(f"Utworzono piłkarza: {self.first_name} {self.last_name}")
        super().save(*args, **kwargs)

    # Metoda do usuwania piłkarza, loguje informację o usunięciu
    def delete(self, *args, **kwargs):
        logger.warning(f"Usunięto piłkarza: {self.first_name} {self.last_name} (ID: {self.pk})")
        super().delete(*args, **kwargs)

# Model statystyk piłkarza, powiązany z ligą i piłkarzem
class PlayerStatistics(models.Model):
    statistics_id = models.AutoField(primary_key=True)  # Klucz główny
    league = models.ForeignKey('League', on_delete=models.CASCADE, related_name='player_statistics') # Powiązanie z ligą
    player = models.ForeignKey('Player', on_delete=models.CASCADE, related_name='statistics') # Powiązanie z piłkarzem
    matches_played = models.IntegerField(default=0) # Liczba rozegranych meczów
    goals = models.IntegerField(default=0) # Liczba strzelonych goli
    yellow_cards = models.IntegerField(default=0) # Liczba żółtych kartek
    red_cards = models.IntegerField(default=0) # Liczba czerwonych kartek

    def __str__(self):
        return f"Statystyki dla {self.player.first_name} {self.player.last_name}"

    # Metoda do zwrócenia statystyk piłkarza w formacie tekstowym
    def save(self, *args, **kwargs):
        logger.info(f"Zapisano statystyki dla gracza: {self.player} w lidze: {self.league}")
        super().save(*args, **kwargs)

# Model meczu, powiązany z ligą, drużynami i właścicielem (użytkownikiem)
class Match(models.Model):
    match_id = models.AutoField(primary_key=True)  # Klucz główny
    league = models.ForeignKey('League', on_delete=models.CASCADE, related_name='matches') # Powiązanie z ligą
    team_1 = models.ForeignKey('Team', on_delete=models.CASCADE, related_name='home_matches') # Drużyna gospodarzy
    team_2 = models.ForeignKey('Team', on_delete=models.CASCADE, related_name='away_matches') # Drużyna gości
    match_date = models.DateField()  # Data meczu
    match_time = models.TimeField()  # Godzina meczu
    score_team_1 = models.IntegerField(default=0) # Wynik drużyny 1
    score_team_2 = models.IntegerField(default=0) # Wynik drużyny 2
    owner = models.ForeignKey(User, on_delete=models.CASCADE, related_name='matches') # Właściciel meczu, powiązany z użytkownikiem
    is_finished = models.BooleanField(default=False) # Flaga informująca, czy mecz jest zakończony

    # Metoda do zwrócenia nazwy miesiąca w formacie 3-literowym po polsku
    def polish_month(self):
        # Mapowanie nazw miesięcy na 3-literowe skróty po polsku
        months = {
            1: "Sty", 2: "Lut", 3: "Mar", 4: "Kwi", 5: "Maj", 6: "Cze",
            7: "Lip", 8: "Sie", 9: "Wrz", 10: "Paź", 11: "Lis", 12: "Gru"
        }
        month = months[self.match_date.month]
        return f"{month}"

    # Metoda do zapisywania meczu, loguje informację o utworzeniu lub aktualizacji
    def save(self, *args, **kwargs):
        if self.pk:
            logger.info(f"Aktualizowano mecz: {self}")
        else:
            logger.info(f"Utworzono mecz: {self}")
        super().save(*args, **kwargs)


    def __str__(self):
        return f"{self.team_1.name} vs {self.team_2.name} ({self.match_date})"
    @property
    def dynamic_score_team_1(self): # Zlicza dynamicznie liczbę goli drużyny 1
        return self.events.filter(player__team=self.team_1, event_type='goal').count()

    @property
    def dynamic_score_team_2(self): # Zlicza dynamicznie liczbę goli drużyny 2
        return self.events.filter(player__team=self.team_2, event_type='goal').count()

# Wydarzenie w meczu (gol, kartka)
class MatchEvent(models.Model):
    event_id = models.AutoField(primary_key=True)  # Klucz główny
    match = models.ForeignKey('Match', on_delete=models.CASCADE, related_name='events') # Powiązanie z meczem
    minute = models.IntegerField(validators=[MinValueValidator(0), MaxValueValidator(90)]) # Minuta wydarzenia, z walidacją
    EVENT_TYPES = [ # Typy wydarzeń w meczu
        ('goal', 'Goal'),
        ('yellow_card', 'Yellow Card'),
        ('red_card', 'Red Card'),
    ]
    event_type = models.CharField(max_length=20, choices=EVENT_TYPES) # Pole wyboru typu wydarzenia
    player = models.ForeignKey('Player', on_delete=models.CASCADE) # Powiązanie z piłkarzem, który spowodował wydarzenie
    owner = models.ForeignKey(User, on_delete=models.CASCADE, related_name='match_events') # Właściciel wydarzenia, powiązany z użytkownikiem

    def __str__(self):
        return f"{self.event_type} at {self.minute} min in {self.match}"

    # Metoda do zwrócenia opisu wydarzenia w formacie tekstowym
    def save(self, *args, **kwargs):
        logger.info(f"Zapisano wydarzenie: {self.event_type} ({self.minute} min) w meczu: {self.match}")
        super().save(*args, **kwargs)

# Model rankingu drużyn w lidze
class TeamRanking(models.Model):
    ranking_id = models.AutoField(primary_key=True)  # Klucz główny
    team = models.ForeignKey('Team', on_delete=models.CASCADE, related_name='rankings') # Powiązanie z drużyną
    league = models.ForeignKey('League', on_delete=models.CASCADE, related_name='rankings') # Powiązanie z ligą
    points = models.IntegerField(default=0) # Punkty zdobyte przez drużynę w lidze
    position = models.IntegerField(default=0) # Pozycja drużyny w rankingu, domyślnie 0

    # Walidacja, aby punkty były nieujemne
    class Meta:
        constraints = [
             models.UniqueConstraint(fields=['team', 'league'], name='unique_team_league')
        ]

    def __str__(self):
        return f"{self.team.name} - {self.points} points, position {self.position} in {self.league.name}"

    # Metoda do zwrócenia opisu rankingu drużyny w formacie tekstowym
    def save(self, *args, **kwargs):
        logger.info(f"Zapisano ranking: {self}")
        super().save(*args, **kwargs)

# Model ligi, powiązany z drużynami i właścicielem (użytkownikiem)
class League(models.Model):
    league_id = models.AutoField(primary_key=True)  # Klucz główny
    name = models.CharField(max_length=255, unique=True) # Unikalna nazwa ligi
    teams = models.ManyToManyField('Team', related_name='leagues') # Powiązanie z drużynami, wiele do wielu
    owner = models.ForeignKey(User, on_delete=models.CASCADE, related_name='leagues') # Właściciel ligi, powiązany z użytkownikiem

    def __str__(self):
        return self.name

    # Metoda do zwrócenia nazwy ligi
    def save(self, *args, **kwargs):
        if self.pk:
            logger.info(f"Aktualizowano ligę: {self.name} (ID: {self.pk})")
        else:
            logger.info(f"Utworzono ligę: {self.name}")
        super().save(*args, **kwargs)

# Model rundy, powiązany z ligą, meczami i właścicielem (użytkownikiem)
class Round(models.Model):
    round_id = models.AutoField(primary_key=True)  # Klucz główny
    number = models.IntegerField(null=True, blank=True) # Numer rundy
    league = models.ForeignKey('League', on_delete=models.CASCADE, related_name='rounds') # Powiązanie z ligą
    matches = models.ManyToManyField('Match', related_name='rounds') # Powiązanie z meczami, wiele do wielu
    owner = models.ForeignKey(User, on_delete=models.CASCADE, related_name='rounds') # Właściciel rundy, powiązany z użytkownikiem

    def __str__(self):
        return f"{self.number} ({self.league.name})"

    # Metoda do zwrócenia opisu rundy w formacie tekstowym
    def save(self, *args, **kwargs):
        logger.info(f"Zapisano rundę: {self.number} w lidze: {self.league.name}")
        super().save(*args, **kwargs)

def index(request):
    return render(request, 'index.html')