CREATE OR REPLACE FUNCTION check_max_players_per_team()
RETURNS TRIGGER AS $$
DECLARE
    player_count INTEGER;
BEGIN
    SELECT COUNT(*) INTO player_count FROM planner_player WHERE team_id = NEW.team_id;
    IF player_count >= 11 THEN
        RAISE EXCEPTION 'Nie można dodać więcej niż 11 zawodników do jednej drużyny!';
    END IF;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;



CREATE OR REPLACE FUNCTION check_min_players_for_match()
RETURNS TRIGGER AS $$
DECLARE
    team1_count INTEGER;
    team2_count INTEGER;
BEGIN
    SELECT COUNT(*) INTO team1_count FROM planner_player WHERE team_id = NEW.team_1_id;
    SELECT COUNT(*) INTO team2_count FROM planner_player WHERE team_id = NEW.team_2_id;

    IF team1_count < 7 THEN
        RAISE EXCEPTION 'Drużyna 1 (ID: %) ma mniej niż 7 zawodników!', NEW.team_1_id;
    ELSIF team2_count < 7 THEN
        RAISE EXCEPTION 'Drużyna 2 (ID: %) ma mniej niż 7 zawodników!', NEW.team_2_id;
    END IF;

    RETURN NEW;
END;
$$ LANGUAGE plpgsql;