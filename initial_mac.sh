rm *.xml
netgenerate --grid --grid.number=5 --grid.length=250 --grid.attach-length=250 -L 2 --output-file=meta.net.xml
# python C:\SUMO\tools\randomTrips.py -n meta.net.xml -o meta.trips.xml --period=0.20 --binomial=20

# Initialise parking areas & traffic flows/ vehicle_stops
python3 generate_parking_flows.py

duarouter -n meta.net.xml -r meta.flows.xml -o meta.rou.xml --no-warnings
python3 vehicle_stops.py