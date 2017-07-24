# coding: utf-8

"""Database controller for the Web Flask API
"""


import daiquiri
import logging

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

def stations(city):
    """List of stations as dict
    """
    if city == 'bordeaux':
        query = bordeaux_stations()
    elif city == 'lyon':
        query = lyon_stations()
    else:
        raise ValueError("City {} not supported".format(city))
    eng = db()
    rset = eng.execute(query)
    keys = rset.keys()
    return [dict(zip(keys, row)) for row in rset]

def bordeaux_stations():
    return """SELECT numstat::int AS id
      ,nom AS name
      ,adresse AS address
      ,commune AS city
      ,nbsuppor::int AS nb_bikes
    FROM {schema}.vcub_station
    """.format(schema=config['bordeaux']['schema'])

def lyon_stations():
    return """SELECT idstation::int AS id
      ,nom AS name
      ,adresse1 AS address
      ,commune AS city
      ,nbbornette::int AS nb_bikes
    FROM {schema}.pvostationvelov
    """.format(schema=config['lyon']['schema'])
