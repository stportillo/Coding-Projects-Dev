import os
import json
import logging
import myutils

import azure.functions as func

from arcgis.gis import GIS
from arcgis.features import FeatureLayerCollection, FeatureLayer
from arcgis.geocoding import reverse_geocode


PORTAL_URL = os.getenv("ARCGIS_PORTAL_URL")
PORTAL_USR = os.getenv("ARCGIS_PORTAL_SA_USR")
PORTAL_PWD = os.getenv("ARCGIS_PORTAL_SA_PWD")
ENV_SIG = os.getenv("ADMS_ENV_SIG")

app = func.FunctionApp()

#To login into arcgis
def gis_login() -> GIS:
    try:
        gis = GIS(PORTAL_URL, PORTAL_USR, PORTAL_PWD)
        logging.info(f"Logged in as {gis.properties.user.username}")
        return gis
    except Exception as e:
        logging.error("Failed to login in to ArcGIS Portal: {0}".format(e))
        raise



#Function to conduct reverse geocode for a JSON file
def reverse_geography(msg_obj: dict):
    lat, lng = 0.0, 0.0
    """    
    In every JSON file there is a "beginningGPS" which will give the coordinates together
    Example is below
    "beginningGps": "29.75911431,-91.17472132"
    """
    try:
        gps = msg_obj["beginningGps"]
        gps_coords = gps.split(",")  # Split the string by the comma
        lat = float(gps_coords[0].strip())  # First part is latitude
        lng = float(gps_coords[1].strip())  # Second part is longitude
        
    except (KeyError, ValueError, IndexError) as e:
        logging.error(f"Error parsing GPS coordinates from msg_obj: {e}")
        lat = 0.0  # Default value if parsing fails
        lng = 0.0  # Default value if parsing fails
        
    #This create a dictionary with any information such as postal, city, state, etc.
    coordinates = reverse_geocode([lng, lat])
    
    return coordinates


#Function to find the extent of the state according to the ESRI open feature layer 
def extent_of_state(state_name):
    
    gis = gis_login()
    
    #Find the feature layer for the state boundaries
    state_layer_url = "https://services.arcgis.com/P3ePLMYs2RVChkJx/arcgis/rest/services/USA_States_Generalized_Boundaries/FeatureServer/0"
    state_layer = FeatureLayer(state_layer_url) #Obtains the data from the url as makes it an object in memory 
    
    
    #Get the state boundary layer (URL is the feature layer )
    query_result = state_layer.query(where=f"STATE_NAME='{state_name}'", return_geometry=True, out_fields="STATE_NAME")
    
   
    if query_result and len(query_result.features) > 0:
        # Extract the geometry (polygon) from the first feature
        feature = query_result.features[0]
    
        state_geometry = feature.geometry
        
        if state_geometry and "rings" in state_geometry:
            # Extract the rings (polygon coordinates)
            rings = state_geometry['rings']
            
            # Initialize min/max values to calculate extent
            xmin, ymin = float('inf'), float('inf')
            xmax, ymax = float('-inf'), float('-inf')
            
            # Iterate over all the coordinates to find the min/max values
            for ring in rings:
                for point in ring:
                    x, y = point[0], point[1]
                    xmin = min(xmin, x)
                    ymin = min(ymin, y)
                    xmax = max(xmax, x)
                    ymax = max(ymax, y)
            
            # Return the calculated extent as a dictionary
            polygon_extent = {
                "ymin": ymin,
                "xmin": xmin,
                "ymax": ymax,
                "xmax": xmax, 
                "spatialReference": {"wkid": 4326},
            }
            # print(polygon_extent)
            return polygon_extent
        else:
            return "Geometry not available or not a polygon"
    else:
        return "State not found in the layer"






@app.queue_trigger(arg_name="azqueue", queue_name="adms-gis-new-missions",
                               connection="ADMS_STORE_CONNSTR") 
