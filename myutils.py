from datetime import datetime
from arcgis.geocoding import reverse_geocode


def get_unique_fs_name_per_env(fs_name, hosting_env):
    # For non-production environment, append env suffix to feature service name
    if hosting_env != "PROD":
        return f"{fs_name}_{hosting_env}"
    
    # For production environment, leave as is
    return fs_name


def sanitize_fs_name(mission_name):
    BLOB_NAME_SPLITTER = '-'
    FS_NAME_SPLITTER = '_'

    fs_name = mission_name.replace(BLOB_NAME_SPLITTER, FS_NAME_SPLITTER)

    return fs_name

def convert_iso8601_to_epoch_ms(iso8601_time_str):
    if iso8601_time_str is None or iso8601_time_str.strip == "":
        return None

    dt = datetime.fromisoformat(iso8601_time_str.replace('Z', '+00:00'))
    epoch_ms = int(dt.timestamp() * 1000)
    return epoch_ms


def modify_point(gis, fs_name, ticket_num, ticketLng, ticketLat):       
        search_res = gis.content.search(f"title: {fs_name}")
        if len(search_res) == 0:
            print(f"title: {fs_name} does not exist in this portal!")
            exit(0)
        #get the first feature service (the mission)
        portal_item = search_res[0]
        print(f"found {portal_item}")
        #get the first layer of the feature service (the ticket layer)
        tickets_layer = portal_item.layers[0]
        #to update a ticket
        #query the ticket layer for the ticket number
        #first query the ticket layer for the features cllection
        reverse_geocode_result = reverse_geocode([ticketLng, ticketLat])
        # print(reverse_geocode_result)
        ticketAddress = reverse_geocode_result['address']['Match_addr']
        ticketCounty = reverse_geocode_result['address']['Subregion']
        ticketCity = reverse_geocode_result['address']['City']
        tickeetZipCode = reverse_geocode_result['address']['Postal']
        ticketState = reverse_geocode_result['address']['RegionAbbr']
        tickets_features = tickets_layer.query().features
        #get the ticket feature from the features collection using the ticket number
        #for a specific ticket
        ticket_feature = [f for f in tickets_features if f.attributes['ticketnum']==ticket_num][0]
        #ticket_edit contains the feature object for the specific ticket to be edited
        ticket_edit = ticket_feature
        #edit the ticket "loadmonitor" attribute
        ticket_edit.attributes["loadmonitor"] = "Marco Polo"
        #edit the ticket "lng" attribute
        ticket_edit.attributes["lng"] = ticketLng
        #edit the ticket "lat" attribute
        ticket_edit.attributes["lat"] = ticketLat
        #edit the ticket "geometry" attribute
        ticket_edit.geometry = {"x": ticketLng, "y": ticketLat}
        #edit the ticket city attribute
        ticket_edit.attributes["city"] = ticketCity
        #edit the ticket county attribute
        ticket_edit.attributes["county"] = ticketCounty
        #edit the ticket state attribute
        ticket_edit.attributes["state"] = ticketState
        #print the result of the update
        update_result = tickets_layer.edit_features(updates = [ticket_edit])
        update_result_success = update_result['updateResults'][0]['success']
        update_result_objectID = update_result['updateResults'][0]['objectId']
        if update_result_success == True:
            print(f"the update result for objectID: {update_result_objectID} is: {update_result_success}")       
        return update_result

