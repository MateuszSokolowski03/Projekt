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

CREATE INDEX idx_playerstatistics_league ON planner_playerstatistics (league_id);

CREATE INDEX idx_round_owner ON planner_round (owner_id);

CREATE INDEX idx_match_is_finished ON planner_match (is_finished);

-- Złożony indeks na MatchEvent dla player_id, event_type i match_id
CREATE INDEX idx_event_player_type_match ON planner_matchevent (player_id, event_type, match_id);
CREATE INDEX idx_matchevent_player ON planner_matchevent (player_id);

-- Indeks na Match dla filtrowania po lidze i zakończonych meczach
CREATE INDEX idx_match_league_finished ON planner_match (league_id, is_finished);

-- Zwiazane z filtracja zawodnika
CREATE INDEX idx_player_position ON planner_player (position);
CREATE INDEX idx_player_team_position ON planner_player (team_id, position);

-- Zwiazane z filtracja kolejki
CREATE INDEX idx_round_league ON planner_round (league_id);

-- Indeksy z filtracja meczu
CREATE INDEX idx_match_team1 ON planner_match (team_1_id);
CREATE INDEX idx_match_team2 ON planner_match (team_2_id);
CREATE INDEX idx_match_date ON planner_match (match_date);
CREATE INDEX idx_match_team1_date ON planner_match (team_1_id, match_date);
CREATE INDEX idx_match_team2_date ON planner_match (team_2_id, match_date);