-- Trigger wywołujący funkcję po INSERT/UPDATE/DELETE na planner_matchevent
DROP TRIGGER IF EXISTS trg_update_match_score ON planner_matchevent;
CREATE TRIGGER trg_update_match_score
AFTER INSERT OR UPDATE OR DELETE ON planner_matchevent
FOR EACH ROW
EXECUTE FUNCTION update_match_score();

DROP TRIGGER IF EXISTS trg_update_rankings_after_match ON planner_match;
CREATE TRIGGER trg_update_rankings_after_match
AFTER UPDATE ON planner_match
FOR EACH ROW
EXECUTE FUNCTION trigger_update_rankings();

CREATE TRIGGER users_audit_trigger
AFTER INSERT OR UPDATE OR DELETE ON users
FOR EACH ROW EXECUTE FUNCTION log_audit_event();






DROP TRIGGER IF EXISTS trg_max_players_per_team ON planner_player;

CREATE TRIGGER trg_max_players_per_team
BEFORE INSERT ON planner_player
FOR EACH ROW
EXECUTE FUNCTION check_max_players_per_team();


DROP TRIGGER IF EXISTS trg_min_players_for_match ON planner_match;

CREATE TRIGGER trg_min_players_for_match
BEFORE INSERT ON planner_match
FOR EACH ROW
EXECUTE FUNCTION check_min_players_for_match();



DROP TRIGGER IF EXISTS trg_update_player_statistics_after_match ON planner_match;
CREATE TRIGGER trg_update_player_statistics_after_match
AFTER UPDATE ON planner_match
FOR EACH ROW
WHEN (NEW.is_finished = TRUE AND (OLD.is_finished IS DISTINCT FROM NEW.is_finished))
EXECUTE FUNCTION trigger_update_player_statistics();