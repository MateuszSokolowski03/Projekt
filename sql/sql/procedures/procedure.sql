-- Procedura generująca mecze dla ligi (single: każdy z każdym, double: mecz + rewanż)
CREATE OR REPLACE PROCEDURE generate_matches_for_league(
    p_league_id INT,
    p_start_date DATE,
    p_match_time TIME,
    p_interval_days INT,
    p_match_type TEXT, -- 'single' lub 'double'
    p_owner_id INT
)
LANGUAGE plpgsql
AS $$
DECLARE
    teams INT[];
    idx INT := 0;
    match_date DATE := p_start_date;
BEGIN
    SELECT array_agg(team_id) INTO teams FROM planner_league_teams WHERE league_id = p_league_id;

    IF array_length(teams, 1) IS NULL OR array_length(teams, 1) < 2 THEN
        RAISE EXCEPTION 'Liga musi mieć co najmniej 2 drużyny.';
    END IF;

    IF p_match_type = 'single' THEN
        FOR i IN 1 .. array_length(teams, 1) - 1 LOOP
            FOR j IN i + 1 .. array_length(teams, 1) LOOP
                IF NOT EXISTS (
                    SELECT 1 FROM planner_match
                    WHERE league_id = p_league_id AND team_1_id = teams[i] AND team_2_id = teams[j]
                ) THEN
                    INSERT INTO planner_match (
                        league_id, team_1_id, team_2_id, match_date, match_time, owner_id, score_team_1, score_team_2, is_finished
                    )
                    VALUES (
                        p_league_id, teams[i], teams[j], match_date + (idx * p_interval_days), p_match_time, p_owner_id, 0, 0, FALSE
                    );
                    idx := idx + 1;
                END IF;
            END LOOP;
        END LOOP;
    ELSE
        FOR i IN 1 .. array_length(teams, 1) LOOP
            FOR j IN 1 .. array_length(teams, 1) LOOP
                IF i <> j THEN
                    IF NOT EXISTS (
                        SELECT 1 FROM planner_match
                        WHERE league_id = p_league_id AND team_1_id = teams[i] AND team_2_id = teams[j]
                    ) THEN
                        INSERT INTO planner_match (
                            league_id, team_1_id, team_2_id, match_date, match_time, owner_id, score_team_1, score_team_2, is_finished
                        )
                        VALUES (
                            p_league_id, teams[i], teams[j], match_date + (idx * p_interval_days), p_match_time, p_owner_id, 0, 0, FALSE
                        );
                        idx := idx + 1;
                    END IF;
                END IF;
            END LOOP;
        END LOOP;
    END IF;
END;
$$;