def create_mission_fs(azqueue: func.QueueMessage) -> None:
    msg = azqueue.get_body().decode('utf-8')
    logging.info('Python Queue trigger processed a message: %s', msg)

    # Access ArcGIS Enterprise Portal
    gis = GIS(PORTAL_URL, PORTAL_USR, PORTAL_PWD)
    logging.info(
        "Logged in ArcGIS Portal as {0}".format(gis.properties.user.username)
    )
    # 'Process' the message
    msg_obj = json.loads(msg)
    hosting_env = msg_obj["env"]
    mission_name = msg_obj["missionName"]
    mission_fs_name = myutils.sanitize_fs_name(mission_name)
    mission_fs_name_full = myutils.get_unique_fs_name_per_env(
        mission_fs_name, hosting_env
    )
    
    
    
    """
    Finds the extent of the state
    """
    #Find the state name
    state_name = msg_obj["mission_state"]
    #Get the extent of the state
    new_extent = extent_of_state(state_name)
    
    
    
    
    portal_folder = "ADMS-{0}".format(hosting_env)
    target_folder = gis.content.folders.get(
        folder=portal_folder, owner=gis.properties.user.username
    )

    if target_folder == None:
        logging.info('Creating a new folder - "{0}"'.format(portal_folder))
        target_folder = gis.content.folders.create(folder=portal_folder)

    logging.info(target_folder)

    # Paramters for the create_service method
    fs_name = mission_fs_name_full
    has_static_data = False  # want to be able to edit
    max_record_count = 1000
    capabilities = "Create,Editing,Uploads,Query,Update,Delete,Sync"
    service_wkid = 4326
    service_type = "featureService"
    item_properties = {"access": "org"}
    tags = [portal_folder, "feature"]
    snippet = "App worker automatically generated feature service"

    try:
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
            "extent": new_extent,
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
        logging.error(ex)
        logging.warning("Msg# {0} processing failed!".format(azqueue.id))
    
    logging.info("Msg# {0} was processed.".format(azqueue.id))




@app.queue_trigger(arg_name="azqueue", queue_name="adms-gis-new-tickets",
                               connection="ADMS_STORE_CONNSTR") 
def add_tickets_to_featurelayer(azqueue: func.QueueMessage) -> None:
    msg = azqueue.get_body().decode('utf-8')
    logging.info('Starting add tickets to feature layer process...')

    try:
        # Access ArcGIS Enterprise Portal
        gis = GIS(PORTAL_URL, PORTAL_USR, PORTAL_PWD)
        logging.info(
            "Logged in ArcGIS Portal as {0}".format(gis.properties.user.username)
        )
    
        # 'Process' the message
        msg_obj = json.loads(msg)
        mission_name = msg_obj["Mission"]
        mission_fs_name = myutils.sanitize_fs_name(mission_name)
        mission_fs_name_full = myutils.get_unique_fs_name_per_env(mission_fs_name, ENV_SIG)

        search_res = gis.content.search(f"title: {mission_fs_name_full}")
        if len(search_res) == 0:
            logging.warning(f"title: {mission_fs_name_full} does not exist in this portal!")
            exit(0)

        portal_item = search_res[0]
        tickets_layer = portal_item.layers[0]

        ticket_num = msg_obj["TicketNum"]
        # construct a Feature object for Los Angeles.
        ticket_dict = {
            "attributes": {
                "ticketnum": msg_obj["TicketNum"],
                "loaddatetime": myutils.convert_iso8601_to_epoch_ms(msg_obj["LoadDateTime"]),
                "loadmonitor": msg_obj["LoadMonitor"],
                "loadsitedesc": msg_obj["LoadSiteDesc"],
                "roadwayid": msg_obj["RoadwayId"],
                "lat": msg_obj["Lat"],
                "lng": msg_obj["Lng"],
                "city": msg_obj["City"],
                "county": msg_obj["County"],
                "state": msg_obj["State"],
                "district": msg_obj["District"],
                "passclass": msg_obj["PassClass"],
                "disposalsite": msg_obj["DisposalSite"],
                "disposalmonitor": msg_obj["DisposalMonitor"],
                "maxcapacityl": msg_obj["MaxCapacityL"],
                "disposaldatetime": myutils.convert_iso8601_to_epoch_ms(msg_obj["DisposalDateTime"]),
                "maxcapacityd": msg_obj["MaxCapacityD"],
                "loadcall": msg_obj["LoadCall"],
                "haulvol": msg_obj["HaulVol"],
                "haulamt": msg_obj["HaulAmt"],
                "contractor": msg_obj["Contractor"],
                "truck": msg_obj["Truck"],
                "sub": msg_obj["Sub"],
                "driver": msg_obj["Driver"],
                "mission": msg_obj["Mission"],
                "payitem": msg_obj["PayItem"],
                "notes": msg_obj["Notes"],
                "invoice": msg_obj["Invoice"]
            },
            "geometry": {
                "x": msg_obj["Lng"], 
                "y": msg_obj["Lat"]
            }
        }
        add_result = tickets_layer.edit_features(adds = [ticket_dict])
        logging.info(f"Ticket# {ticket_num} was added into feature layer!")
    except Exception as ex:
        logging.error(ex)
        logging.warning("Msg# {0} processing failed!".format(azqueue.id))
        exit(1)

    logging.info("Msg# {0} was processed.".format(azqueue.id))
    