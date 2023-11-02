from django.shortcuts import render
from django.http import HttpResponse
from backendCode.geocoding import reverse_geocoding, geocoding_from_address
from backendCode.nearbyplaces import search_nearby_places
from home_page.models import BusInformation,Map
from backendCode.findBusByDirection import find_distance
from decouple import config
import random
import time
import math
# Create your views here.


def searchnearby_address(request):
    location = request.POST['userlocationaddress']
    print(location)
    text = 'AIzaSyAjtcM486PgopQgphrdHOHZlrLCeI2KQz8'
    url = f"https://maps.googleapis.com/maps/api/js?key=AIzaSyAjtcM486PgopQgphrdHOHZlrLCeI2KQz8&callback=initMap&libraries=&v=weekly"
    data = geocoding_from_address(location)
    nearby_list = search_nearby_places(data['lat'], data['lng'])
    data.update({'nearlist': nearby_list})
    data.update({'text': url})
    return render(request, 'smartTracking/searchnearby.html', data)


def searchnearby_latlng(request):
    location = str(request.POST['userLocation'])
    lat, lng = location.split(sep=',', maxsplit=1)
    formatted_address = reverse_geocoding(location)
    nearby_list = search_nearby_places(lat=lat, lng=lng)
    text = 'AIzaSyAjtcM486PgopQgphrdHOHZlrLCeI2KQz8'
    url = f"https://maps.googleapis.com/maps/api/js?key=AIzaSyAjtcM486PgopQgphrdHOHZlrLCeI2KQz8&callback=initMap&libraries=&v=weekly"
    data = {
        'formatted_address': formatted_address,
        'nearlist': nearby_list,
        'text': url

    }
    # print(location)
    return render(request, 'smartTracking/searchnearby.html', data)

def distanceCalculating(point1,point2):
    R = 6373.0
    
    lat1 = math.radians(float(point1.split(sep=',')[0]))
    lon1 = math.radians(float(point1.split(sep=',')[1]))
    lat2 = math.radians(float(point2.split(sep=',')[0]))
    lon2 = math.radians(float(point2.split(sep=',')[1]))

    dlon = lon2 - lon1
    dlat = lat2 - lat1
    a = math.sin(dlat / 2)**2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon / 2)**2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    distance = R * c
    return distance

def finddirection(request):
    bus_list = []
    start = str(request.POST['from']).strip()
    end = str(request.POST['to']).strip()
    #print('start : ',start)
    #print('end : ',end)
    #try:
    buses = BusInformation.objects.filter(bus_viaroad__contains=start).filter(bus_viaroad__contains=end)
    #print(buses)
    for bus in buses:
        bus_id = bus.bus_id
        bus_id = "bus" + str(bus_id)
        bus_name = bus.bus_name
        bus_raw_route = bus.route_id.routes
        bus_raw_route = bus_raw_route.split(sep=',')
        #print('Bus raw route : ',bus_raw_route)
        #print('Bus id : ',bus.bus_id)
        route_coordinates = Map.objects.filter(bus_id=bus.bus_id)
        raw_coordinates = []
        for route in route_coordinates:
            points = route.way_points.split(sep='|')
           # print(route.way_points.split(sep='|'))
        for point in points:
            raw_coordinates.append(point[4:])
        #print('coordinates before slice',raw_coordinates)
        #print('leng bus_raw_route rout',len(bus_raw_route))
        #print('coordinates bus_raw_route leng',len(raw_coordinates)) 
        
        start_index = -1
        end_index  = -1
        for i in range(0, len(bus_raw_route)):
            if start.lower() in bus_raw_route[i].lower():
                start_index = i
            if end.lower() in bus_raw_route[i].lower():
                end_index = i
        
        #print('Start_index' + str(start_index))
        #print('End_index' + str(end_index))
        bus_route = []
        coordinates = []
        if(start_index != -1 and end_index != -1):
            coordinates.clear()
            #print('inside main if')
            if start_index <= end_index:
                #print('print if')
                for i in range(start_index, end_index+1):
                 #   print('Bus raw route',bus_raw_route[i])
                    bus_route.append(bus_raw_route[i])
                    coordinates.append(raw_coordinates[i])
                
            else:
                #print('print else')
                for i in range(start_index,end_index-1,-1):
                 #   print('Bus raw route',bus_raw_route[i])
                    bus_route.append(bus_raw_route[i])
                    coordinates.append(raw_coordinates[i])
                
        #print('coordinates after slice',coordinates)
        #print('leng bus rout',len(bus_route))
        #print('coordinates leng',len(coordinates)) 
        #distance = find_distance(bus_route)
            
        stop1 = time.time() + 300
        stop2 = stop1 + random.randrange(60,300)
        distance = 0.0
        list_route=[]
        distance = [0]
        d = 0.0
        for i in range(0, len(coordinates)-1):
            d += distanceCalculating(coordinates[i],coordinates[i+1])
            distance.append(round(d,2))
        final_distance = 0.0
        for i in range(0, len(bus_route), 2):
            if i + 1 == len(bus_route):
                d = distanceCalculating(coordinates[i],coordinates[i])
                final_distance += d
                temp = (bus_route[i], None,distance[i],distance[i],time.strftime("%H:%M:%S",time.strptime(time.ctime(stop1))),time.strftime("%H:%M:%S",time.strptime(time.ctime(stop2))))
            else:
                final_distance += d
                temp = (bus_route[i], bus_route[i + 1],distance[i],distance[i+1],time.strftime("%H:%M:%S",time.strptime(time.ctime(stop1))),time.strftime("%H:%M:%S",time.strptime(time.ctime(stop2))))
            list_route.append(temp)
            stop1 = stop2 + random.randrange(60,300)
            stop2 = stop1 + random.randrange(60,300)
        data = {
            'bus_id': bus_id,
            'bus_name': bus_name,
            'bus_route': list_route,
            'distance': round(final_distance,2),
            
        }
    
        print('List route ',list_route)
        bus_list.append(data)
        length = len(bus_list)
        print(bus_list)
    contex = {
        'From': start,
        'To': end,
        'Number_of_bus': len(bus_list),
        'bus_list': bus_list,
    }
    return render(request, 'smartTracking/finddirection.html', contex)
    '''except:
    #print("In except")
        contex = {
            'check': 1,
            'From': start,
            'To': end,
            'Number_of_bus': 0
        }
        return render(request, 'smartTracking/finddirection.html', contex)'''


