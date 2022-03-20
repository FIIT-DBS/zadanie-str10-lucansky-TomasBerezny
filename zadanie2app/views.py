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
