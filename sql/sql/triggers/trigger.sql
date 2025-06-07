-- Trigger: po każdej zmianie (INSERT/UPDATE/DELETE) w planner_matchevent aktualizuje wynik meczu
DROP TRIGGER IF EXISTS trg_update_match_score ON planner_matchevent;
CREATE TRIGGER trg_update_match_score
AFTER INSERT OR UPDATE OR DELETE ON planner_matchevent
FOR EACH ROW
EXECUTE FUNCTION update_match_score();

-- Trigger: po aktualizacji meczu (gdy zmieni się status zakończenia) aktualizuje ranking drużyn
DROP TRIGGER IF EXISTS trg_update_rankings_after_match ON planner_match;
CREATE TRIGGER trg_update_rankings_after_match
AFTER UPDATE ON planner_match
FOR EACH ROW
EXECUTE FUNCTION trigger_update_rankings();


-- Trigger: przed dodaniem gracza sprawdza limit zawodników w drużynie
DROP TRIGGER IF EXISTS trg_max_players_per_team ON planner_player;
CREATE TRIGGER trg_max_players_per_team
BEFORE INSERT ON planner_player
FOR EACH ROW
EXECUTE FUNCTION check_max_players_per_team();

-- Trigger: przed dodaniem meczu sprawdza minimalną liczbę graczy w drużynach
DROP TRIGGER IF EXISTS trg_min_players_for_match ON planner_match;
CREATE TRIGGER trg_min_players_for_match
BEFORE INSERT ON planner_match
FOR EACH ROW
EXECUTE FUNCTION check_min_players_for_match();

-- Trigger: po zakończeniu meczu aktualizuje statystyki graczy w lidze
DROP TRIGGER IF EXISTS trg_update_player_statistics_after_match ON planner_match;
CREATE TRIGGER trg_update_player_statistics_after_match
AFTER UPDATE ON planner_match
FOR EACH ROW
WHEN (NEW.is_finished = TRUE AND (OLD.is_finished IS DISTINCT FROM NEW.is_finished))
EXECUTE FUNCTION trigger_update_player_statistics();

-- Trigger: po każdej zmianie wydarzenia meczu aktualizuje statystyki graczy
DROP TRIGGER IF EXISTS trg_update_player_statistics_event ON planner_matchevent;
CREATE TRIGGER trg_update_player_statistics_event
AFTER INSERT OR UPDATE OR DELETE ON planner_matchevent
FOR EACH ROW
EXECUTE FUNCTION trigger_update_player_statistics_event();

-- Trigger: po usunięciu meczu aktualizuje statystyki graczy w lidze
DROP TRIGGER IF EXISTS trg_update_player_statistics_match_delete ON planner_match;
CREATE TRIGGER trg_update_player_statistics_match_delete
AFTER DELETE ON planner_match
FOR EACH ROW
EXECUTE FUNCTION trigger_update_player_statistics_match_delete();