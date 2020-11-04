import googlemaps
from fuzzywuzzy import fuzz as match
import csv
import datetime

PATH = 'd:\\'

API_KEY = 'AIzaSyBwhYdDMmFq2ALquLVMom_LZuD591LacAc'

gmaps = googlemaps.Client(key=API_KEY)

with open(f'{PATH}locations.csv') as csv_file:
    reader = csv.reader(csv_file)
    locations = list(reader)[1:]

with open(f'{PATH}telfords.csv') as csv_file:
    reader = csv.reader(csv_file)
    data = list(reader)[2:]
    
jobs = []
driver_jobs = {}

for idx, job in enumerate(data):
    if len(job) < 2 or job[0] == '' or job[1] == '': 
        continue
    
    clean_data = [elem.strip() for elem in job]
    driver, name, start_time, pup_time, pup, dest, arr_time, dep_time, back_time, *tmp = clean_data

    driver_job_list = driver_jobs.get(driver, [])
    driver_job_list.append(clean_data)
    driver_jobs[driver] = driver_job_list


def get_likely_location(name: str, threshold:int=95) -> (str, list, int, int):
    best_match = ''
    best_ratio = 0
    best_location = None

    for location in locations:
        ratio = match.ratio(name, location[0])
        #partial = match.partial_ratio(name, location[0])
        if ratio > best_ratio:
            best_ratio = ratio
            best_match = location[0]
            best_location = location

    if best_ratio >= threshold:
        return best_match, best_location, best_ratio, 0
    
    return None, [], 0, 0

def get_location(name: str, threshold:int=95) -> (bool, [float, float], {}):
    # matched_name, location, confidence, interval = get_likely_location(name, threshold)
    # if confidence:
    #     return True, location[9:11], location

    place = gmaps.find_place(input_type='textquery', input=[name], fields=['name', 'formatted_address', 'geometry/location'], location_bias='rectangle:140.77,-37.86|154.13,-28.1')
    if place['status'] == 'ZERO_RESULTS':
        return False, (None, None), None

    candidate = place['candidates'][0]
    return True, (candidate['geometry']['location']['lat'], candidate['geometry']['location']['lat']), candidate


def get_driving_time(pickup, dest, time):
    directions_result = gmaps.directions(', '.join(pickup), ', '.join(dest), mode="driving", avoid="ferries", departure_time=time)
    print(directions_result)

for driver, jobs in driver_jobs.items():
    for job in jobs:
        pup = job[-4:][:2]
        dest = job[-4:][2:]
        #print(pup, dest)
        get_driving_time(pup, dest, datetime.datetime.now())
     





    






