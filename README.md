# Auckland Transit Tracker
A python tool for tracking the location of any public transit vehicle along with information about the vehicle.

This tool accesses the Auckland Transport "Realtime Compat" API to get GTFS (General Transit Feed Specification) information about public transport vehicles in Auckland and displays this information on a simple, easy-to-use GUI. This tool makes finding rare or special transit vehicles much easier as it gives the live location, route, trip ID, and much more about the vehicle.

![Overview of user interface](https://raw.githubusercontent.com/WilliamsRandomProjects/Auckland-Transit-Tracker/refs/heads/main/overview.PNG)

# Setup
Download and unzip the contents into a folder. Before you run it, you'll need:
- An API key from the Auckland Transport Developer Portal- Create an account for free on AT's developer portal, get an API key for the "Realtime Compat" API, and paste it into the config.ini file.
- Auckland Transport's GTFS files which can be downloaded from AT's website, though a copy of these (may be out of date) is already included. If you download, paste the txt files into the same folder as the python script.
Once you've got these files you can run the python script. If you're running through Visual Studio Code then you'll also need to enable the "Execute in File Dir" setting otherwise the program won't be able to find any of the files.

You can also pre-setup the list of transit vehicles you want to track. These should be in a comma-separated list without spaces and should be the "name" of the vehicle, e.g. RT1466 or AMP903

# Usage
Once you run the python script you'll see the GUI. If you've set up the list of vehicles to track then it'll update periodically and display vehicle information in the table at the top. Otherwise, you can set the list of vehicles through the "Edit Vehicles" option at the bottom- again, input a comma-separated list with no spaces.

By default, the vehicle data updates every 30 seconds (30000 milliseconds). If you want to change this, use the "Edit Refresh Rate" button. Auckland Transport allows for 35,000 API requests per week and 10 API requests per second, so if you leave the program running constantly then at minimum the refresh rate should be 20000 milliseconds, but you can go lower if you're only using the tracker for short periods of time.

Vehicles on the map are colour-coded: Red vehicles have no trip assigned (deadheading or non-AT charter services), orange vehicles have a trip assigned but the route couldn't be found (typically school bus services), and black vehicles are running regularly scheduled routes. Vehicles which aren't found won't be shown on the map and will display "Not Found" in the table.

If a vehicle has a valid route, you can click on its entry in the table which will highlight the vehicle and the route along with the stops will be shown on the map. This will take some time (typically a few seconds) to load and during this time you won't be able to interact with the interface- this is normal. If a vehicle doesn't have a valid route, you can still click on the vehicle's entry and the vehicle will still be highlighted. You can clear this by pressing the "clear selection" button.

If you want the tracker to update immediately (e.g. after making changes to the settings), you can use the "Force Update" button.

Speed on the data table is in km/h, occupancy goes from 0 (empty) to 5 (completely full)
![Vehicle selection and route display](https://raw.githubusercontent.com/WilliamsRandomProjects/Auckland-Transit-Tracker/refs/heads/main/routesel.PNG)

# Limitations and Problems
- School bus routes aren't included in the GTFS data, so you won't be able to see school routes displayed on the map.
- Be patient when clicking on a vehicle to see its route, as it's quite slow.
- When you initially select a vehicle, the route path and stops will be drawn over the top of vehicle icons- this will resolve itself when the map updates.
- Occasionally, the map will fail to clear vehicle markers and stop markers, leaving a ghost image on the map. You'll need to close and reopen the tracker to reset it.
