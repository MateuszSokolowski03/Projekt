from django.contrib import admin
from .models import Team, Player, PlayerStatistics, Match, MatchEvent, TeamRanking, League, Round

# Rejestracja modeli w panelu administracyjnym
admin.site.register(Team)
admin.site.register(Player)
admin.site.register(PlayerStatistics)
admin.site.register(Match)
admin.site.register(MatchEvent)
admin.site.register(TeamRanking)
admin.site.register(League)
admin.site.register(Round)