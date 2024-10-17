import os
import json
import logging
import myutils

# import arcpy

import azure.functions as func

from arcgis.gis import GIS, Item
from arcgis.features import FeatureLayerCollection, FeatureLayer
from arcgis.geocoding import reverse_geocode
from arcgis.mapping import WebMap


#For this I hard coded it so it has the username and password and links atlas website
PORTAL_URL = "https://atlas.metriceng.com/portal"#os.getenv("ARCGIS_PORTAL_URL")
PORTAL_USR = "adms-app-sa"#os.getenv("ARCGIS_PORTAL_SA_USR")
PORTAL_PWD = "cjh24Esx.rug"#os.getenv("ARCGIS_PORTAL_SA_PWD")
ENV_SIG = "DEV"#os.getenv("ADMS_ENV_SIG")

app = func.FunctionApp()


#Finding the key in the message
#This had to be made to find the key inside the locally stored dictionary
def find_key(nested_dict, target_key):
    """
    Recursively search for a key in a nested dictionary.
    
    :param nested_dict: The dictionary to search.
    :param target_key: The key to find.
    :return: The value of the found key, or None if the key is not found.
    """
    if target_key in nested_dict:
        return nested_dict[target_key]

    for key, value in nested_dict.items():
        if isinstance(value, dict):  # If value is a nested dictionary, search recursively
            found = find_key(value, target_key)
            if found is not None:
                return found
    return None

#This will parse through each file and create the dictionary
def load_json_files(file_path):
    #Try clause to try and open the file and see for any mistakes or whatever
    try: 
        with open(file_path, "r") as file:
            msg = json.load(file) #The dictionary is created
    except json.JSONDecodeError as e:
        logging.error(f"Failed to decode JSON file {file_path}: {e}")
    except Exception as e:
        logging.error(f"Error reading the file {file_path}: {e}")
    
    return msg
        
#To login into ArcGIS
def gis_login() -> GIS:
    try:
        gis = GIS(PORTAL_URL, PORTAL_USR, PORTAL_PWD)
        logging.info(f"Logged in as {gis.properties.user.username}")
        return gis
    except Exception as e:
        logging.error("Failed to login in to ArcGIS Portal: {0}".format(e))
        raise
    
#Process a certain key within the json files (dictionaries)
def process_message(msg: dict, search):
    """
    According to the original code there is only one main thing that is shared
    and that is the mission name
    Look at the function_app.py at the two functions
    """
    """
    Processes mission data or any ticket needed
    The dictionary loaded from the JSON file 
    THe processed mission feature service name 
    """
    hosting_env = "DEV"
    
    mission_name = find_key(msg, search)
    mission_fs_name = myutils.sanitize_fs_name(mission_name)
    mission_fs_name_full = myutils.get_unique_fs_name_per_env(mission_fs_name, hosting_env)

    return mission_fs_name_full

def process_searches(msg: dict, search):
    searched_item = find_key(msg, search)
    return searched_item


def construct_ticket_dict(msg_obj: dict) -> dict:
    """
    Constructs a ticket dictionary to be added to the feature layer
    The dictionary containing ticket information
    Dictionary formatted for ArcGIS feature layer addition
    """
    
    # Initialize lat and lng with default values
    lat, lng = 0.0, 0.0
        
    try:
        gps = find_key(msg_obj, "beginningGps")
        gps_coords = gps.split(",")  # Split the string by the comma
        lat = float(gps_coords[0].strip())  # First part is latitude
        lng = float(gps_coords[1].strip())  # Second part is longitude
        
    except (KeyError, ValueError, IndexError) as e:
        logging.error(f"Error parsing GPS coordinates from msg_obj: {e}")
        lat = 0.0  # Default value if parsing fails
        lng = 0.0  # Default value if parsing fails
    
    
    #Switch between these two to see what happens
    # find_variables = reverse_geocode(location={"x": lng, "y": lat})
    
    #This will create a dictionary of other values from the point
    find_variables = reverse_geocode([lng, lat])
    
    
    ticket_dict = {
        "attributes": {
            "ticketnum": find_key(msg_obj, "ticketNum"),
            "loaddatetime": myutils.convert_iso8601_to_epoch_ms(find_key(msg_obj, "loadDTBegin")),
            "loadmonitor": find_key(msg_obj, "loadMonitor_ID"),
            "loadsitedesc": find_key(msg_obj, "disposalSiteName"),
            "roadwayid": find_key(msg_obj, "RoadwayId"),
            "lat": lat,
            "lng": lng, 
            "city": find_key(find_variables,"City"),
            "county": find_key(find_variables, "Subregion"),
            "state": find_key(find_variables, "Region"),
            "district": find_key(find_variables, "District"),
            "passclass": find_key(msg_obj, "PassClass"),
            "disposalsite": find_key(msg_obj, "disposalSiteName"),
            "disposalmonitor": find_key(msg_obj, "disposalMonitor_ID"),
            "maxcapacityl": find_key(msg_obj, "maxCapacity"),
            "disposaldatetime": myutils.convert_iso8601_to_epoch_ms(find_key(msg_obj, "disposalDT")),
            "maxcapacityd": find_key(msg_obj, "maxCapacity"),
            "loadcall": find_key(msg_obj, "LoadCall"),
            "haulvol": find_key(msg_obj, "haulVol"),
            "haulamt": find_key(msg_obj, "haulAmt"),
            "contractor": find_key(msg_obj, "contractorName"),
            "truck": find_key(msg_obj, "truckCertification_ID"),
            "sub": find_key(msg_obj, "subContractorName"),
            "driver": find_key(msg_obj, "driverName"),
            "mission": find_key(msg_obj, "missionName"),
            "payitem": find_key(msg_obj, "payItemName"),
            "notes": find_key(msg_obj, "note"),
            "invoice": find_key(msg_obj, "invoice")
        },
        "geometry": {
            "x": lng, 
            "y": lat
        }
    }
    # Log or print to debug
    logging.info(f"Constructed ticket dictionary: {ticket_dict}")
    
    #Test this out
    return ticket_dict

