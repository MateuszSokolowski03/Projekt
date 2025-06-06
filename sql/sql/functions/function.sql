CREATE OR REPLACE FUNCTION update_team_rankings(p_league_id INTEGER)
RETURNS VOID AS $$
DECLARE
    team_rec RECORD;
    match_rec RECORD;
    team_points JSONB := '{}';
    v_team_id INT;
    v_points INT;
    pos INT := 1;
BEGIN
    -- Pobierz drużyny w lidze
    FOR team_rec IN
        SELECT t.team_id
        FROM planner_team t
        JOIN planner_league_teams lt ON lt.team_id = t.team_id
        WHERE lt.league_id = p_league_id
    LOOP
        team_points := team_points || jsonb_build_object(team_rec.team_id::TEXT, 0);
    END LOOP;

    -- Przetwarzanie zakończonych meczów
    FOR match_rec IN
        SELECT * FROM planner_match
        WHERE league_id = p_league_id AND is_finished = TRUE
    LOOP
        IF match_rec.score_team_1 > match_rec.score_team_2 THEN
            team_points := jsonb_set(team_points, ('{' || match_rec.team_1_id || '}')::TEXT[], 
                to_jsonb((team_points->>match_rec.team_1_id::TEXT)::INT + 3));
        ELSIF match_rec.score_team_1 < match_rec.score_team_2 THEN
            team_points := jsonb_set(team_points, ('{' || match_rec.team_2_id || '}')::TEXT[], 
                to_jsonb((team_points->>match_rec.team_2_id::TEXT)::INT + 3));
        ELSE
            team_points := jsonb_set(team_points, ('{' || match_rec.team_1_id || '}')::TEXT[], 
                to_jsonb((team_points->>match_rec.team_1_id::TEXT)::INT + 1));
            team_points := jsonb_set(team_points, ('{' || match_rec.team_2_id || '}')::TEXT[], 
                to_jsonb((team_points->>match_rec.team_2_id::TEXT)::INT + 1));
        END IF;
    END LOOP;

    -- Zapisanie punktów
    FOR v_team_id, v_points IN
        SELECT key::INT, value::INT FROM jsonb_each(team_points)
    LOOP
        INSERT INTO planner_teamranking (team_id, league_id, points, position)
        VALUES (v_team_id, p_league_id, v_points, 0)
        ON CONFLICT ("team_id", "league_id")
        DO UPDATE SET points = EXCLUDED.points;
    END LOOP;

    -- Ustawienie pozycji
    FOR team_rec IN
        SELECT * FROM planner_teamranking
        WHERE league_id = p_league_id
        ORDER BY points DESC, team_id
    LOOP
        UPDATE planner_teamranking
        SET position = pos
        WHERE ranking_id = team_rec.ranking_id;
        pos := pos + 1;
    END LOOP;
END;
$$ LANGUAGE plpgsql;


CREATE OR REPLACE FUNCTION update_match_score()
RETURNS TRIGGER AS $$
DECLARE
    v_match_id INTEGER;
BEGIN
    IF TG_OP = 'DELETE' THEN
        v_match_id := OLD.match_id;
    ELSE
        v_match_id := NEW.match_id;
    END IF;

    UPDATE planner_match
    SET
        score_team_1 = (
            SELECT COUNT(*)
            FROM planner_matchevent e
            JOIN planner_player p ON e.player_id = p.player_id
            WHERE e.match_id = v_match_id
              AND e.event_type = 'goal'
              AND p.team_id = planner_match.team_1_id
        ),
        score_team_2 = (
            SELECT COUNT(*)
            FROM planner_matchevent e
            JOIN planner_player p ON e.player_id = p.player_id
            WHERE e.match_id = v_match_id
              AND e.event_type = 'goal'
              AND p.team_id = planner_match.team_2_id
        )
    WHERE match_id = v_match_id;
    RETURN NULL;
END;
$$ LANGUAGE plpgsql;


CREATE OR REPLACE FUNCTION trigger_update_rankings()
RETURNS TRIGGER AS $$
BEGIN
    -- Tylko jeśli mecz został zakończony
    IF NEW.is_finished = TRUE AND (OLD.is_finished IS DISTINCT FROM NEW.is_finished) THEN
        PERFORM update_team_rankings(NEW.league_id);
    END IF;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;


