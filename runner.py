import os
import sys

# we need to import python modules from the $SUMO_HOME/tools directory
if 'SUMO_HOME' in os.environ:
    tools = os.path.join(os.environ['SUMO_HOME'], 'tools')
    sys.path.append(tools)
else:
    
    PYTHONPATH="$SUMO_HOME/toolsos.environ['SUMO_HOME'] = '/usr/local/opt/sumo/share/sumo':$PYTHONPATH"
    #sys.exit("please declare environment variable 'SUMO_HOME'")
    
from sumolib import checkBinary  # noqa
import traci  # noqa

def start(h):
    # Link to and use TraCI
    # this is the normal way of using traci. sumo is started as a
    # subprocess and then the python script connects and runs
    sumoBinary = checkBinary('sumo')
    traci.start([sumoBinary, '-n', 'meta.net.xml', '-a', 'meta_parking-areas.xml', '-r', f'routes/meta_stops{h}.rou.xml', '--tripinfo-output', f'trips/tripinfo{h}.xml'])

    step = 0
    while traci.simulation.getMinExpectedNumber() > 0:
        traci.simulationStep()
        step += 1
    traci.close()
    sys.stdout.flush()
