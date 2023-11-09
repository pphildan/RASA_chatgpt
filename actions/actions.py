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
import time
import random

ALLOWED_FROM = ["7", "8", "9", "10", "11", "12", "1", "2", "3", "4", "5", "6"]
ALLOWED_TO = ["7", "8", "9", "10", "11", "12", "1", "2", "3", "4", "5", "6"]

os.environ['OPENAI_API_KEY'] = 'your_key'
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

empty_thread = openai.beta.threads.create()
thread_id = empty_thread.id
asst_id = 'your_assist'


# filename='conversation_history.json'
# conversation_history = [{"role": "system", "content": ""}]
# with open(filename, 'w') as f:
#     json.dump(conversation_history, f)


# info_string = ("You are now a social robot named Navel, situated within a university building called SQUARE. "
#                "You have the capability to answer questions regarding SQUARE and book a group room for a maximum of 2 hours today. Answer with maximum of 25 words! "
#                "Here is some information that might be useful for potential queries: "
#                "\n\nThe building’s operating hours are as follows:\n"
#                "- Monday to Friday: 7:00 AM - 9:00 PM\n"
#                "- Saturday: 7:00 AM - 4:00 PM\n"
#                "- Sunday and public holidays: closed\n"
#                "\nThe cafe's opening hours are:\n"
#                "- Monday to Friday: 8:00 AM - 5:00 PM\n"
#                "- Saturday: 8:00 AM - 4:00 PM\n"
#                "\nThe group rooms are located on the first floor on the left side.\n"
#                "\nHere are some exciting facts about SQUARE:\n"
#                "- It was designed by architect Sou Fujimoto and financed by the HSG Foundation.\n"
#                "- SQUARE was constructed in a record time of two years, from November 2019 to November 2021.\n"
#                "- The building serves as a test environment for innovative teaching and learning formats, featuring a flexible space concept for experimental and cross-generational education.\n"
#                "- The project 'Open Grid - choices for tomorrow' by Sou Fujimoto is based on the architectural principle of the square, integrating concepts of a station, monastery, and workshop.\n"
#                "- The total construction costs were CHF 53 million, with around 63% of the services provided by companies from the Eastern Switzerland region.\n"
#                "- The building’s design resembles a large notebook, providing flexible spaces and walls for testing and applying innovative teaching formats.\n"
#                "- Its cube-like structure consists of a grid with blocks measuring 10x10x5 meters, with some areas featuring half room heights for additional space and a harmonious silhouette.\n"
#                "- The facade is made of transparent glass that visually adapts to the seasons, ensuring a healthy indoor climate with daylight and extensive views.\n"
#                "- The building’s heating and cooling systems are powered by heat pumps, utilizing 65 probes drilled about 200 meters deep, divided into two fields for optimal energy efficiency.\n"
#                "- A photovoltaic system with a capacity of 67 kW has been installed to cover the building’s energy needs, potentially meeting 50-60% of its annual energy requirement.\n"
#                "- A total of 6,000 m3 of concrete was used in the construction, including eco-friendly options like Holcim Evopact plus and Holcim Evopact ZERO, which help to reduce carbon emissions by 10%.\n"
#                "\nIMPORTANT: If a user expresses the intention to book a room, respond exclusively with the following JSON format: {'intent': 'room_booking'}.")




message_sent = False

class ActionConfirmBooking(Action):

    def name(self) -> Text:
        return "action_confirm"

    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:

        von = tracker.get_slot("from")
        to = tracker.get_slot("to")
        name = tracker.get_slot("name")
        avail = tracker.get_slot("available")
        if von is not None and to is not None and name is not None and avail is True:
            dispatcher.utter_message(text=f"Perfect, I booked a room from {von} to {to} for {name}!")
            global message_sent
            message_sent = False
        return [AllSlotsReset(), ActiveLoop(None)]