CREATE OR REPLACE FUNCTION log_audit_event()
RETURNS TRIGGER AS $$
BEGIN
    INSERT INTO audit_log (
        username,
        action,
        table_name,
        old_data,
        new_data,
        record_id
    ) VALUES (
        current_user,
        TG_OP,
        TG_TABLE_NAME,
        CASE WHEN TG_OP IN ('UPDATE', 'DELETE') THEN to_jsonb(OLD) ELSE NULL END,
        CASE WHEN TG_OP IN ('INSERT', 'UPDATE') THEN to_jsonb(NEW) ELSE NULL END,
        COALESCE(NEW.id, OLD.id)
    );
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;




DROP FUNCTION IF EXISTS trigger_update_player_statistics();
CREATE OR REPLACE FUNCTION trigger_update_player_statistics()
RETURNS TRIGGER AS $$
BEGIN
    PERFORM update_player_statistics(NEW.league_id);
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;


CREATE OR REPLACE FUNCTION update_player_statistics(p_league_id INTEGER)
RETURNS VOID AS $$
BEGIN
    -- Usuwamy stare statystyki dla ligi (opcjonalnie, jeśli chcesz mieć zawsze aktualne)
    DELETE FROM planner_playerstatistics WHERE league_id = p_league_id;

    -- Wstawiamy nowe statystyki
    INSERT INTO planner_playerstatistics (player_id, league_id, matches_played, goals, yellow_cards, red_cards)
    SELECT
        p.player_id,
        l.league_id,
        (
            SELECT COUNT(DISTINCT m.match_id)
            FROM planner_match m
            WHERE (m.team_1_id = p.team_id OR m.team_2_id = p.team_id)
              AND m.league_id = l.league_id
              AND m.is_finished = TRUE
        ) AS matches_played,
        COALESCE(SUM(CASE WHEN e.event_type = 'goal' THEN 1 ELSE 0 END), 0) AS goals,
        COALESCE(SUM(CASE WHEN e.event_type = 'yellow_card' THEN 1 ELSE 0 END), 0) AS yellow_cards,
        COALESCE(SUM(CASE WHEN e.event_type = 'red_card' THEN 1 ELSE 0 END), 0) AS red_cards
    FROM planner_player p
    JOIN planner_team t ON p.team_id = t.team_id
    JOIN planner_league_teams lt ON t.team_id = lt.team_id
    JOIN planner_league l ON lt.league_id = l.league_id
    LEFT JOIN planner_matchevent e ON e.player_id = p.player_id
        AND e.match_id IN (
            SELECT match_id FROM planner_match WHERE league_id = l.league_id AND is_finished = TRUE
        )
    WHERE l.league_id = p_league_id
    GROUP BY p.player_id, l.league_id;
END;
$$ LANGUAGE plpgsql;


-- EDYCJA WYDARZEN
DROP FUNCTION IF EXISTS trigger_update_player_statistics_event();
CREATE OR REPLACE FUNCTION trigger_update_player_statistics_event()
RETURNS TRIGGER AS $$
DECLARE
    v_league_id INTEGER;
BEGIN
    IF TG_OP = 'DELETE' THEN
        SELECT league_id INTO v_league_id FROM planner_match WHERE match_id = OLD.match_id;
    ELSE
        SELECT league_id INTO v_league_id FROM planner_match WHERE match_id = NEW.match_id;
    END IF;
    PERFORM update_player_statistics(v_league_id);
    RETURN NULL;
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS trg_update_player_statistics_event ON planner_matchevent;
CREATE TRIGGER trg_update_player_statistics_event
AFTER INSERT OR UPDATE OR DELETE ON planner_matchevent
FOR EACH ROW
EXECUTE FUNCTION trigger_update_player_statistics_event();


-- EDYCJA MECZU
DROP FUNCTION IF EXISTS trigger_update_player_statistics_match_delete();
CREATE OR REPLACE FUNCTION trigger_update_player_statistics_match_delete()
RETURNS TRIGGER AS $$
BEGIN
    PERFORM update_player_statistics(OLD.league_id);
    RETURN OLD;
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS trg_update_player_statistics_match_delete ON planner_match;
CREATE TRIGGER trg_update_player_statistics_match_delete
AFTER DELETE ON planner_match
FOR EACH ROW
EXECUTE FUNCTION trigger_update_player_statistics_match_delete();