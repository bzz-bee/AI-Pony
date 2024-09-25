from concurrent.futures import ThreadPoolExecutor, wait
from cookies import get_cookies
from time import sleep
import soundfile as sf
import openai
import wave
import aiohttp
import asyncio
import os
import uuid
import requests
import logging

##Below is code from base.py
#Set up logging
logging.basicConfig(filename='test.log', encoding='utf-8', level=logging.DEBUG)

#Set up the base prompt
base_prompt = """
    You are to create scripts. 
    You will be giving the topic and who to act like. 
    Make sure you are in character.
    You are the act like the person you are given. 
    You dont need actions just what they say.
    Dont do any actions.
    Make sure the script is over 10 lines long, but under 15.
    Format is: person: "what they say" 
    Keep everything dumb and stupid.
"""

#Set up the topics
prompts = [
    "Rainbow Dash, Applejack, Rainbow Dash says Undertale is gay",
    "Rainbow Dash, Applejack, Applejack says she hates apples",
    "Rainbow Dash, Applejack, Applejack and Rainbow Dash are fighting over which Linux distro is best",
    "Rainbow Dash, Applejack, Rainbow Dash says she loves Applejack",
]

#Create the script using the OpenAI API
def chat_gen(script, content):
    try:
        logging.info("Script Generation Started")
        reply = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": script},
                {"role": "user", "content": content},
            ]
        )

        # Cleanup of the response 
        if 'choices' not in reply:
            logging.error("Script Generation Failed: 'choices' not in reply")
            return None

        response = reply['choices'][0]['message']['content'] # type: ignore
        response = response.replace("\n\n","\n")
        response = response.split("\n")
        logging.info("Script Generation Finished")

        return response
    except Exception as e:
        logging.error(f"Error occurred in chat_gen: {e}")
        return None



#set up voices (voices.py)

tokens = {"Rainbow Dash": "weight_wd1zz2z8av48j9k7z3dtkg58j",
          "Applejack": "weight_a24e7sx6qgqpwamjsff3b3vef",
          "Twilight Sparkle": "",
          "Pinkie Pie": "weight_xzdr5a4cqhakdkshc96r32nv3",
          "Rarity": "weight_4j661zfzd3wm7sh3ks7eghx3w",
          "Fluttershy":"weight_25rdhte22qb0n6xtzk0h6s4xj",
          "Spike":"weight_p0t7d8tqk35v6q8a50n5d2vke"}

headers = {
    "content-type": "application/json",
    "credentials": "include",
    "cookie": f"session={get_cookies()}"
}


def get_models_list(path: str = "./"):
    """Request for a list of models and save it in path/models_list.txt"""
    try:
        response = requests.get("https://api.fakeyou.com/tts/list")
        response.raise_for_status()
        with open(os.path.join(path, "models_list.txt"), "w") as file:
            file.write(str(response.content))
    except requests.exceptions.RequestException as e:
        print(f"Request failed: {e}")


async def make_tts_request(session, character: str, phrase: str) -> str:
    """Asynchronous request for speech synthesis."""
    try:
        print("Making request...")
        async with session.post(
            url="https://api.fakeyou.com/tts/inference",
            json={
                "tts_model_token": tokens.get(character.lower()),
                "uuid_idempotency_token": str(uuid.uuid4()),
                "inference_text": phrase
            },
            headers=headers
        ) as response:
            response.raise_for_status()
            job_token = (await response.json()).get("inference_job_token")
            if job_token:
                print(f"Job token: {job_token}")
                return job_token
            else:
                print("Error: No job token in response.")
    except aiohttp.ClientError as e:
        print(f"Request failed: {e}")
    return None


async def poll_tts_status(session, inference_job_token: str, delay: float = 2, max_attempts: int = 50) -> str:
    """Asynchronous survey of the status of a request for speech synthesis and obtaining a link to an audio file."""
    try:
        print("Polling request...")
        base_url = "https://storage.googleapis.com/vocodes-public"
        attempts = 0
        while attempts < max_attempts:
            await asyncio.sleep(delay)
            attempts += 1
            async with session.get(f"https://api.fakeyou.com/tts/job/{inference_job_token}", headers=headers) as response:
                response.raise_for_status()
                json_response = await response.json()
                print(f"Polling attempt: {attempts}")
                if json_response["state"]["maybe_public_bucket_wav_audio_path"]:
                    audio_path = base_url + json_response["state"]["maybe_public_bucket_wav_audio_path"]
                    print(f"Audio file ready: {audio_path}")
                    return audio_path
                print("Pending...")
        print("Error: max attempts reached")
    except aiohttp.ClientError as e:
        print(f"Polling failed: {e}")
    return None


async def download_audio(session, url: str, output_path: str):
    """Asynchronous download of an audio file by url"""
    try:
        async with session.get(url) as response:
            response.raise_for_status()
            with open(output_path, "wb") as f:
                f.write(await response.read())
            print(f"Saved audio file to: {output_path}")
    except aiohttp.ClientError as e:
        print(f"Download failed: {e}")


async def fetch_and_save_audio(session, character: str, phrase: str, output_path: str, filename: str):
    """Asynchronous receipt and downloading of a file"""
    job_token = await make_tts_request(session, character, phrase)
    if job_token:
        audio_url = await poll_tts_status(session, job_token)
        if audio_url:
            output_path_audio = os.path.join(output_path, filename)
            await download_audio(session, audio_url, output_path_audio)

