from django import forms
from .models import Team, Player, League, Round, Match, MatchEvent,TeamRanking
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User

# Model formularzy dla drużyny
class TeamForm(forms.ModelForm):
    class Meta:
        model = Team # Upewnij się, że model Team jest poprawnie zaimportowany
        fields = ['team_id', 'name', 'logo']  # 'logo' jako string, jeśli jest to pole tekstowe lub URL
    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user', None) # Pobierz użytkownika z argumentów
        super(TeamForm, self).__init__(*args, **kwargs)

# Formularz dla piłkarza
class PlayerForm(forms.ModelForm):
    class Meta:
        model = Player # Upewnij się, że model Player jest poprawnie zaimportowany
        fields = ['player_id', 'first_name', 'last_name', 'position', 'team', 'profile_picture'] # 'profile_picture' jako string, jeśli jest to pole tekstowe lub URL

# Formularz dla ligi
class LeagueForm(forms.ModelForm):
    teams = forms.ModelMultipleChoiceField( # Wybór wielu drużyn
        queryset=Team.objects.all(),  # Pobierz wszystkie drużyny
        required=False, # Pole nie jest wymagane
        widget=forms.CheckboxSelectMultiple # Użyj widgetu do wyboru wielu opcji
    )

    class Meta:
        model = League # Upewnij się, że model League jest poprawnie zaimportowany
        fields = ['league_id', 'name', 'teams']

# Formularz dla kolejki
class RoundForm(forms.ModelForm):
    matches = forms.ModelMultipleChoiceField( # Wybór wielu meczów
        queryset=Match.objects.all(), # Pobierz wszystkie mecze
        required=False # Pole nie jest wymagane
    )

    class Meta:
        model = Round # Upewnij się, że model Round jest poprawnie zaimportowany
        fields = ['round_id', 'number', 'league', 'matches']

    def clean(self):
        cleaned_data = super().clean() # Pobierz oczyszczone dane
        number = cleaned_data.get('number') # Numer kolejki
        league = cleaned_data.get('league') # Liga, do której należy kolejka
        if number and league:
            qs = Round.objects.filter(number=number, league=league) # Filtruj kolejki według numeru i ligi
            if self.instance.pk:
                qs = qs.exclude(pk=self.instance.pk) # Wyklucz aktualną instancję, jeśli jest edytowana
            if qs.exists():
                raise forms.ValidationError("Numer kolejki musi być unikalny w danej lidze.")
        return cleaned_data
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Pokaż tylko mecze nieprzypisane do żadnej kolejki
        self.fields['matches'].queryset = Match.objects.filter(rounds=None)

# Formularz dla meczu
class MatchForm(forms.ModelForm):
    class Meta:
        model = Match # Upewnij się, że model Match jest poprawnie zaimportowany
        fields = ['league', 'team_1', 'team_2', 'match_date', 'match_time']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

# Formularz dla wydarzenia meczu
class MatchEventForm(forms.ModelForm):
    class Meta:
        model = MatchEvent # Upewnij się, że model MatchEvent jest poprawnie zaimportowany
        fields = ['match', 'minute', 'event_type', 'player']

# Formularz dla rankingu drużyn
class TeamRankingForm(forms.ModelForm):
    class Meta:
        model = TeamRanking # Upewnij się, że model TeamRanking jest poprawnie zaimportowany
        fields = ['team', 'league', 'points', 'position']
        widgets = { # Użyj widgetów do stylizacji pól formularza
            'league': forms.Select(attrs={'class': 'form-control'}), # Wybór ligi
            'team': forms.Select(attrs={'class': 'form-control'}), # Wybór drużyny
            'points': forms.NumberInput(attrs={'class': 'form-control'}), # Pole punktów
            'position': forms.NumberInput(attrs={'class': 'form-control'}), # Pole pozycji
        }

# Formularz rejestracji użytkownika
class CustomUserCreationForm(UserCreationForm):
    email = forms.EmailField(required=True, label="Email")

    class Meta:
        model = User # Upewnij się, że model User jest poprawnie zaimportowany
        fields = ("username", "email", "password1", "password2") # Pola formularza do rejestracji użytkownika