#Processes the file in the directory 
def process_files_in_directory(directory: str, process_file_callback) -> None:
    """
    Iterates over each JSON file in the specified directory and processes it will
    """
    for filename in os.listdir(directory):
        if filename.endswith(".json"):
            file_path = os.path.join(directory, filename)
            msg = load_json_files(file_path)
            
            if msg:
                logging.info(f"Process JSON file: {filename}")
                process_file_callback(msg)
            else:
                logging.error(f"Sipping file due to load error: {filename}")
    
#Processes all missions and if any mission folders need to be created
def process_missions(msg: dict):
    directory = r"C:\Users\Steven.Portillo\Coding_Projects\Python\Practice\.vs\ArcGIS_Projects\Steven"
    hosting_env = "DEV"
    try:
        gis = gis_login()
        
        mission_fs_name_full = process_message(msg, "missionName")
        portal_folder = "ADMS-{0}".format(hosting_env)#Will store the mission according to the hosting environment

        target_folder = gis.content.folders.get( 
                    folder=portal_folder, owner=gis.properties.user.username
                )

        #If the folder does not exist then it creates a new folder called "ADMS-{0}"
        if target_folder == None:
            logging.info('Creating a new folder - "{0}"'.format(portal_folder))
            target_folder = gis.content.folders.create(folder=portal_folder)

        logging.info(target_folder)

        # Paramters for the create_service method
        fs_name = mission_fs_name_full
        has_static_data = False  # want to be able to edit
        max_record_count = 1000
        capabilities = "Create,Editing,Uploads,Query,Update,Delete,Sync" #Capabilities for the mission
        service_wkid = 4326
        service_type = "featureService" #Becomes a feature service 
        item_properties = {"access": "org"} #Access is given to the org
        tags = [portal_folder, "feature"]
        snippet = "App worker automatically generated feature service"

    
        # Create the empty feature service
        empty_service_item = gis.content.create_service(
            name=fs_name,
            has_static_data=has_static_data,
            max_record_count=max_record_count,
            capabilities=capabilities,
            wkid=service_wkid,
            service_type=service_type,
            folder=portal_folder,
            item_properties=item_properties,
            tags=tags,
            snippet=snippet,
        )
        # The feature layer defintion template.
        # Note: print a feature layers properties to screen to see more definitions,
        #       see previous video Access Feature Layer and View Properties.
        fl_definition = {
            "type": "Feature Layer",
            "name": "tickets",
            "description": "App worker automatically created point layer",
            "geometryType": "esriGeometryPoint",
            "extent": {
                #Had to change this to zoom into the United States
                # "ymin": 24.396308,
                # "xmin": -125.0,
                # "ymax": 49.384358,
                # "xmax": -66.93457,
                
                #This is show the whole world
                "ymin": 17.903,
                "xmin": -165.938,
                "ymax": 53.702,
                "xmax": -30.938,
                "spatialReference": {"wkid": 4326},
            },
            "objectIdField": "OBJECTID",
            "fields": [
                {
                    "name": "OBJECTID",
                    "type": "esriFieldTypeOID",
                    "alias": "OBJECTID",
                    "nullable": False,
                    "editable": False
                },
                {
                    "name": "TicketNum",
                    "type": "esriFieldTypeString",
                    "alias": "Ticket Number",
                    "length": 32,
                    "nullable": True,
                    "editable": True
                },
                {
                    "name": "LoadDateTime",
                    "type": "esriFieldTypeDate",
                    "alias": "Load Date",
                    "editable": True,
                    "nullable": True
                },
                {
                    "name": "LoadMonitor",
                    "type": "esriFieldTypeString",
                    "alias": "Load Monitor",
                    "editable": True,
                    "nullable": True,
                    "length": 50
                },
                {
                    "name": "LoadSiteDesc",
                    "type": "esriFieldTypeString",
                    "alias": "LoadSiteDesc",
                    "editable": True,
                    "nullable": True,
                    "length": 256
                },
                {
                    "name": "RoadwayId",
                    "type": "esriFieldTypeString",
                    "alias": "RoadwayId",
                    "editable": True,
                    "nullable": True,
                    "length": 31
                },
                {
                    "name": "Lat",
                    "type": "esriFieldTypeDouble",
                    "alias": "Latitude",
                    "editable": True,
                    "nullable": True
                },
                {
                    "name": "Lng",
                    "type": "esriFieldTypeDouble",
                    "alias": "Longitude",
                    "editable": True,
                    "nullable": True
                },
                {
                    "name": "City",
                    "type": "esriFieldTypeString",
                    "alias": "City",
                    "editable": True,
                    "nullable": True,
                    "length": 256
                },
                {
                    "name": "County",
                    "type": "esriFieldTypeString",
                    "alias": "County",
                    "editable": True,
                    "nullable": True,
                    "length": 256
                },
                {
                    "name": "State",
                    "type": "esriFieldTypeString",
                    "alias": "State",
                    "editable": True,
                    "nullable": True,
                    "length": 24
                },
                {
                    "name": "District",
                    "type": "esriFieldTypeString",
                    "alias": "District",
                    "editable": True,
                    "nullable": True,
                    "length": 10
                },
                {
                    "name": "PassClass",
                    "type": "esriFieldTypeString",
                    "alias": "PassClass",
                    "editable": True,
                    "nullable": True,
                    "length": 512
                },
                {
                    "name": "DisposalSite",
                    "type": "esriFieldTypeString",
                    "alias": "DisposalSite",
                    "editable": True,
                    "nullable": True,
                    "length": 256
                },
                {
                    "name": "DisposalMonitor",
                    "type": "esriFieldTypeString",
                    "alias": "DisposalMonitor",
                    "editable": True,
                    "nullable": True,
                    "length": 50
                },
                {
                    "name": "MaxCapacityL",
                    "type": "esriFieldTypeDouble",
                    "alias": "Load Max Capacity",
                    "editable": True,
                    "nullable": True
                },
                {
                    "name": "DisposalDateTime",
                    "type": "esriFieldTypeDate",
                    "alias": "Disposal Date",
                    "editable": True,
                    "nullable": True
                },
                {
                    "name": "MaxCapacityD",
                    "type": "esriFieldTypeDouble",
                    "alias": "Disposal Max Capacity",
                    "editable": True,
                    "nullable": True
                },
                {
                    "name": "LoadCall",
                    "type": "esriFieldTypeSmallInteger",
                    "alias": "Load Call",
                    "editable": True,
                    "nullable": True
                },
                {
                    "name": "HaulVol",
                    "type": "esriFieldTypeDouble",
                    "alias": "Haul Volume",
                    "editable": True,
                    "nullable": True
                },
                {
                    "name": "HaulAmt",
                    "type": "esriFieldTypeDouble",
                    "alias": "Haul Amount",
                    "editable": True,
                    "nullable": True
                },
                {
                    "name": "Contractor",
                    "type": "esriFieldTypeString",
                    "alias": "Contractor",
                    "editable": True,
                    "nullable": True,
                    "length": 24
                },
                {
                    "name": "Truck",
                    "type": "esriFieldTypeString",
                    "alias": "Truck Plate",
                    "editable": True,
                    "nullable": True,
                    "length": 8
                },
                {
                    "name": "Sub",
                    "type": "esriFieldTypeString",
                    "alias": "Sub",
                    "editable": True,
                    "nullable": True,
                    "length": 256
                },
                {
                    "name": "Driver",
                    "type": "esriFieldTypeString",
                    "alias": "Driver",
                    "editable": True,
                    "nullable": True,
                    "length": 50
                },
                {
                    "name": "Mission",
                    "type": "esriFieldTypeString",
                    "alias": "Mission",
                    "editable": True,
                    "nullable": True,
                    "length": 24
                },
                {
                    "name": "PayItem",
                    "type": "esriFieldTypeString",
                    "alias": "Pay Item",
                    "editable": True,
                    "nullable": True,
                    "length": 255
                },
                {
                    "name": "Notes",
                    "type": "esriFieldTypeString",
                    "alias": "Notes",
                    "editable": True,
                    "nullable": True,
                    "length": 2047
                },
                {
                    "name": "Invoice",
                    "type": "esriFieldTypeString",
                    "alias": "Invoice",
                    "editable": True,
                    "nullable": True,
                    "length": 256
                }
            ],
            "geometryField": {
                "name": "SHAPE",
                "type": "esriFieldTypeGeometry",
                "alias": "SHAPE",
                "domain": None,
                "editable": True,
                "nullable": True,
                "defaultValue": None,
                "modelName": "SHAPE",
            },
            "uniqueIdField": {
                "isSystemMaintained": True,
                "name": "OBJECTID",
            },
            "dateFieldsTimeReference": {
                "timeZone": "UTC",
                "respectsDaylightSaving": False,
            },
            "hasAttachments": False
        }
        
        # Access as FeatureLayerCollection
        flc = FeatureLayerCollection.fromitem(empty_service_item)
        # Update the JSON definition for the feature service to iclude the layer
        flc.manager.add_to_definition({"layers": [fl_definition]})
        logging.info(
            "Created Feature Service - {0}".format(mission_fs_name_full)
        )    
    
    except Exception as ex:
        logging.error(f"Error while processing mission: {ex}")

