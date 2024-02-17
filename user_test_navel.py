import requests
import os
from openai import OpenAI
import openai
import re
import csv
import json
from voice_listener2 import VoiceListener


from multiprocessing import Manager
import os
import time
from typing import Dict
import asyncio
from speech_recognition import Recognizer, Microphone, RequestError, UnknownValueError



config_file = 'actions/config.json'
with open(config_file, 'r') as f:
    config = json.load(f)

os.environ['OPENAI_API_KEY'] = config['api_key']
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

empty_thread = openai.beta.threads.create()
thread_id = empty_thread.id
asst_id = config['assistant']

def send_text_to_server(text, url="http://172.20.10.2:5000/speak"):
    try:
        # Sending the text as a JSON object
        headers = {'Content-Type': 'application/json'}
        data = json.dumps({"text": text})
        response = requests.post(url, headers=headers, data=data)
        return response.text
    except requests.RequestException as e:
        return f"An error occurred: {e}"


def send_message_to_rasa(text_message):
    url = "http://localhost:5005/webhooks/rest/webhook"
    payload = {"sender": "user", "message": text_message}
    response = requests.post(url, json=payload)
    if response.status_code == 200:
        return response.json()
    return None

def text_to_speech(text):
    # Set your OpenAI API key here
    api_key = os.environ['OPENAI_API_KEY']
    # Set the endpoint URL
    url = "https://api.openai.com/v1/audio/speech"
    # Set the headers
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }
    # Set the data payload
    data = {
        "model": "tts-1",
        "input": text,
        "voice": "alloy"
    }

    # Make the POST request to the OpenAI API
    response = requests.post(url, headers=headers, json=data)

    # Check if the request was successful
    if response.status_code == 200:
        # Play the audio in the notebook
        with open("speech.mp3", "wb") as f:
            f.write(response.content)
        os.system("afplay " + "speech.mp3")
        
    else:
        print(f"Request failed with status code {response.status_code}: {response.text}")
        return None

#txt_file_path = 'conversation_history.txt'








if __name__ == '__main__':
    name = input("Name of participant: ")
    date = input("Date of user test: ")
    txt_file_path = f'/Users/phildan/Dev/Navel/user_tests/conversation_history_{name}.txt'
    # Function to append a single line to the txt file
    def append_to_txt(file_path, line):
        with open(file_path, 'a', encoding='utf-8') as file:
            file.write(line + '\n')

    # Create the txt file if it does not exist
    if not os.path.isfile(txt_file_path):
        with open(txt_file_path, 'w', encoding='utf-8') as file:
            file.write("Participant: " + name + '\n')
            file.write("Date: " + date + '\n')
    else:
        with open(txt_file_path, 'a', encoding='utf-8') as file:
            file.write('\n')
            file.write("Participant: " + name + '\n')
            file.write("Date: " + date + '\n')


    with Manager() as manager:
        shared_dict = manager.dict({'stop_record': False})
        listener = VoiceListener(shared_dict)

        while True:

            
            user_message = asyncio.run(listener.start())

            if user_message:
                print("You: " + user_message)
                
            
                append_to_txt(txt_file_path, "User: " + user_message)

            else:
                continue
            
        
            if user_message.lower() == 'stop.' or user_message.lower() == 'stop':
                break
            bot_responses = send_message_to_rasa(user_message)
            if bot_responses:
                for response in bot_responses:
                    if 'text' in response:
                        #print("Bot:", "." )
                        pattern = r"【.*$"
                        cleaned_response = re.sub(pattern, '', response['text'])
                        append_to_txt(txt_file_path, "Bot: " + cleaned_response)
                        #response_text = send_text_to_server(cleaned_response)
                        print("Bot:", cleaned_response)

                        #chars = len(cleaned_response)
                        #x = int(chars/25)
                        #time.sleep(x)

          



# while True:

#     user_message = asyncio.run(listener.start())
#     print("You: " + user_message)

    # append_to_txt(txt_file_path, "User: " + user_message)
        
    # if user_message.lower() == 'stop.' or user_message.lower() == 'stop':
    #     break
    # bot_responses = send_message_to_rasa(user_message)
    # if bot_responses:
    #     for response in bot_responses:
    #         if 'text' in response:
    #             print("Bot:", "." )
    #             pattern = r"【.*$"
    #             cleaned_response = re.sub(pattern, '', response['text'])
    #             append_to_txt(txt_file_path, "Bot: " + cleaned_response)
    #             response_text = send_text_to_server(cleaned_response)
                

                


   