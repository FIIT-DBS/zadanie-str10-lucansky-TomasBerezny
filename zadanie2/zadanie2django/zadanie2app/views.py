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
