import asyncio
import datetime
from multiprocessing import Manager
import os
from typing import Dict

from speech_recognition import Recognizer, Microphone, RequestError, UnknownValueError

OUTPUT_DIR = "/Users/phildan/Dev/Navel/RASA_chatgpt"
ABS_PATH = "/Users/phildan/Dev/Navel/RASA_chatgpt/actions/service.json"

class VoiceListener:
    def __init__(self, shared_dict: Dict):
        self.RECOGNIZER = Recognizer()
        self.RECOGNIZER.dynamic_energy_threshold = False
        self.shared_dict = shared_dict

        # Initialize 'stop_record' key in the shared dictionary
        self.shared_dict['stop_record'] = False

    def stop(self):
        self.shared_dict['stop_record'] = True

    async def listen(self):
        with Microphone() as source:
            print("Say something...")
            self.RECOGNIZER.adjust_for_ambient_noise(source)

            while not self.shared_dict['stop_record']:
                audio = self.RECOGNIZER.listen(source)
                try:
                    recognized_text = self.RECOGNIZER.recognize_google_cloud(
                        audio, credentials_json=ABS_PATH
                    )
                    #print(recognized_text)
                    return recognized_text

                except UnknownValueError as e:
                    print(f"Google Cloud Speech could not understand audio; {e}")
                    return None
                except RequestError as e:
                    print(f"Could not request results from Google Cloud Speech service; {e}")
                    return None

            print("Listener stopped.")
            return None

    async def start(self):
        try:
            return await self.listen()
        except KeyboardInterrupt:
            pass

if __name__ == '__main__':
    with Manager() as manager:
        # Create a shared dictionary
        shared_dict = manager.dict({})
        # Create and start a process
        listener = VoiceListener(shared_dict)
        asyncio.run(listener.start())
