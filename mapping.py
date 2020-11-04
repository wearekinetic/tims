import datetime

import utils
import settings
import realtime
from exceptions import GeocodingException

import googlemaps

ONE_DAY = 86400 # in seconds

gmaps = googlemaps.Client(key=settings.API_KEY)


class Location:
    def __init__(self, place, time, gps):
        self.place = place
        self.time = time
        self.gps = gps

        self.inbound_leg = None
        self.outbound_leg = None

    def __eq__(self, other):
        return self.place == other.place


class GPS:    
    def __init__(self, latitude, longitude):
        self.latitude = latitude
        self.longitude = longitude

    def __str__(self):
        return f'{self.latitude}, {self.longitude}'

    def gmap(self):
        return str(self) 


def depot(time):
    return Location('Depot', time, GPS(*settings.DEPOT_GPS))


@utils.error(GeocodingException)
def driving_time(start: Location, end: Location):
    tomorrow = datetime.date.today() + datetime.timedelta(seconds=ONE_DAY)
    departure_time = datetime.datetime.combine(tomorrow, start.time.to_datetime().time())
    try:
        directions_result = gmaps.directions(start.gps.gmap(), end.gps.gmap(), mode="driving", avoid="ferries", departure_time=departure_time)
    except googlemaps.exceptions.ApiError:
        raise GeocodingException(f'Unable to find route between {start.place} and {end.place}')
    if not directions_result:
        raise GeocodingException(f'Unable to find route between {start.place} and {end.place}')
    
    return realtime.Time(directions_result[0]['legs'][0]['duration']['value'])


