# coding: utf-8

"""Database controller for the Web Flask API
"""


import daiquiri
import logging

from itertools import groupby
from datetime import timedelta

from jitenshea import config
from jitenshea.iodb import db


daiquiri.setup(level=logging.INFO)
logger = daiquiri.getLogger(__name__)

CITIES = ('bordeaux',
          'lyon')


def cities():
    "List of cities"
    # Lyon
    # select count(*) from lyon.pvostationvelov;
    # Bdx
    # select count(*) from bordeaux.vcub_station;
    return [{'city': 'lyon',
             'country': 'france',
             'stations': 348},
            {'city': 'bordeaux',
             'country': 'france',
             'stations': 174}]

def stations(city, limit):
    """List of bicycle stations

    city: string
    limit: int

    Return a list of dict, one dict by bicycle station
    """
    if city == 'bordeaux':
        query = bordeaux_stations(limit)
    elif city == 'lyon':
        query = lyon_stations(limit)
    else:
        raise ValueError("City {} not supported".format(city))
    eng = db()
    rset = eng.execute(query)
    keys = rset.keys()
    return [dict(zip(keys, row)) for row in rset]

def bordeaux_stations(limit=20):
    """Query for the list of bicycle stations in Bordeaux

    limit: int
       default 20

    Return a SQL query to execute
    """
    return """SELECT numstat::int AS id
      ,nom AS name
      ,adresse AS address
      ,commune AS city
      ,nbsuppor::int AS nb_bikes
    FROM {schema}.vcub_station
    LIMIT {limit}
    """.format(schema=config['bordeaux']['schema'],
               limit=limit)

def lyon_stations(limit=20):
    """Query for the list of bicycle stations in Lyon

    limit: int
       default 20

    Return a SQL query to execute
    """
    return """SELECT idstation::int AS id
      ,nom AS name
      ,adresse1 AS address
      ,commune AS city
      ,nbbornette::int AS nb_bikes
    FROM {schema}.pvostationvelov
    LIMIT {limit}
    """.format(schema=config['lyon']['schema'],
               limit=limit)

def bordeaux(station_ids):
    """Get some specific bicycle-sharing stations for Bordeaux
    station_id: list of int
       Ids of the bicycle-sharing station

    Return bicycle stations in a list of dict
    """
    query = bordeaux_stations(1).replace("LIMIT 1", 'WHERE numstat IN %(id_list)s')
    eng = db()
    rset = eng.execute(query, id_list=tuple(str(x) for x in station_ids)).fetchall()
    if not rset:
        return []
    return [dict(zip(x.keys(), x)) for x in rset]

def lyon(station_ids):
    """Get some specific bicycle-sharing stations for Lyon
    station_id: list of ints
       Ids of the bicycle-sharing stations

    Return bicycle stations in a list of dict
    """
    query = lyon_stations(1).replace("LIMIT 1", 'WHERE idstation IN %(id_list)s')
    eng = db()
    rset = eng.execute(query, id_list=tuple(str(x) for x in station_ids)).fetchall()
    if not rset:
        return []
    return [dict(zip(x.keys(), x)) for x in rset]


def daily_query(city):
    """SQL query to get daily transactions according to the city
    """
    if city not in ('bordeaux', 'lyon'):
        raise ValueError("City '{}' not supported.".format(city))
    return """SELECT id
           ,number AS value
           ,date
        FROM {schema}.daily_transaction
        WHERE id IN %(id_list)s AND date >= %(start)s AND date <= %(stop)s
        ORDER BY id,date""".format(schema=config[city]['schema'])

    raise ValueError("City '{}' not supported.".format(city))


def daily_transaction(city, station_ids, day, window=0, backward=True):
    """Retrieve the daily transaction for the Bordeaux stations

    stations_ids: list of int
        List of ids station
    day: date
        Data for this specific date
    window: int (0 by default)
        Number of days to look around the specific date
    backward: bool (True by default)
        Get data before the date or not, according to the window number

    Return a list of dicts
    """
    stop = day
    sign = 1 if backward else -1
    start = stop - timedelta(sign * window)
    if not backward:
        start, stop = stop, start
    query = daily_query(city)
    eng = db()
    rset = eng.execute(query,
                       id_list=tuple(str(x) for x in station_ids),
                       start=start, stop=stop).fetchall()
    if not rset:
        return []
    data = [dict(zip(x.keys(), x)) for x in rset]
    if window == 0:
        return data
    # re-arrange the result set to get a list of values for the keys 'date' and 'value'
    values = []
    for k, group in groupby(data, lambda x: x['id']):
        group = list(group)
        values.append({'id': k,
                       "date": [x['date'] for x in group],
                       'value': [x['value'] for x in group]})
    return values

