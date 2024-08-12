del *.xml
netgenerate --grid --grid.number=5 --grid.length=250 --grid.attach-length=250 -L 2 --output-file=meta.net.xml
:: python C:\SUMO\tools\randomTrips.py -n grid.net.xml -o grid.trips.xml --period=0.20 --binomial=20
python3 generate_parking_flows.py

:: duarouter -n grid.net.xml --additional-files grid.trips.xml -o grid.rou.xml
duarouter -n meta.net.xml -r meta.flows.xml -o meta.rou.xml --no-warnings
python3 vehicle_stops.py
:: sumo -n grid.net.xml -a parking-areas.xml -r grid-stops.rou.xml --tripinfo-output tripinfo.xml