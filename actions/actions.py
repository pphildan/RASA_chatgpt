from typing import Any, Text, Dict, List

from rasa_sdk.events import SlotSet, ActiveLoop, Form
from rasa_sdk.events import AllSlotsReset, FollowupAction
from rasa_sdk.events import EventType
from rasa_sdk import Action, Tracker, FormValidationAction
from rasa_sdk.executor import CollectingDispatcher
from rasa_sdk.types import DomainDict
from openai import OpenAI
import openai
import os
import json
import requests
import os
import time as t
import random
from datetime import time, datetime
from bs4 import BeautifulSoup


import openmeteo_requests

import requests_cache
import pandas as pd
from retry_requests import retry




def update_booking_info(booking_info):
    with open("booking_info.json", "w") as file:
        json.dump(booking_info, file)

config_file = 'actions/config.json'
with open(config_file, 'r') as f:
    config = json.load(f)


os.environ['OPENAI_API_KEY'] = config['api_key']
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))



def new_thread():
    empty_thread = openai.beta.threads.create()
    thread_id = empty_thread.id
    return thread_id

asst_id = config['assistant']

thread_id = new_thread()

def create_message(text_message):
    thread_message = openai.beta.threads.messages.create(
        thread_id,
        role="user",
        content=text_message)                  
    return None

def run_thread():
    start_time = t.time()  # Record the start time

    run = client.beta.threads.runs.create(
        thread_id=thread_id,
        assistant_id=asst_id)

    while True:
        t.sleep(0.4)  # Sleep for 400 milliseconds
        r_run = client.beta.threads.runs.retrieve(
            thread_id=thread_id,
            run_id=run.id)
        print(r_run.status)

        if r_run.status == 'completed':
            thread_messages = client.beta.threads.messages.list(thread_id, limit=2)
            break

        # Check if 10 seconds have passed
        if t.time() - start_time > 10:
            print("Timeout reached, restarting function")
            client.beta.threads.runs.cancel(
                thread_id=thread_id,
                run_id=run.id
            )
            return run_thread()  # Restart the function

    return thread_messages



not_available_for_this_slot = False

class ActionConfirmBooking(Action):

    def name(self) -> Text:
        return "action_confirm"

    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:

        von = tracker.get_slot("from")
        to = tracker.get_slot("to")
        name = tracker.get_slot("name")
        if von is not None and to is not None and name is not None:
            dispatcher.utter_message(text=f"Perfect, I booked a room from {von} bis {to} for {name}! The room is located on the first floor on the left-hand side. There is a screen in front of the room where you can see your reservation shortly before the start of the time.")
            global booking_info
            update_booking_info(booking_info = {
                            "name": name,
                            "von": von,
                            "bis": to
                            })
            global message_sent
            message_sent = False
            global thread_id
            thread_id = new_thread()
        return [AllSlotsReset(), FollowupAction('action_listen')]

class ActionConfirmBooking(Action):

    def name(self) -> Text:
        return "action_confirm_possibility"


    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:

        #Simulating vysoft if there are 2 time slots left
        available_slots = [
            # Morning slots (8 AM to 10 AM)
            (time(8, 0), time(10, 0)),
            # Afternoon slots (1 PM to 6 PM)
            (time(13, 0), time(18, 0))
        ]
        #Simulating vysoft if there is no room left
        # available_slots = [
        #     # Morning slots (8 AM to 10 AM)
        #     #(time(8, 0), time(10, 0)),
        #     # Afternoon slots (1 PM to 6 PM)
        #     #(time(13, 0), time(18, 0))
        # ]
        #Simulating vysoft if there is no booking yet
        # available_slots = [
        #     #Morning slots (7 AM to 6 PM)
        #     (time(7, 0), time(18, 0)),
        #     #Afternoon slots (1 PM to 6 PM)
        #     #(time(13, 0), time(18, 0))
        # ]
        
        
        # von = tracker.get_slot("from")
        # to = tracker.get_slot("to")
        # name = tracker.get_slot("name")
        von = None
        to = None
        name = None


        variable_list = []
        message = "Today we have a free time slot "
    
        for available_start, available_end in available_slots:
            variable_value = f"from {str(available_start)[:-3]} to {str(available_end)[:-3]}"
            # Append the variable value to the list
            variable_list.append(variable_value)

        for i, variable_value in enumerate(variable_list):
            message = message + variable_value + " and "

        user_input = tracker.latest_message.get('text')

        create_message(user_input + '\n' +  "room_availabilities :" + message)

        thread_messages = run_thread()
        

    
        # Extract the assistant's reply
        assistant_reply = thread_messages.data[0].content[0].text.value
        print(assistant_reply)
    

        try:
            assistant_reply = assistant_reply.replace("'", '"') 
            json_obj = json.loads(assistant_reply)
            # Check if the response contains the "room_booking" intent
            von = json_obj['from']
            to = json_obj['to']
            name = json_obj['name']
            
  
                    
        except json.JSONDecodeError:
            # The assistant's reply is not a valid JSON string
                
            dispatcher.utter_message(text=assistant_reply)


        global not_available_for_this_slot

        if von is not None and to is not None and name is not None:
            return [FollowupAction("action_confirm"), SlotSet("to", to), SlotSet("from", von), SlotSet("name", name)]


