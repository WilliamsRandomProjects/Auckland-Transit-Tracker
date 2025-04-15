import requests
import time
import json
import csv
import os
import datetime
import sys
import configparser
import tkinter as tk
from PIL import Image, ImageTk
from tkinter import ttk, simpledialog, messagebox
import folium
from geopy.geocoders import Nominatim
from tkintermapview import TkinterMapView

# Load config
GTFS_FOLDER = os.getcwd()
CONFIG_FILE = os.path.join(GTFS_FOLDER, "config.ini")
config = configparser.ConfigParser()
config.read(CONFIG_FILE)

API_KEY = config.get("Settings", "API_KEY", fallback=None)
VEHICLE_NUMBERS = [v.strip() for v in config.get("Settings", "VEHICLES", fallback="").split(',')]
REFRESH_RATE = config.getint("Settings", "REFRESH_RATE", fallback=30000)  # Default 30s
BASE_URL = "https://api.at.govt.nz/realtime/legacy"

# Load GTFS data
routes = {}
trips = {}
shape_ids = {}
vehicle_markers = {}
stop_markers = []
current_shape = ""
selected_vehicle = ""
stop_positions = []
terminus_stop = (None,None)
after_id = None



def load_gtfs_data():
    global routes, trips
    try:
        with open(os.path.join(GTFS_FOLDER, "routes.txt"), newline='', encoding='utf-8') as csvfile:
            reader = csv.DictReader(csvfile)
            for row in reader:
                routes[row["route_id"]] = row["route_short_name"]
    except Exception as e:
        print("Error loading routes.txt:", e)
    
    try:
        with open(os.path.join(GTFS_FOLDER, "trips.txt"), newline='', encoding='utf-8') as csvfile:
            reader = csv.DictReader(csvfile)
            for row in reader:
                trips[row["trip_id"]] = row["trip_headsign"]
                shape_ids[row["trip_id"]] = row["shape_id"]
    except Exception as e:
        print("Error loading trips.txt:", e)

def get_all_vehicle_details():
    headers = {"Ocp-Apim-Subscription-Key": API_KEY}
    response = requests.get(f"{BASE_URL}/vehiclelocations", headers=headers)
    if response.status_code != 200:
        print("Error fetching data:", response.text)
        return []
    data = response.json()
    return data.get("response", {}).get("entity", [])

def monitor_vehicles():
    global tracked_vehicles
    load_gtfs_data()
    vehicle_numbers_set = set([v.replace(" ", "").strip() for v in VEHICLE_NUMBERS])
    vehicles = get_all_vehicle_details()
    tracked_vehicles = {v: {"Vehicle": v, "License Plate": "Not Found", "Latitude": "Not Found", "Longitude": "Not Found", "Bearing": "Not Found", "Speed": "Not Found", "Occupancy": "Not Found", "Route": "Not Found", "Trip": "Not Found"} for v in vehicle_numbers_set}
    
    for vehicle in vehicles:
        details = vehicle.get("vehicle", {})
        label = details.get("vehicle", {}).get("label", "").replace(" ", "").strip()
        if label in vehicle_numbers_set:
            tracked_vehicles[label] = {
                "Vehicle": label,
                "License Plate": details.get("vehicle", {}).get("license_plate", "Unknown"),
                "Latitude": details.get("position", {}).get("latitude", "Unknown"),
                "Longitude": details.get("position", {}).get("longitude", "Unknown"),
                "Bearing": details.get("position", {}).get("bearing", "Unknown"),
                "Speed": details.get("position", {}).get("speed", "Unknown"),
                "Occupancy": details.get("occupancy_status", "Unknown"),
                "Route": routes.get(details.get("trip", {}).get("route_id", "Unknown"), "Unknown"),
                "Route ID": details.get("trip", {}).get("route_id", "Unknown"),
                "Trip": trips.get(details.get("trip", {}).get("trip_id", "Unknown"), "Unknown"),
                "Trip ID": details.get("trip", {}).get("trip_id", "Unknown")
            }
    tracked_sorted = dict(sorted(tracked_vehicles.items()))
    return list(tracked_sorted.values())

