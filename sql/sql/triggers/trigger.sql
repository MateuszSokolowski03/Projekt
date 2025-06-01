-- Trigger wywołujący funkcję po INSERT/UPDATE/DELETE na planner_matchevent
DROP TRIGGER IF EXISTS trg_update_match_score ON planner_matchevent;
CREATE TRIGGER trg_update_match_score
AFTER INSERT OR UPDATE OR DELETE ON planner_matchevent
FOR EACH ROW
EXECUTE FUNCTION update_match_score();