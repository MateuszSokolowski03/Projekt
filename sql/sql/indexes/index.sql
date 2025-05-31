CREATE INDEX idx_matchevent_match_eventtype
ON planner_matchevent (match_id, event_type);

CREATE INDEX idx_teamranking_league_team
ON planner_teamranking (league_id, team_id);

CREATE INDEX idx_playerstatistics_player
ON planner_playerstatistics (player_id);

CREATE INDEX idx_team_owner ON planner_team (owner_id);
CREATE INDEX idx_player_owner ON planner_player (owner_id);
CREATE INDEX idx_match_owner ON planner_match (owner_id);
CREATE INDEX idx_league_owner ON planner_league (owner_id);

CREATE INDEX idx_match_league ON planner_match (league_id);

CREATE INDEX idx_player_team ON planner_player (team_id);