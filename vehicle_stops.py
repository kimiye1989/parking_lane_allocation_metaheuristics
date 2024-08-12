import csv
from random import random, randrange
from xml.dom.minidom import Node
from xml.dom.minidom import parse

pas = {}

def hash_individual(individual):
    return str(hash(tuple(individual)))

def load_parking_areas():
    doc = parse('meta_parking-areas.xml')
    for i, pa in enumerate(doc.getElementsByTagName('parkingArea')):
        id = pa.getAttribute('id')
        pas[id] = i


def remove_stops(parking_areas):
    doc = parse('meta_stops.rou.xml')
    vehicles = doc.getElementsByTagName('vehicle')
    for i in range(len(vehicles)):
        vehicle = vehicles[i]

        # add stop for enabled parking areas
        stops = vehicle.getElementsByTagName('stop')
        if len(stops) > 0:
            stop = stops[0]
            pa = stop.getAttribute('parkingArea')
            index = pas[pa]
            if not parking_areas[index]:
                vehicle.removeChild(stop)

    remove_blanks(doc)
    doc.normalize()
    h = hash_individual(parking_areas)
    doc.writexml(open(f'routes/meta_stops{h}.rou.xml', 'w'), addindent='\t', newl='\n')

def remove_blanks(node):
    for x in node.childNodes:
        if x.nodeType == Node.TEXT_NODE:
            if x.nodeValue:
                x.nodeValue = x.nodeValue.strip()
        elif x.nodeType == Node.ELEMENT_NODE:
            remove_blanks(x)

def add_stops():
    STOPS_PER_EDGE = 25
    STOP_DURATION = str(30 * 60)
    enabled_edges = set()
    with open('meta_stops.csv', newline='') as csvfile:
        csvreader = csv.reader(csvfile, delimiter=',')
        for edge, enabled in csvreader:
            if enabled == '1':
                enabled_edges.add(edge)

    doc = parse('meta.rou.xml')
    vehicles = doc.getElementsByTagName('vehicle')
    n_stops = len(enabled_edges) * STOPS_PER_EDGE
    p_stop = n_stops / len(vehicles) * 0.5
    stop_counts = {edge: 0 for edge in enabled_edges}
    for vehicle in vehicles:
        if random() >= p_stop:
            continue

        # add stop for enabled parking areas
        route = vehicle.getElementsByTagName('route')[0]
        edges = list(filter(lambda edge: edge in enabled_edges, route.getAttribute('edges').split(' ')))
        if len(edges) == 0: continue
        i = randrange(len(edges))
        edge = edges[i]
        if stop_counts[edge] >= STOPS_PER_EDGE: continue

        # create stop element
        stop = doc.createElement('stop')
        stop.setAttribute('parkingArea', f'pa-{edge}')
        stop.setAttribute('duration', STOP_DURATION)
        vehicle.appendChild(stop)
        stop_counts[edge] += 1

    print(f'created {sum(stop_counts.values())} stops')
    edge, count = max(stop_counts.items(), key=lambda kv: kv[1])
    #print(f'max stops: {count} for edge {edge}')
    remove_blanks(doc)
    doc.normalize()
    doc.writexml(open('meta_stops.rou.xml', 'w'), addindent='\t', newl='\n')


def total_delay(h):
    doc = parse(f'trips/tripinfo{h}.xml')
    total = 0.0
    for tripinfo in doc.getElementsByTagName('tripinfo'):
        d = float(tripinfo.getAttribute('timeLoss'))
        total += d
    return total


if __name__ == '__main__':
    
    letters = [chr(ord('A') + i) for i in range(5)]
    numbers = [str(i) for i in range(5)]
    edges = []
    for i in range(5):
        l = letters[i]
        for j in range(5):
            n = numbers[j]
            ln = l + n    
            if i > 0:
                edges.append(letters[i - 1] + n + ln)
            if i < 4:
                edges.append(letters[i + 1] + n + ln)
            
            ns = []
            if j > 0:
                edges.append(l + numbers[j - 1] + ln)
            if j < 4:
                edges.append(l + numbers[j + 1] + ln)

    with open('meta_stops.csv', 'w', newline='') as csvfile:
        csvwriter = csv.writer(csvfile, delimiter=',')
        for edge in edges:
            csvwriter.writerow([edge, '1'])

    add_stops()
