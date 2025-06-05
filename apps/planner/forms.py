from django import forms
from .models import Team, Player, League, Round, Match, MatchEvent,TeamRanking
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User

class TeamForm(forms.ModelForm):
    class Meta:
        model = Team
        fields = ['team_id', 'name']
    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user', None)
        super(TeamForm, self).__init__(*args, **kwargs)


class PlayerForm(forms.ModelForm):
    class Meta:
        model = Player
        fields = ['player_id', 'first_name', 'last_name', 'position', 'team']

class LeagueForm(forms.ModelForm):
    teams = forms.ModelMultipleChoiceField(
        queryset=Team.objects.all(),
        required=False,
        widget=forms.CheckboxSelectMultiple
    )

    class Meta:
        model = League
        fields = ['league_id', 'name', 'teams']



class RoundForm(forms.ModelForm):
    matches = forms.ModelMultipleChoiceField(
        queryset=Match.objects.all(),
        required=False
    )

    class Meta:
        model = Round
        fields = ['round_id', 'number', 'league', 'matches']

class MatchForm(forms.ModelForm):
    class Meta:
        model = Match
        fields = ['league', 'team_1', 'team_2', 'match_date', 'match_time']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        
class MatchEventForm(forms.ModelForm):
    class Meta:
        model = MatchEvent
        fields = ['match', 'minute', 'event_type', 'player']
class TeamRankingForm(forms.ModelForm):
    class Meta:
        model = TeamRanking
        fields = ['team', 'league', 'points', 'position']
        widgets = {
            'league': forms.Select(attrs={'class': 'form-control'}),
            'team': forms.Select(attrs={'class': 'form-control'}),
            'points': forms.NumberInput(attrs={'class': 'form-control'}),
            'position': forms.NumberInput(attrs={'class': 'form-control'}),
        }

class CustomUserCreationForm(UserCreationForm):
    email = forms.EmailField(required=True, label="Email")

    class Meta:
        model = User
        fields = ("username", "email", "password1", "password2")