def update_table():
    global vehicle_data
    global after_id
    if after_id:
        root.after_cancel(after_id)
    try:
        vehicle_data = monitor_vehicles()
        for row in table.get_children():
            table.delete(row)
        for vehicle in vehicle_data:
            values = [vehicle.get(col, "Not Found") for col in columns]
            table.insert("", "end", values=values)
        last_updated_label.config(text=f"Last Updated: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        update_map(vehicle_data)
    except Exception as e:
        print("Failed to get vehicle data: ", e )
        messagebox.showinfo("Failed to get vehicles", f"Could not get vehicle data due to: {e} \n Check your connection or API key")
    after_id = root.after(REFRESH_RATE, update_table)  # Refresh at configured interval

def update_map(vehicle_data):
    global vehicle_markers
    global selected_vehicle
    global terminus_stop
    global stop_positions
    global stop_markers
    map_widget.delete_all_marker()
    stop_markers = []
    if terminus_stop != (None,None) and stop_positions != []:
        for coord in stop_positions:
            marker = map_widget.set_marker(coord[0], coord[1], icon = stop_icon)
            stop_markers.append(marker)
        stop_markers.append(map_widget.set_marker(terminus_stop[0], terminus_stop[1], icon = terminal_icon))
    vehicle_markers = {}
    for vehicle in vehicle_data:
        if vehicle["Latitude"] != "Not Found" and vehicle["Longitude"] != "Not Found":
            if vehicle["Vehicle"] == selected_vehicle or selected_vehicle == "":
                if vehicle["Trip ID"] == "Unknown": # No Trip ID -> Unassigned vehicle or non-AT route
                    pin_colour = "red"
                elif vehicle["Route"] == "Unknown": # No Route ID but yes Trip ID -> non-regular schedule route
                    pin_colour = "orange"
                else:
                    pin_colour = "black"
                vehicle_markers[vehicle["Vehicle"]] = map_widget.set_marker(vehicle["Latitude"], vehicle["Longitude"], text=vehicle["Vehicle"], icon=vehicle_icon, text_color = pin_colour)
            else:
                vehicle_markers[vehicle["Vehicle"]] = map_widget.set_marker(vehicle["Latitude"], vehicle["Longitude"], text=vehicle["Vehicle"], icon=small_vehicle_icon, text_color = "grey")

def edit_vehicle_list():
    global VEHICLE_NUMBERS
    new_vehicles = simpledialog.askstring("Edit Vehicles", "Enter vehicle numbers separated by commas:", initialvalue=",".join(VEHICLE_NUMBERS))
    if new_vehicles is not None:
        VEHICLE_NUMBERS = [v.strip() for v in new_vehicles.split(',')]
        config.set("Settings", "VEHICLES", new_vehicles)
        with open(CONFIG_FILE, "w") as configfile:
            config.write(configfile)
        messagebox.showinfo("Success", "Vehicle list updated. Changes will be reflected in the next update.")

def edit_refresh_rate():
    global REFRESH_RATE
    new_rate = simpledialog.askinteger("Edit Refresh Rate", "Enter refresh rate in milliseconds:", initialvalue=REFRESH_RATE)
    if new_rate is not None:
        REFRESH_RATE = new_rate
        config.set("Settings", "REFRESH_RATE", str(new_rate))
        with open(CONFIG_FILE, "w") as configfile:
            config.write(configfile)
        messagebox.showinfo("Success", "Refresh rate updated. Changes will take effect immediately.")

def on_table_click(event):
    global current_shape
    global vehicle_markers
    global selected_vehicle
    global vehicle_data
    global stop_markers
    global terminus_stop
    global stop_positions
    global loading_message
    global loading_text
    selected_item = table.selection()
    if selected_item:
        table_vehicle_data = table.item(selected_item, "values")
        vehicle_name = table_vehicle_data[0]
        selected_vehicle = vehicle_name
        if vehicle_name != "Unknown" and vehicle_name != "Not Found":
            update_map(vehicle_data)

        try:
            vehicle_shape = shape_ids[tracked_vehicles[vehicle_name]["Trip ID"]]
        except Exception as e:
            map_widget.delete_all_path()
            for marker in stop_markers:
                marker.delete()
            messagebox.showinfo("No assigned path", "Vehicle does not have a valid path.")
            return
        if vehicle_shape != current_shape:
            map_widget.delete_all_path()
            current_shape = vehicle_shape
            poslist = []
            stop_ids = {}
            terminus_id = ""
            terminus_stop = (0,0)
            stop_positions = []
            try:

                loading_text.set("Please Wait... Loading Route Shape")
                block_input(1)
                root.update()
                with open(os.path.join(GTFS_FOLDER, "shapes.txt"), newline='', encoding='utf-8') as csvfile:
                    reader = csv.DictReader(csvfile)
                    for row in reader:
                        if row["shape_id"] == vehicle_shape:
                            if len(poslist) < int(row["shape_pt_sequence"]):
                                poslist.extend( [""]*( int(row["shape_pt_sequence"]) - len(poslist) -1 ) )
                            poslist.insert(int(row["shape_pt_sequence"])-1, ( float(row["shape_pt_lat"]), float(row["shape_pt_lon"]) ) )
                loading_text.set("Please Wait... Loading Route Stops")
                root.update()
                with open(os.path.join(GTFS_FOLDER, "stop_times.txt"), newline='', encoding='utf-8') as csvfile:
                    reader = csv.DictReader(csvfile)
                    for row in reader:
                        if row["trip_id"] == tracked_vehicles[vehicle_name]["Trip ID"]:
                            stop_ids[int(row["stop_sequence"])] = row["stop_id"]
                terminus_id = stop_ids[max(stop_ids.keys())]

                loading_text.set("Please Wait... Loading Stop Positions")
                root.update()
                with open(os.path.join(GTFS_FOLDER, "stops.txt"), newline='', encoding='utf-8') as csvfile:
                    reader = csv.DictReader(csvfile)
                    for row in reader:
                        if row["stop_id"] == terminus_id:
                            terminus_stop = (float(row["stop_lat"]), float(row["stop_lon"]))
                        elif row["stop_id"] in stop_ids.values():
                            stop_positions.append((float(row["stop_lat"]), float(row["stop_lon"])))
                loading_text.set("Please Wait... Placing Stops")
                root.update()
                for marker in stop_markers:
                    marker.delete()
                for coord in stop_positions:
                    marker = map_widget.set_marker(coord[0], coord[1], icon = stop_icon)
                    stop_markers.append(marker)
                stop_markers.append(map_widget.set_marker(terminus_stop[0], terminus_stop[1], icon = terminal_icon))
                loading_text.set("")
                root.update()
                block_input(0)


            except Exception as e:
                block_input(0)
                loading_text.set("")
                root.update()
                print("Error creating map path: ", e)
            map_path = map_widget.set_path(tuple(poslist))
            
        
    else:
        clear_selection()

def clear_selection():
    global selected_vehicle
    global stop_markers
    global terminus_stop
    global stop_positions
    global current_shape
    table.selection_set(())   
    map_widget.delete_all_path()
    for marker in stop_markers:
        marker.delete()
    stop_positions = []
    terminus_stop = (None,None)
    current_shape = ""
    selected_vehicle = ""
    update_map(vehicle_data) 

def block_input(state):
    if state == 0:
        overlay.place_forget()
    if state == 1:
        overlay.place(relx=0,rely=0,relwidth=1,relheight=1)

# GUI setup
root = tk.Tk()
root.title("Auckland Transport Vehicle Tracker")

columns = ["Vehicle", "License Plate", "Latitude", "Longitude", "Bearing", "Speed", "Occupancy", "Route", "Route ID", "Trip", "Trip ID"]
table = ttk.Treeview(root, columns=columns, show="headings")
column_widths = {"Vehicle": 80, "License Plate": 100, "Latitude": 80, "Longitude": 80, "Bearing": 80, "Speed": 80, "Occupancy": 100, "Route": 100, "Route ID":100, "Trip": 400, "Trip ID": 200}
for col in columns:
    table.heading(col, text=col)
    table.column(col, width=column_widths.get(col, 100))

table.bind("<ButtonRelease-1>", on_table_click)
table.pack(fill="both", expand=True)

deselect_button = tk.Button(root, text = "Clear Selection", command=clear_selection)
deselect_button.pack()
update_button = tk.Button(root, text = "Force update", command = update_table)
update_button.pack()
loading_text = tk.StringVar()
loading_text.set("")
loading_message = tk.Label(root,textvariable = loading_text)
loading_message.pack()

map_widget = TkinterMapView(root, width=1200, height=600)
map_widget.set_position(-36.8441353, 174.7679576)  # Paris, France
map_widget.set_zoom(11)
map_widget.pack()

last_updated_label = tk.Label(root, text="Last Updated: --", font=("Arial", 10))
last_updated_label.pack()

frame = tk.Frame(root)
frame.pack()

edit_button = tk.Button(frame, text="Edit Vehicles", command=edit_vehicle_list)
edit_button.pack(side=tk.LEFT)

refresh_button = tk.Button(frame, text="Edit Refresh Rate", command=edit_refresh_rate)
refresh_button.pack(side=tk.LEFT)

vehicle_icon = ImageTk.PhotoImage(Image.open(os.path.join(GTFS_FOLDER, "vehicle.png")))
small_vehicle_icon = ImageTk.PhotoImage(Image.open(os.path.join(GTFS_FOLDER, "small vehicle.png")))
stop_icon = ImageTk.PhotoImage(Image.open(os.path.join(GTFS_FOLDER, "small_stop.png")))
terminal_icon = ImageTk.PhotoImage(Image.open(os.path.join(GTFS_FOLDER, "last_stop.png")))

overlay = tk.Frame(root, bg="", width=1200, height=600)
overlay.place_forget()  # Start hidden

update_table()
root.mainloop()
