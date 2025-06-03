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