#Processes all tickets
#The main core
def process_tickets(msg: dict) -> None:
    try:
        gis = gis_login()
        mission_fs_name_full = process_message(msg, "missionName")
        
        search_res = gis.content.search(f"title: {mission_fs_name_full}")
        
        #To make sure the mission name exists
        if len(search_res) == 0:
            logging.warning(f"title: {mission_fs_name_full} does not exist in this portal")
            exit(0)
            
        portal_item = search_res[0]
        tickets_layer = portal_item.layers[0]
        
        # ticket_num = process_searches(msg, "ticketNum")
        ticket_num = msg.get("ticketNum")
        ticket_dict = construct_ticket_dict(msg) #Error
        
        # ticket_num = msg["TicketNum"]
        add_result = tickets_layer.edit_features(adds = [ticket_dict])
        logging.info(f"Ticket# {ticket_num} was added into feature layer")
    except Exception as ex:
        logging.error(ex)
        logging.warning("Msg# processing failed!")
        exit(1)
    
    logging.info("Msg was processed")
    

#This is the create mission function
def create_mission_fs():
    directory = r"C:\Users\Steven.Portillo\Coding_Projects\Python\Practice\.vs\ArcGIS_Projects\Steven"
    process_files_in_directory(directory, process_missions)


#This is to add tickets to the missions
def add_tickets_to_missions():
    directory = r"C:\Users\Steven.Portillo\Coding_Projects\Python\Practice\.vs\ArcGIS_Projects\Steven"
    process_files_in_directory(directory, process_tickets)
    





