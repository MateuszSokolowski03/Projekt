CREATE OR REPLACE FUNCTION update_team_rankings(p_league_id INTEGER)
RETURNS VOID AS $$
DECLARE
    team_rec RECORD;
    match_rec RECORD;
    team_points JSONB := '{}';
    team_id INT;
    points INT;
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
            team_points := jsonb_set(team_points, ('{' || match_rec.team_1 || '}')::TEXT[], 
                to_jsonb((team_points->>match_rec.team_1::TEXT)::INT + 3));
        ELSIF match_rec.score_team_1 < match_rec.score_team_2 THEN
            team_points := jsonb_set(team_points, ('{' || match_rec.team_2 || '}')::TEXT[], 
                to_jsonb((team_points->>match_rec.team_2::TEXT)::INT + 3));
        ELSE
            team_points := jsonb_set(team_points, ('{' || match_rec.team_1 || '}')::TEXT[], 
                to_jsonb((team_points->>match_rec.team_1::TEXT)::INT + 1));
            team_points := jsonb_set(team_points, ('{' || match_rec.team_2 || '}')::TEXT[], 
                to_jsonb((team_points->>match_rec.team_2::TEXT)::INT + 1));
        END IF;
    END LOOP;

    -- Zapisanie punktów
    FOR team_id, points IN
        SELECT key::INT, value::INT FROM jsonb_each(team_points)
    LOOP
        INSERT INTO planner_teamranking (team_id, league_id, points, position)
        VALUES (team_id, p_league_id, points, 0)
        ON CONFLICT (team_id, league_id)
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