class ActionConfirmBooking(Action):

    def name(self) -> Text:
        return "action_confirm_possibility"

    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:

  
        actions = ['Action 3', 'Action 3', 'Action 3']
        selected_action = random.choice(actions)

        # Perform an action based on the selected action
        if selected_action == 'Action 1':
            dispatcher.utter_message(text=f"All right, today there are still free rooms all day from 7 am to 6 pm. The maximum duration for a booking is 2 hours.")
            return [FollowupAction("booking_form")]
        elif selected_action == 'Action 2':
            dispatcher.utter_message(text=f"Today we have left an available room from 2 to 6 pm. You can book a maximum of 2 hours time slot.")
            return [FollowupAction("booking_form")]
        elif selected_action == 'Action 3':
            dispatcher.utter_message(text=f"Unfortunately we have no room left today. Sorry for that. Can I assist you with something else?")
            return [AllSlotsReset(), ActiveLoop(None),FollowupAction('action_listen')]

class ActionChatWithGPT(Action):

    def name(self) -> Text:
        return "action_chat_with_gpt"

    def _create_message(self,text_message):
        thread_message = openai.beta.threads.messages.create(
            thread_id,
            role="user",
            content=text_message)                  
        return None

    def _run_thread(self):
        run = client.beta.threads.runs.create(
            thread_id=thread_id,
            assistant_id=asst_id)
    
        while True:
            time.sleep(0.4)  # Sleep for 500 milliseconds
            r_run = client.beta.threads.runs.retrieve(
            thread_id=thread_id,
            run_id=run.id)
            if r_run.status == 'completed':
                thread_messages = client.beta.threads.messages.list(thread_id, limit=2)
                break
    
        return thread_messages   
    
    async def run(self, dispatcher: CollectingDispatcher,
                  tracker: Tracker,
                  domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:

        # Get the latest user message
        user_input = tracker.latest_message.get('text')

        self._create_message(user_input)

        thread_messages = self._run_thread()
        

    
        # Extract the assistant's reply
        assistant_reply = thread_messages.data[0].content[0].text.value
    

        try:
            assistant_reply = assistant_reply.replace("'", '"') 
            json_obj = json.loads(assistant_reply)
            # Check if the response contains the "room_booking" intent
            if json_obj['intent'] == 'room_booking':
                dispatcher.utter_message(text="You can book one of our group rooms today for 2 hours between 7am and 6 pm.")

                return [FollowupAction("booking_form")]
                    
        except json.JSONDecodeError:
            # The assistant's reply is not a valid JSON string
                
            dispatcher.utter_message(text=assistant_reply)

        return []    

class ActionResetSlots(Action):

    def name(self) -> Text:
        return "action_reset_slots"

    def run(self, dispatcher: CollectingDispatcher, tracker: Tracker, domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
        dispatcher.utter_message(text="All right, how else can I help?")
        return [AllSlotsReset(), ActiveLoop(None)]


class ValidateSimplePizzaForm(FormValidationAction):
    def name(self) -> Text:
        return "validate_booking_form"

    def validate_from(
        self,
        slot_value: Any,
        dispatcher: CollectingDispatcher,
        tracker: Tracker,
        domain: DomainDict,
    ) -> Dict[Text, Any]:
        """Validate `from` value."""

        if slot_value.lower() not in ALLOWED_FROM:
            dispatcher.utter_message(text=f"You can only book a room from 7am to 8pm")
            return {"from": None}
        #dispatcher.utter_message(text=f"OK! You want to have a {slot_value} pizza.")
        return {"from": slot_value}

    def validate_to(
        self,
        slot_value: Any,
        dispatcher: CollectingDispatcher,
        tracker: Tracker,
        domain: DomainDict,
    ) -> Dict[Text, Any]:
        """Validate `to` value."""

        if slot_value not in ALLOWED_TO:
            dispatcher.utter_message(text=f"You can only book a room from 7am to 8pm")
            return {"to": None}
        #dispatcher.utter_message(text=f"OK! You want to have a {slot_value} pizza.")
        return {"to": slot_value}


    async def run(self, dispatcher, tracker, domain):
        von = tracker.get_slot("from")
        to = tracker.get_slot("to")
        global message_sent
        if von is not None and to is not None:
            if not message_sent:
                dispatcher.utter_message(text=f"Great we have a room from {von} to {to}.")
                message_sent = True
                return [SlotSet("available", True)]
            else:
                # If the message has already been sent, just return the available slot
                return [SlotSet("available", True)]
        else:
            
            return [SlotSet("available", False)]

