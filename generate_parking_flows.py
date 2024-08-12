import re
from xml.dom.minidom import parse, getDOMImplementation, getDOMImplementation
import itertools
from random import randrange
import pandas as pd



net = parse('meta.net.xml')
edges = net.getElementsByTagName('edge')
regex = re.compile('[A-E][0-4][A-E][0-4]')

doc = getDOMImplementation().createDocument(None, 'additional', None)
root = doc.documentElement
for edge in edges:
    edge_id = edge.getAttribute('id')
    if regex.match(edge_id):
        pa = doc.createElement('parkingArea')
        pa.setAttribute('id', f'pa-{edge_id}')
        pa.setAttribute('lane', f'{edge_id}_0')
        pa.setAttribute('startPos', '25')
        pa.setAttribute('endPos', '220')
        pa.setAttribute('onRoad', 'true')
        pa.setAttribute('roadsideCapacity', '25')
        root.appendChild(pa)
doc.writexml(open('meta_parking-areas.xml', 'w'), addindent='\t', newl='\n')

doc2 = getDOMImplementation().createDocument(None, 'routes', None)
root2 = doc2.documentElement
root2.setAttributeNS("http://www.w3.org/2000/xmlns/", "xmlns:xsi", "http://www.w3.org/2001/XMLSchema-instance")
root2.setAttributeNS("http://www.w3.org/2001/XMLSchema-instance", "xsi:noNamespaceSchemaLocation", "http://sumo.dlr.de/xsd/routes_file.xsd")

def map_junction(label, index):
    col = row = None
    if label == 'top' or label == 'bottom':col = chr(ord('A') + index)
    else:row = str(index)

    if label == 'top':row = '4'
    elif label == 'bottom':row = '0'
    elif label == 'left':col = 'A'
    else:col = 'E'
    return col + row

f = pd.read_csv('input.csv', sep=',',header=None)
MaxFlow = int(f.iloc[0,1])

labels = ['top', 'bottom', 'left', 'right']
sources = itertools.product(labels, range(5))
all_vehi = 0

for source_label, source_index in sources:
    source = source_label + str(source_index) + map_junction(source_label, source_index)
    sink_labels = labels.copy()
    sink_labels.remove(source_label)
    sinks = itertools.product(sink_labels, range(5))
    for sink_label, sink_index in sinks:
        sink = map_junction(sink_label, sink_index) + sink_label + str(sink_index)
        flow = doc2.createElement('flow')
        flow.setAttribute('id', f'{source}-{sink}')
        flow.setAttribute('from', source)
        flow.setAttribute('to', sink)
        flow.setAttribute('begin', '0')
        flow.setAttribute('end', '3600')
        flow_rate = randrange(MaxFlow)
        all_vehi += flow_rate
        flow.setAttribute('number', str(flow_rate))
        root2.appendChild(flow)

doc2.writexml(open('meta.flows.xml', 'w'), addindent='\t', newl='\n')