#Note to self
#Check for parameters and their variable type to not have mistakes 
#Please check this as this very important
def modify_points_version_two(gis, mission_name, ticket_num, ticketLng, ticketLat, attributes_to_update):
    try:
        search_res = gis.content.search(f"title: {mission_name}")
            
        if len(search_res) == 0:
            print(f"title: {mission_name} does not exist in this portal!")
            exit(0)

        portal_item = search_res[0]
        print(f"found {portal_item}")
        
        tickets_layer = portal_item.layers[0]
        print(f"found {tickets_layer}")
        
        tickets_features = tickets_layer.query().features
        
        #Original
        #Obtains a list of tickets with the corresponding ticket number
        #There has to be a value that can distingush each ticket like a date for example????
        ticket_matches = [f for f in tickets_features if f.attributes['ticketnum']==ticket_num]
        
        #If no ticket is found then exit
        if len(ticket_matches) == 0:
            print(f"Ticket number {ticket_num} not found")
            return
    
        #Obtains the first ticket in the list, usually will only be one item in the matched ticket numbers
        ticket_edit = ticket_matches[0]
        
        
        
        #If the lat and lng are changed, all corresponding values need to be changed 
        #This includes the city, postal, address, county and state --> Will have to check if there is anything else that needs change 
        if ticketLng is not None and ticketLat is not None: 
            #Reverse geocode helps with obtaining specific data of a point
            reverse_geocode_result = reverse_geocode([ticketLng, ticketLat])
            
            #City, address, county, postal code and state are interpreted here
            ticket_city = reverse_geocode_result['address']['City']
            ticket_address = reverse_geocode_result['address']['Match_addr']
            ticket_county = reverse_geocode_result['address']['Subregion']
            ticket_postal_code = reverse_geocode_result['address']['Postal']
            ticket_state = reverse_geocode_result['address']['RegionAbbr']
            
            #The values above are then pushed into their respective dictionaries either attributes or geometry
            #Geometry is only the x (Longitude) and y (Latitude) coordinates
            ticket_edit.attributes["lng"] = ticketLng
            ticket_edit.attributes["lat"] = ticketLat
            ticket_edit.geometry = {"x": ticketLng, "y": ticketLat}
            
            #The values pertaining to city, county, state, address and postal are pushed as well into the dictionary
            ticket_edit.attributes["city"] = ticket_city
            ticket_edit.attributes["county"] = ticket_county
            ticket_edit.attributes["state"] = ticket_state
            ticket_edit.attributes["address"] = ticket_address
            ticket_edit.attributes["postal"] = ticket_postal_code
     

        #If there is anything to update 
        #Any attributes that need to be changed run through here
        if attributes_to_update:
            """
            For every attribute in the dictionary of attribute_to_update
            if there is an attribute in the dictionaries in the ticket 
            Make the attribute of the ticket the value from attributes_to_update
            """
            
            for attr, value in attributes_to_update.items():
                if attr in ticket_edit.attributes:
                    ticket_edit.attributes[attr] = value
                else: 
                    print(f"Warning: attribute{attr} does not exist in the ticket")
         
        #The updated attributes are then sent and printed
        update_result = tickets_layer.edit_features(updates = [ticket_edit])
        

        update_result_success = update_result['updateResults'][0]['success']
        update_result_objectID = update_result['updateResults' ][0]['objectId']
        
        
        if update_result_success:
            print(f"Update successful for objectID: {update_result_objectID}")
        else:
            print(f"Failed to update ticket #{ticket_num}")
        # return update_result
    
    except Exception as Ex:
        print(f"There was an error with something: {Ex}")
    