class ActionChatWithGPT(Action):

    def name(self) -> Text:
        return "action_chat_with_gpt"
  
    
    async def run(self, dispatcher: CollectingDispatcher,
                  tracker: Tracker,
                  domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:

        # Get the latest user message
        user_input = tracker.latest_message.get('text')

        create_message(user_input)

        thread_messages = run_thread()
        

    
        # Extract the assistant's reply
        assistant_reply = thread_messages.data[0].content[0].text.value
        print(assistant_reply)

        von = None
        to = None
        name = None
    

        try:
            assistant_reply = assistant_reply.replace("'", '"') 
            json_obj = json.loads(assistant_reply)
            # Check if the response contains the "room_booking" intent
            von = json_obj['from']
            to = json_obj['to']
            name = json_obj['name']
            
            #start_time = datetime.strptime(von, '%H:%M:%S').time()
            #end_time = datetime.strptime(to, '%H:%M:%S').time()
  
                    
        except json.JSONDecodeError:
            # The assistant's reply is not a valid JSON string
                
            dispatcher.utter_message(text=assistant_reply)


        global not_available_for_this_slot

        if von is not None and to is not None and name is not None:
            return [FollowupAction("action_confirm"), SlotSet("to", to), SlotSet("from", von), SlotSet("name", name)] 
        else:
            return [FollowupAction('action_listen')]

class ActionResetSlots(Action):

    def name(self) -> Text:
        return "action_reset_slots"

    def run(self, dispatcher: CollectingDispatcher, tracker: Tracker, domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
        dispatcher.utter_message(text="All right, how else can I help?")
        global thread_id
        thread_id = new_thread()
        return [AllSlotsReset(), ActiveLoop(None), FollowupAction('action_listen')]




class ActionCurrentWheather(Action):

    def name(self) -> Text:
        return "current_weather"
 

    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:

        # Setup the Open-Meteo API client with cache and retry on error
        cache_session = requests_cache.CachedSession('.cache', expire_after = 3600)
        retry_session = retry(cache_session, retries = 5, backoff_factor = 0.2)
        openmeteo = openmeteo_requests.Client(session = retry_session)

        # Make sure all required weather variables are listed here
        # The order of variables in hourly or daily is important to assign them correctly below
        url = "https://api.open-meteo.com/v1/forecast"
        params = {
            "latitude": 47.4239,
            "longitude": 9.3748,
            "current": ["temperature_2m", "rain", "snowfall", "cloud_cover"],
            "daily": ["temperature_2m_max", "sunshine_duration", "rain_sum", "snowfall_sum"],
            "timezone": "auto",
            "forecast_days": 1
        }
        responses = openmeteo.weather_api(url, params=params)

        # Process first location. Add a for-loop for multiple locations or weather models
        response = responses[0]
    
        # Current values. The order of variables needs to be the same as requested.
        current = response.Current()
        current_temperature_2m = int(current.Variables(0).Value())
        current_rain = int(current.Variables(1).Value())
        current_snowfall = int(current.Variables(2).Value()*100)
        current_cloud_cover = int(current.Variables(3).Value())
        
        if current_snowfall != 0:
            current_snowfall = True
        else:
            current_snowfall = False
        if current_rain != 0:
            current_rain = True
        else:
            current_rain = False

        # Process daily data. The order of variables needs to be the same as requested.
        daily = response.Daily()
        daily_temperature_2m_max = int(daily.Variables(0).ValuesAsNumpy())
        daily_sunshine_duration = int(daily.Variables(1).ValuesAsNumpy())
        daily_rain_sum = int(daily.Variables(2).ValuesAsNumpy())
        daily_snowfall_sum = int(daily.Variables(3).ValuesAsNumpy())
        print("ok")
       



        current_weather = f"Current Weather Information in St.Gallen: Current temperature: {current_temperature_2m}." + f"Current rain: {current_rain}." + f"Current snowfall: {current_snowfall}." + f"Current cloud cover: {current_cloud_cover}."
        tomorrows_weather = f"Tomorrows Weather Information in St.Gallen: Tomorrows max temperature: {daily_temperature_2m_max}." + f"Tomorrows sunshine duration: {daily_sunshine_duration}." + f"Tomorrows rai sum: {daily_rain_sum}." + f"Tomorrows snowfall sum: {daily_snowfall_sum}."
        print(current_weather)
        # Get the latest user message
        user_input = tracker.latest_message.get('text')
        create_message(user_input + "\n" + current_weather+ "\n" + tomorrows_weather)
        thread_messages = run_thread()
        
        # Extract the assistant's reply
        assistant_reply = thread_messages.data[0].content[0].text.value
        print(assistant_reply)

        dispatcher.utter_message(text=assistant_reply)

        
        return [FollowupAction('action_listen')]   


class ActionCurrentWheather(Action):

    def name(self) -> Text:
        return "current_events"
 

    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:

        
        current_date = datetime.now().strftime("%d.%m.%Y")


        # URL of the website to crawl
        #url = 'https://www.hsg-square.ch/en/program/current-events/'
        url = f'https://www.hsg-square.ch/en/program/current-events/eventsformsent/1/eventdate/{current_date} - 31.12.2023/eventcategory/*/eventvenue/*/eventspeaker/*/eventquery/*/'

        # Send a GET request to the website
        response = requests.get(url)
        
        # Check if the request was successful
        if response.status_code == 200:
            # Parse the HTML content
            soup = BeautifulSoup(response.content, 'html.parser')

            # Find elements containing the event information
            # Note: This is a generic example, you'll need to adjust the selectors
            # based on the actual HTML structure of the website
            events = soup.find_all('div', class_='col mb-gap')  # Adjust the class name as per actual website
            i = 1
            event_list = []
            # Loop through each event and extract information
            for event in events:
                #print(event)
                title = event.find('h3', class_='mb-3').text  # Adjust the tag and class as needed
                day = event.find('div', class_= "font-size-ui-nav text-uppercase mt-3").text
                time = event.find('div', class_= "mt-3 text-center")
                time = time.find('div', class_= "font-size-ui-nav").text
                date = event.find('div', class_='h1 huge mb-0').text  # Adjust the class name
                location = event.find('div', class_="col-12 col-lg-9").text
                parsed_location = location.split(",")[0]
                events = f'Event : Date: {day}, {date} at {time}, Title: {title}, Location: {parsed_location}'
                event_list.append(events)
                i+=1
        else:
            print(f"Failed to retrieve content: Status code {response.status_code}")
            events = "I am not able to get the current events, because of a problem of the website. Please try it later."
        
       

        # Get the latest user message
        user_input = tracker.latest_message.get('text')
        create_message(text_message=user_input + "\n" + "Context Information:" + "\n" + "Todays Date: " + str(current_date) + "\n" + str(event_list[1:]))
        
        thread_messages = run_thread()
        print(str(event_list[1:]))
        # Extract the assistant's reply
        assistant_reply = thread_messages.data[0].content[0].text.value
        print(assistant_reply)

        dispatcher.utter_message(text=assistant_reply)

        
        return [FollowupAction('action_listen')]   




class ActionBusFromDfour(Action):

    def name(self) -> Text:
        return "next_bus"
 

    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:

        current_day_of_week = datetime.now().strftime("%A")

        # Selecting bus times based on the current day of the week
        if current_day_of_week in ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday"]:
            times_duf = [
                        '7.07', '7.17', '7.27', '7.37', '7.47', '7.57', '8.07', '8.17', '8.27',
                        '8.37', '8.47', '8.57', '9.07', '9.17', '9.27', '9.37', '9.47', '9.57',
                        '10.07', '10.17', '10.27', '10.37', '10.47', '10.57', '11.07', '11.17',
                        '11.27', '11.37', '11.47', '11.57', '12.07', '12.17', '12.27', '12.37',
                        '12.47', '12.57', '13.07', '13.17', '13.27', '13.37', '13.47', '13.57',
                        '14.07', '14.17', '14.27', '14.37', '14.47', '14.57', '15.07', '15.17',
                        '15.27', '15.37', '15.47', '15.57', '16.07', '16.17', '16.27', '16.37',
                        '16.47', '16.57', '17.07', '17.17', '17.27', '17.37', '17.47', '17.57',
                        '18.07', '18.17', '18.27', '18.37', '18.47', '18.57', '19.07', '19.17',
                        '19.25', '19.33', '19.45', '19.53', '20.05', '20.25', '20.45'
                    ]

            times_gat = [
                        '7.01', '7.11', '7.21', '7.31', '7.41', '7.51', '8.01', '8.11', '8.21', '8.31',
                        '8.41', '8.51', '9.01', '9.11', '9.16', '9.31', '9.51', '10.11', '10.31', '10.51',
                        '11.11', '11.31', '11.51', '12.11', '12.31', '12.51', '13.11', '13.31', '13.51',
                        '14.11', '14.31', '14.51', '15.11', '15.31', '15.51', '16.11', '16.31', '16.51',
                        '17.01', '17.11', '17.21', '17.31', '17.41', '17.51', '18.01', '18.11', '18.21',
                        '18.31', '18.41', '18.51', '19.01', '19.11', '19.21', '19.31', '19.41', '19.51',
                        '20.01', '20.12', '20.32', '20.52'
                    ]

        elif current_day_of_week == "Saturday":
            #if current day = saturday:
            times_duf = [
                        '7.05', '7.25', '7.45', '8.05', '8.25', '8.45', '9.13', '9.28', '9.43',
                        '9.58', '10.13', '10.28', '10.43', '10.58', '11.13', '11.28', '11.43',
                        '11.58', '12.13', '12.28', '12.43', '12.58', '13.13', '13.28', '13.43',
                        '13.58', '14.13', '14.28', '14.43', '14.58', '15.13', '15.28', '15.43',
                        '15.58'
                    ]

            times_gat = [
                        '7.11', '7.31', '7.51', '8.11', '8.31', '8.51', '9.11', '9.31', '9.51',
                        '10.11', '10.31', '10.51', '11.11', '11.31', '11.51', '12.11', '12.31',
                        '12.51', '13.11', '13.31', '13.51', '14.11', '14.31', '14.51', '15.11',
                        '15.31', '15.51'
                    ]
        else:
            # Assuming there are no buses on Sundays and other days
            times_gat = []
            times_duf = []

        # Current time
        current_time = datetime.now().strftime("%H.%M")

        # Convert the times in the list to datetime objects for comparison
        times_datetime_duf = [datetime.strptime(time, "%H.%M") for time in times_duf]

        # Convert current time to datetime object
        current_time_datetime = datetime.strptime(current_time, "%H.%M")

        # Find the next three buses
        next_buses_duf = []
        for bus_time in times_datetime_duf:
            if bus_time > current_time_datetime:
                next_buses_duf.append(bus_time.strftime("%H.%M"))
                if len(next_buses_duf) == 3:
                    break

        # Convert the times in the list to datetime objects for comparison
        times_datetime_gat = [datetime.strptime(time, "%H.%M") for time in times_gat]

        # Find the next three buses
        next_buses_gat = []
        for bus_time in times_datetime_gat:
            if bus_time > current_time_datetime:
                next_buses_gat.append(bus_time.strftime("%H.%M"))
                if len(next_buses_gat) == 3:
                    break

        
        print(str(next_buses_gat))
        print(str(next_buses_duf))            

        user_input = tracker.latest_message.get('text')
        create_message(text_message=user_input + "\n" + "Current time:" +str(current_time) + "\n" + "Next Busses from Uni/Dufourstrasse to St. Gallen Bahnhof: "+ str(next_buses_duf) + "\n" + "Next Busses from Uni/Gatterstrasse to St. Gallen Bahnhof: "+ str(next_buses_gat))
        
        thread_messages = run_thread()
        # Extract the assistant's reply
        assistant_reply = thread_messages.data[0].content[0].text.value
        print(assistant_reply)

        dispatcher.utter_message(text=assistant_reply)


        
        return [FollowupAction('action_listen')]          