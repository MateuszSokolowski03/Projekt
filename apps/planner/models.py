from django.db import models
import locale
from django.shortcuts import render
from django.core.validators import MinValueValidator, MaxValueValidator
from django.contrib.auth.models import User
import logging

logger = logging.getLogger(__name__)

class Team(models.Model):
    team_id = models.AutoField(primary_key=True)  # Klucz główny
    name = models.CharField(max_length=255, unique=True)
    logo = models.ImageField(upload_to='team_logos/', null=True, blank=True)
    owner = models.ForeignKey(User, on_delete=models.CASCADE, related_name='teams', null=True, blank=True) 

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        if self.pk:
            logger.info(f"Aktualizowano drużynę: {self.name} (ID: {self.pk})")
        else:
            logger.info(f"Utworzono drużynę: {self.name}")
        super().save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        logger.warning(f"Usunięto drużynę: {self.name} (ID: {self.pk})")
        super().delete(*args, **kwargs)

class Player(models.Model):
    player_id = models.AutoField(primary_key=True)  # Klucz główny
    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)
    POSITION_CHOICES = [
        ('GK', 'Goalkeeper'),
        ('DEF', 'Defender'),
        ('MID', 'Midfielder'),
        ('FWD', 'Forward'),
    ]
    position = models.CharField(max_length=3, choices=POSITION_CHOICES)
    team = models.ForeignKey('Team', on_delete=models.CASCADE, related_name='players')
    owner = models.ForeignKey(User, on_delete=models.CASCADE, related_name='players', null=True, blank=True) 

    def __str__(self):
        return f"{self.first_name} {self.last_name} ({self.get_position_display()})"

    def save(self, *args, **kwargs):
        if self.pk:
            logger.info(f"Aktualizowano piłkarza: {self.first_name} {self.last_name} (ID: {self.pk})")
        else:
            logger.info(f"Utworzono piłkarza: {self.first_name} {self.last_name}")
        super().save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        logger.warning(f"Usunięto piłkarza: {self.first_name} {self.last_name} (ID: {self.pk})")
        super().delete(*args, **kwargs)

class PlayerStatistics(models.Model):
    statistics_id = models.AutoField(primary_key=True)  # Klucz główny
    league = models.ForeignKey('League', on_delete=models.CASCADE, related_name='player_statistics')
    player = models.ForeignKey('Player', on_delete=models.CASCADE, related_name='statistics') 
    matches_played = models.IntegerField(default=0)
    goals = models.IntegerField(default=0)
    yellow_cards = models.IntegerField(default=0)
    red_cards = models.IntegerField(default=0)

    def __str__(self):
        return f"Statystyki dla {self.player.first_name} {self.player.last_name}"

    def save(self, *args, **kwargs):
        logger.info(f"Zapisano statystyki dla gracza: {self.player} w lidze: {self.league}")
        super().save(*args, **kwargs)

class Match(models.Model):
    match_id = models.AutoField(primary_key=True)  # Klucz główny
    league = models.ForeignKey('League', on_delete=models.CASCADE, related_name='matches')
    team_1 = models.ForeignKey('Team', on_delete=models.CASCADE, related_name='home_matches')
    team_2 = models.ForeignKey('Team', on_delete=models.CASCADE, related_name='away_matches')
    match_date = models.DateField()  # Data meczu
    match_time = models.TimeField()  # Godzina meczu
    score_team_1 = models.IntegerField(default=0)
    score_team_2 = models.IntegerField(default=0)
    owner = models.ForeignKey(User, on_delete=models.CASCADE, related_name='matches', null=True, blank=True)
    is_finished = models.BooleanField(default=False) 
    
    def get_polish_month_short(self):
        # Mapowanie nazw miesięcy na 3-literowe skróty po polsku
        months = {
            1: "sty", 2: "lut", 3: "mar", 4: "kwi", 5: "maj", 6: "cze",
            7: "lip", 8: "sie", 9: "wrz", 10: "paź", 11: "lis", 12: "gru"
        }
        # day = self.match_date.day
        month = months[self.match_date.month]
        # year = self.match_date.year
        return f"{month}"

    def save(self, *args, **kwargs):
        if self.pk:
            logger.info(f"Aktualizowano mecz: {self}")
        else:
            logger.info(f"Utworzono mecz: {self}")
        super().save(*args, **kwargs)

    @property
    def dynamic_score_team_1(self):
        return self.events.filter(player__team=self.team_1, event_type='goal').count()

    @property
    def dynamic_score_team_2(self):
        return self.events.filter(player__team=self.team_2, event_type='goal').count()
    
class MatchEvent(models.Model):
    event_id = models.AutoField(primary_key=True)  # Klucz główny
    match = models.ForeignKey('Match', on_delete=models.CASCADE, related_name='events')
    minute = models.IntegerField(validators=[MinValueValidator(0), MaxValueValidator(90)])
    EVENT_TYPES = [
        ('goal', 'Goal'),
        ('yellow_card', 'Yellow Card'),
        ('red_card', 'Red Card'),
    ]
    event_type = models.CharField(max_length=20, choices=EVENT_TYPES)
    player = models.ForeignKey('Player', on_delete=models.CASCADE, null=True, blank=True)
    owner = models.ForeignKey(User, on_delete=models.CASCADE, related_name='match_events', null=True, blank=True) 

    def __str__(self):
        return f"{self.event_type} at {self.minute} min in {self.match}"

    def save(self, *args, **kwargs):
        logger.info(f"Zapisano wydarzenie: {self.event_type} ({self.minute} min) w meczu: {self.match}")
        super().save(*args, **kwargs)

class TeamRanking(models.Model):
    ranking_id = models.AutoField(primary_key=True)  # Klucz główny
    team = models.ForeignKey('Team', on_delete=models.CASCADE, related_name='rankings')  # Zmieniono na ForeignKey
    league = models.ForeignKey('League', on_delete=models.CASCADE, related_name='rankings')
    points = models.IntegerField(default=0)
    position = models.IntegerField(default=0)

    class Meta:
        constraints = [
             models.UniqueConstraint(fields=['team', 'league'], name='unique_team_league')
        ]

    def __str__(self):
        return f"{self.team.name} - {self.points} points, position {self.position} in {self.league.name}"

    def save(self, *args, **kwargs):
        logger.info(f"Zapisano ranking: {self}")
        super().save(*args, **kwargs)

class League(models.Model):
    league_id = models.AutoField(primary_key=True)  # Klucz główny
    name = models.CharField(max_length=255, unique=True)
    teams = models.ManyToManyField('Team', related_name='leagues')
    owner = models.ForeignKey(User, on_delete=models.CASCADE, related_name='leagues', null=True, blank=True)

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        if self.pk:
            logger.info(f"Aktualizowano ligę: {self.name} (ID: {self.pk})")
        else:
            logger.info(f"Utworzono ligę: {self.name}")
        super().save(*args, **kwargs)

class Round(models.Model):
    round_id = models.AutoField(primary_key=True)  # Klucz główny
    number = models.IntegerField(null=True, blank=True)    
    league = models.ForeignKey('League', on_delete=models.CASCADE, related_name='rounds')
    matches = models.ManyToManyField('Match', related_name='rounds')
    owner = models.ForeignKey(User, on_delete=models.CASCADE, related_name='rounds', null=True, blank=True)
    def __str__(self):
        return f"{self.number} ({self.league.name})"

    def save(self, *args, **kwargs):
        logger.info(f"Zapisano rundę: {self.number} w lidze: {self.league.name}")
        super().save(*args, **kwargs)

def index(request):
    return render(request, 'index.html')