#This function is used to edit the feature layer collection
def edit_mission(gis, mission_name, new_table):
    #Serch for the mission (feature layer collection)
    search_res = gis.content.search(f"title: {mission_name}")
    
    
    # new_extent = {
    #     "xmin": -165.938,
    #     "ymin": 17.903,
    #     "xmax": -30.938,
    #     "ymax": 53.702,
    #     "spatialReference": {
    #         "wkid": {"wkid": 4326}
    #     }
    # }


    # new_definition = {
    #     "name": "My new tickets",
    #     "description": "A new application is being made here",
    #     "extent": new_extent
    # }
    
    #This is a dictionary with things to change for the feature layer collection
    

    #If nothing shows up then return that it does not exist
    if len(search_res) == 0:
        print(f"title: {mission_name} does not exist in this portal!")
        exit(0)

    #Searches for the feature layer collection (Feature Service)
    portal_item = search_res[0]
    print(f"found {portal_item}")
    
    #Creates an instance of the feature layer collection
    flc = FeatureLayerCollection.fromitem(portal_item)
    
    #This will print out all the properties in the feature layer collection
    # print(flc.properties.capabilities)
    
    #This will update the feature layer collection
    flc.manager.update_definition(new_table)
    
    


def edit_feature_layer(gis, mission_name, new_parameters: dict):
    """_summary_
    This function allows the user to update the individual feature layer
    For example you can change the name, the extent and other attributes below
    
    
    """
    
    search_res = gis.content.search(f"title: {mission_name}")
    
    
    if len(search_res) == 0:
        print(f"title: {mission_name} does not exist in this portal!")
        exit(0)
    
    portal_item = search_res[0]
    print(f"found {portal_item}")
    
    # target_folder = portal_item.layers[0]
    # print(f"found {target_folder}")
    
    flc = FeatureLayerCollection.fromitem(portal_item)
    print(f"found {flc}")
    
    feature_layer = flc.layers[0]
    print(f"found {feature_layer}")
    
    # print(feature_layer.features)
    
    feature_layer.manager.update_definition(new_parameters)
    
    # print(feature_layer)
    # feature_layer.manager.update_definition(new_parameters)
    
    
    
    
    
if __name__ == "__main__":
    pass