def findspecificbus(request):
    bus_name_from_user = str(request.POST['bus_name'])
    try:
        buses = BusInformation.objects.filter(bus_name__iexact=bus_name_from_user)
        bus = buses[0]
        ssource_destination = str(bus.bus_sourcetodestination)
        start, end = ssource_destination.split(sep='-', maxsplit=1)
        routes = bus.route_id.routes
        routes = routes.split(sep=',')
        list_route = []
        for i in range(0, len(routes), 2):
            if i + 1 == len(routes):
                temp = (routes[i], None)
            else:
                temp = (routes[i], routes[i + 1])
            list_route.append(temp)
        data = {
            'check': 0,
            'bus_id': bus.bus_id,
            'bus_name': bus.bus_name,
            'start': start,
            'end': end,
            'routes': list_route
        }
        return render(request, 'smartTracking/findspecificbus.html', data)

    except:
        data = {
            'check': 1,
            "error": bus_name_from_user
        }
        return render(request, 'smartTracking/findspecificbus.html', data)

        # ssource_destination = str(bus.bus_sourcetodestination)
        # start, end = ssource_destination.split(sep='-', maxsplit=1)
        # routes = bus.route_id.routes
        # routes = routes.split(sep=',')
        # list_route = []
        # for i in range(0, len(routes), 2):
        #     if i + 1 == len(routes):
        #         temp = (routes[i], None)
        #     else:
        #         temp = (routes[i], routes[i + 1])
        #     list_route.append(temp)
        # data = {
        #     'check': 0,
        #     'bus_id': bus.bus_id,
        #     'bus_name': bus.bus_name,
        #     'start': start,
        #     'end': end,
        #     'routes': list_route
        # }
        # return render(request, 'smartTracking/findspecificbus.html', data)


def allbuses(request):
    buses = BusInformation.objects.all()
    buses_list = []
    for bus in buses:
        ssource_destination = str(bus.bus_sourcetodestination)
        start, end = ssource_destination.split(sep='-', maxsplit=1)
        routes = bus.route_id.routes
        routes = routes.split(sep=',')
        design = str(routes[0])
        for r in range(1, len(routes) - 1):
            design = design + '<->' + str(routes[r])
        data = {
            'bus_id': bus.bus_id,
            'bus_name': bus.bus_name,
            'start': start,
            'end': end,
            'routes': design
        }
        buses_list.append(data)
    contex = {
        'contex': buses_list
    }
    # print(routes)
    return render(request, 'smartTracking/allbuses.html', contex)

# urls of smarttracking apps
# {% url 'searchnearby'%}
# {% url 'finddirection'%}
# {% url 'findspecificbus'%}
# {% url 'allbuses'%}
