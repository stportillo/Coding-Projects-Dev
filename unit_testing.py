import dumby
import myutils

#This is the main class to just create the missions with tickets
class create_mission_tickets():
    def main():
        dumby.create_mission_fs()
        dumby.add_tickets_to_missions()


#This are test units for the updating tickets
class Testing():
    def testingOne():
        gis = dumby.gis_login()
        mission_name = "St_Mary_Francine_2024_DEV"
        ticket_num = "9164240926103102"
        ticket_lng = -118.2437
        ticket_lat = 34.0522
        
        attributes_to_update = {
            "loadmonitor": "Bob",
            "loadsitedesc": "Worker",
            "roadwayid": 9282882,
            "loaddatetime": myutils.convert_iso8601_to_epoch_ms("2024-09-27 08:14:44")
            }
        dumby.modify_points_version_two(gis, mission_name, ticket_num, ticket_lng, ticket_lat, attributes_to_update)
    
    def testingTwo():
        gis = dumby.gis_login()
        mission_name = "St_Mary_Francine_2024_DEV"
        ticket_num = "9164240926082739"
        ticket_lng = -80.22830577208659
        ticket_lat = 25.781546624466525
        
        attributes_to_update = {
            "loadmonitor": "Steven",
            "loadsitedesc": "New Worker",
            "roadwayid": 786238
            }
        dumby.modify_points_version_two(gis, mission_name, ticket_num, ticket_lng, ticket_lat, attributes_to_update)
        
    #Ticket Number invalid
    #Remember that all parameters must be correctly used with the correct variable type
    def testingThree():
        gis = dumby.gis_login()
        mission_name = "St_Mary_Francine_2024_DEV"
        ticket_num = "1234"
        ticket_lng = -80.22830577208659
        ticket_lat = 25.781546624466525
        
        attributes_to_update = {
            "loadmonitor": "Steven",
            "loadsitedesc": "New Worker",
            "roadwayid": 786238
            }
        dumby.modify_points_version_two(gis, mission_name, ticket_num, ticket_lng, ticket_lat, attributes_to_update)
        
    #Gis is not properly configured
    def testingFour():
        gis = None
        mission_name = "St_Mary_Francine_2024_DEV"
        ticket_num = "1234"
        ticket_lng = -80.22830577208659
        ticket_lat = 25.781546624466525
        
        attributes_to_update = {
            "loadmonitor": "Steven",
            "loadsitedesc": "New Worker",
            "roadwayid": 786238
            }
        dumby.modify_points_version_two(gis, mission_name, ticket_num, ticket_lng, ticket_lat, attributes_to_update)
        
    def testingFive():
        gis = dumby.gis_login()
        mission_name = "TEST1234_DEV"
        ticket_num = "9166240926122205"
        ticket_lng = -80.22830577208659
        ticket_lat = 25.781546624466525
        
        attributes_to_update = {
            "loadmonitor": "Captain Ahab",
            "loadsitedesc": "Worker",
            "roadwayid": 435277283
            }
        dumby.modify_points_version_two(gis, mission_name, ticket_num, ticket_lng, ticket_lat, attributes_to_update)
        
    #New York Museum of Art
    def testingSix():
        gis = dumby.gis_login()
        mission_name = "TEST1234_DEV"
        ticket_num = "9166240926122358"
        ticket_lng = -73.9632901974198
        ticket_lat = 40.77954238191457
        
        attributes_to_update = {
            "loadmonitor": "Queequeg",
            "loadsitedesc": "Artist",
            "roadwayid": 98765432
            }
        dumby.modify_points_version_two(gis, mission_name, ticket_num, ticket_lng, ticket_lat, attributes_to_update)

    def testingSeven():
        gis = dumby.gis_login()
        mission_name = "TEST1234_DEV"
        ticket_num = "9166241011231750"
        ticket_lng = 25.728281
        ticket_lat = -80.42505
        
        attributes_to_update = {
            "loadmonitor": "Pierre Bezukhov",
            "loadsitedesc": "Artistocrat",
            "roadwayid": 75432
            }
        dumby.modify_points_version_two(gis, mission_name, ticket_num, ticket_lng, ticket_lat, attributes_to_update)
        
        
    def testingEight():
        gis = dumby.gis_login()
        mission_name = "TEST1234_DEV"
        ticket_num = "9166241011231639"
        ticket_lng = 25.7282889
        ticket_lat = -80.4250481
        
        attributes_to_update = {
            "loadmonitor": "Pierre Bezukhov",
            "loadsitedesc": "Artistocrat",
            "roadwayid": 98765432
            }
        dumby.modify_points_version_two(gis, mission_name, ticket_num, ticket_lng, ticket_lat, attributes_to_update)
    
    def testingNine():
        gis = dumby.gis_login()
        mission_name = "TEST1234_DEV"
        ticket_num = "9166241013164747"
        ticket_lng = 25.7283046
        ticket_lat = -80.4250812
        
        attributes_to_update = {
            "loadmonitor": "Rashkolnikov",
            "loadsitedesc": "Dostoevsky",
            "roadwayid": 875463749
            }
        dumby.modify_points_version_two(gis, mission_name, ticket_num, ticket_lng, ticket_lat, attributes_to_update)


#This is for testing the editing mission function
class TestingTwo: 
    def testing_one():
        gis = dumby.gis_login()
        mission_name = "St_Mary_Francine_2024_DEV"
        another_thing = {
            'description': "Changing this as soon as possible",
            # "spatialReference": {"wkid": 4326},
            "initialExtent": {
                "ymin": 24.396308,
                "xmin": -125.0,
                "ymax": 49.384358,
                "xmax": -66.93457,
                "spatialReference": {
                    "latestWkid": 3857,
                    "wkid": 102100
                },
                
                # "ymin": 17.903,
                # "xmin": -165.938,
                # "ymax": 53.702,
                # "xmax": -30.938,
                # "spatialReference": {
                #     "latestWkid": 3857,
                #     "wkid": 102100
                # },
            },
            # "fullExtent": {
            #     "ymin": 24.396308,
            #     "xmin": -125.0,
            #     "ymax": 49.384358,
            #     "xmax": -66.93457,
            #     "spatialReference": {"wkid": 4326}
            # },
            "serviceDescription": "Trying to fix this"
        }
        
        # county_name = "St. Mary Parish"
        
        dumby.edit_mission(gis, mission_name, another_thing)
    
    def testing_Two():
        gis = dumby.gis_login()
        mission_name = "St_Mary_Francine_2024_DEV"
        new_parameters = {
            "name": "Steven's cookies and change",
            "description": "Moby Dick - Great American Novel",
            "extent": {
                "ymin": 17.903,
                "xmin": -165.938,
                "ymax": 53.702,
                "xmax": -30.938,
                "spatialReference": {"wkid": 4326}
            },
            "hasAttachments": True
        }
        # county_name = "Washington County"
        
        dumby.edit_feature_layer(gis, mission_name, new_parameters)





if __name__ == "__main__":
    #This is a sort of main just to create the missions and the tickets 
    # create_mission_tickets.main()
    
    
    #Testing the updating points functions
    # Testing.testingOne()
    # Testing.testingTwo()
    # Testing.testingThree()
    # Testing.testingFour()
    # Testing.testingFive()
    # Testing.testingSix()
    # Testing.testingSeven()
    # Testing.testingEight()
    # Testing.testingNine()
    
    # TestingTwo.testing_one()
    TestingTwo.testing_Two()
    
    
    #Notes
    """
    Works for both files so far 
    Only thing is that it needs another parameter that is indefinite that can distinguish
    ticket with the same number for example 
    """
    pass