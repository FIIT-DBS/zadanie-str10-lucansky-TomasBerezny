import json
from django import conf
from django.shortcuts import render
from django.http import HttpResponse, JsonResponse
from django.db import connection
import psycopg2
from decouple import config

# Create your views here.

print(config('USER_NAME'))
connection = psycopg2.connect(user=config('USER_NAME'),
                                  password=config('USER_PASSWORD'),
                                  host=config('DB_HOST'),
                                  port=config('DB_PORT'),
                                  database=config('DB_NAME'))

cursor = connection.cursor()

def say_hello(request):
    cursor.execute("SELECT VERSION()")
    response1 = cursor.fetchone()
    cursor.execute("SELECT pg_database_size('dota2')/1024/1024 as dota2_db_size")
    response2 = cursor.fetchone()

    responses = {}
    responses['version'] = response1[0]
    responses['dota2_db_size'] = response2[0]

    json = {}
    json['pgsql'] = responses

    return JsonResponse(json, safe = False)

def endpoint2(request):
    cursor.execute("""SELECT patch_version, 
patch_start_date, 
patch_end_date,
id as match_id,
cast((cast(duration as decimal(7,2))/60) as decimal(7,2)) as match_duration
FROM (SELECT name as patch_version, 
cast(extract(epoch from release_date) as integer) as patch_start_date,
cast(extract(epoch from LEAD(release_date) OVER(ORDER BY name)) as integer)as patch_end_date
FROM patches) as patches_new
LEFT JOIN matches on matches.start_time > patches_new.patch_start_date
and matches.start_time < patches_new.patch_end_date""")
    response = cursor.fetchall()

    json = {'patches': []}
    last_patch = response[0][0]

    i = 0
    for res in response:
        match = None
        if res[3] != None:
            match = {'match_id': res[3], 'match_duration': res[4]}
        patch = {'patch_version': res[0], 'patch_start_date': res[1], 'patch_end_date': res[2], 'matches': []}
        if match != None:
            patch['matches'].append(match)
        
        if len(json['patches']) == 0:
            json['patches'].append(patch)
        else:
            if json['patches'][len(json['patches'])-1]['patch_version'] == res[0]:
                if match != None:
                    json['patches'][len(json['patches'])-1]['matches'].append(match)
            else:
                json['patches'].append(patch)
        
        

    return JsonResponse(json, safe = False)


def endpoint1(request, player_id):
    cursor.execute("""SELECT
players.id as id,
COALESCE(players.nick, 'unknown') as player_nick,
heroes.localized_name as hero_localized_name,
CAST(CAST(matches.duration as DECIMAL)/60 as DECIMAL(7,2)) as match_duration_minutes,
(xp_hero+xp_creep+COALESCE(xp_other,0)+COALESCE(xp_roshan,0)) as experience_gained,
mpd.level as level_gained,
CASE
WHEN player_slot < 5 and radiant_win = True THEN True
WHEN player_slot > 127 and radiant_win = False THEN True
ELSE False
END as winner,
matches.id as match_id
FROM players
INNER JOIN matches_players_details as mpd on players.id = mpd.player_id
INNER JOIN matches on mpd.match_id = matches.id
INNER JOIN heroes on mpd.hero_id = heroes.id
WHERE players.id = """+player_id)
    response = cursor.fetchall()

    json = {}

    i = 0
    for res in response:
        player = {'id': res[0], 'player_nick': res[1], 'matches': []}
        match = {'hero_localized_name': res[2], 'match_duration_minutes': res[3], 'experience_gained': res[4], 'level_gained': res[5],
        'winner': res[6], 'match_id': res[7]}
        if match != None:
            player['matches'].append(match)
        
        if len(json) == 0:
            json = player
        else:
            if match != None:
                json['matches'].append(match)
        
        

    return JsonResponse(json, safe = False)


def purchases(request, match_id):
    cursor.execute("""SELECT * FROM
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
WHERE item_num <= 5""")
    response = cursor.fetchall()

    json = {'id': int(match_id), 'heroes': []}
    hero = {'id': "", 'name': "", 'top_purchases': []}

    i = 0
    for res in response:
        hero['id'] = res[0]
        hero['name'] = res[1]
        item = {'id': res[2], 'name': res[3], 'count': res[4]}

        hero['top_purchases'].append(item)
        i+=1
        if i==5:
            json['heroes'].append(hero)
            hero = {'id': "", 'name': "", 'top_purchases': []}
            i=0
    return JsonResponse(json, safe = False)


def ability_usage(request, ability_id):
    cursor.execute("""SELECT DISTINCT ON (hero_id, winner) heroes.id AS hero_id, 
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
ORDER BY hero_id, winner DESC, COUNT DESC""")
    response = cursor.fetchall()

    json = {'id': int(ability_id), 'name': '', 'heroes': []}
    hero_name = ""

    for res in response:
        hero = {'id': "", 'name': ""}
        json['name'] = res[3]
        prev_hero = hero_name
        hero['id'] = res[0]
        hero['name'] = res[2]
        hero_name = res[2]
        usage = {'bucket': res[4], 'count': res[5]}

        if prev_hero != res[2]:
            if res[1]==True:
                hero['usage_winners'] = usage
            else:
                hero['usage_loosers'] = usage
            json['heroes'].append(hero)
        else:
            if res[1]==True:
                json['heroes'][len(json['heroes'])-1]['usage_winners'] = usage
            else:
                json['heroes'][len(json['heroes'])-1]['usage_loosers'] = usage
            
    return JsonResponse(json, safe = False)


def tower_kills(request):
    cursor.execute("""SELECT * FROM (
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
ORDER BY streak DESC, hero_name ASC""")
    response = cursor.fetchall()

    json = {'heroes': []}

    for res in response:
        hero = {'id': res[0], 'name': res[1], 'tower_kills': res[2]}
        json['heroes'].append(hero)
            
    return JsonResponse(json, safe = False)