from django import forms
from .models import Team, Player, League, Round, Match, MatchEvent

class TeamForm(forms.ModelForm):
    class Meta:
        model = Team
        fields = ['team_id', 'name']

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

from .models import Round, Match

class RoundForm(forms.ModelForm):
    matches = forms.ModelMultipleChoiceField(
        queryset=Match.objects.all(),
        required=False
    )

    class Meta:
        model = Round
        fields = ['round_id', 'name', 'league', 'matches']

class MatchForm(forms.ModelForm):
    class Meta:
        model = Match
        fields = ['match_id', 'team_1', 'team_2', 'match_date', 'match_time']

class MatchEventForm(forms.ModelForm):
    class Meta:
        model = MatchEvent
        fields = ['match', 'minute', 'event_type', 'player']