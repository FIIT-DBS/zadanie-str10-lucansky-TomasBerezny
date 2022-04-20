toto je berkov repozitar na dbs zadania

Zadanie 1:
Berezny_Zadanie_1.pdf

Zadanie 2:
branch zadanie2
https://fiit-dbs-xberezny.herokuapp.com/v1/health/


Zadanie 3:
taktiez na branchi zadanie2, su tam doplnene endpointy

http://fiit-dbs-xberezny.herokuapp.com/v2/patches/

http://fiit-dbs-xberezny.herokuapp.com/v2/players/<player_id>/game_exp



queries zadanie 5:

PURCHASES:

SELECT * FROM
(SELECT *, ROW_NUMBER() OVER (PARTITION BY hero_id ORDER BY COUNT DESC,item_name) AS item_num           
FROM (SELECT her.id AS hero_id, hero_localized_name AS hero_name, items.id AS item_id, items.name AS item_name, COUNT(items.id) FROM
(SELECT * FROM
(SELECT heroes.id,
    CASE
	    WHEN mpd.player_slot <=4 THEN matches.radiant_win
	    ELSE NOT matches.radiant_win
    END AS winner,
 	heroes.localized_name AS hero_localized_name,
 	mpd.id AS mpd_id
    FROM players
    JOIN matches_players_details mpd ON players.id = mpd.player_id
    JOIN heroes ON mpd.hero_id = heroes.id
    JOIN matches ON mpd.match_id = matches.id
    WHERE matches.id = """ +match_id+
    """ORDER BY id) AS her where winner = true) AS her 
	JOIN purchase_logs pl ON pl.match_player_detail_id = her.mpd_id
	JOIN items ON pl.item_id = items.id
	group BY items.name, her.id, hero_localized_name, items.id, items.name
	ORDER BY hero_id) AS musi_alias
	) AS musi_alias_dva
WHERE item_num <= 5

ABILITIES:

SELECT DISTINCT ON (hero_id, winner) heroes.id AS hero_id, 
CASE
	WHEN mpd.player_slot <= 4 THEN matches.radiant_win
	ELSE NOT matches.radiant_win
END AS winner,
heroes.localized_name AS hero_localized_name, 
abilities.name AS ability_name,
CASE
	WHEN 100*au.time/matches.duration >= 0 
	AND 100*au.time/matches.duration < 10 THEN '0-9'
	WHEN 100*au.time/matches.duration >= 10 
	AND 100*au.time/matches.duration < 20 THEN '10-19'
	WHEN 100*au.time/matches.duration >= 20 
	AND 100*au.time/matches.duration < 30 THEN '20-29'
	WHEN 100*au.time/matches.duration >= 30 
	AND 100*au.time/matches.duration < 40 THEN '30-39'
	WHEN 100*au.time/matches.duration >= 40 
	AND 100*au.time/matches.duration < 50 THEN '40-49'
	WHEN 100*au.time/matches.duration >= 50 
	AND 100*au.time/matches.duration < 60 THEN '50-59'
	WHEN 100*au.time/matches.duration >= 60 
	AND 100*au.time/matches.duration < 70 THEN '60-69'
	WHEN 100*au.time/matches.duration >= 70 
	AND 100*au.time/matches.duration < 80 THEN '70-79'
	WHEN 100*au.time/matches.duration >= 80 
	AND 100*au.time/matches.duration < 90 THEN '80-89'
	WHEN 100*au.time/matches.duration >= 90 
	AND 100*au.time/matches.duration < 100 THEN '90-99'
	ELSE '100-109'
END AS bucket,
COUNT(*)
FROM abilities
JOIN ability_upgrades au on au.ability_id = abilities.id
JOIN matches_players_details mpd on au.match_player_detail_id = mpd.id
JOIN heroes on heroes.id = mpd.hero_id
JOIN matches on matches.id = mpd.match_id
WHERE abilities.id = """+ability_id+"""
GROUP BY heroes.id, hero_localized_name, ability_name, winner, bucket
ORDER BY hero_id, winner DESC, COUNT DESC

TOWER_KILLS:

SELECT * FROM (
SELECT DISTINCT ON (hero_id) hero_id AS hero_id, hero_localized_name AS hero_name, streak FROM (
SELECT hero_id, hero_localized_name, ROW_NUMBER() OVER (PARTITION BY difference, hero_localized_name, match_id ORDER BY match_id,time) streak FROM(
SELECT ROW_NUMBER() OVER (PARTITION BY match_id ORDER BY match_id, time) roww,
	ROW_NUMBER() OVER (PARTITION BY hero_id, match_id ORDER BY match_id, time) heroo,
	(ROW_NUMBER() OVER (PARTITION BY match_id ORDER BY match_id, time) - ROW_NUMBER() OVER (PARTITION by hero_id ORDER BY match_id, time))difference,
* FROM (
SELECT matches.id AS match_id, heroes.id AS hero_id, heroes.localized_name AS hero_localized_name, time
FROM game_objectives game_o
JOIN matches_players_details mpd ON mpd.id = game_o.match_player_detail_id_1
JOIN matches ON matches.id = mpd.match_id
JOIN heroes ON mpd.hero_id = heroes.id 
WHERE subtype = 'CHAT_MESSAGE_TOWER_KILL' AND match_player_detail_id_1 IS NOT null
ORDER BY match_id, time ASC) tower_kill )musi
ORDER BY match_id, time ASC ) musi
ORDER BY hero_id, streak DESC)musi
ORDER BY streak DESC, hero_name ASC