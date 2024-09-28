from concurrent.futures import ThreadPoolExecutor, wait
from time import sleep
import soundfile as sf
import wave, logging, random, os, fakeyou, requests, json
from objects import *
from exception import *
from openai import OpenAI
from openai import Client
client = OpenAI(
api_key = ""
)

#Settup up logging
logging.basicConfig(filename='test.log', encoding='utf-8', level=logging.DEBUG)

#set up fakeyou
fy = fakeyou.FakeYou()
try:
  fy.login(username="", password="")
except fakeyou.exception.InvalidCredentials:
  print("Login failed")
  exit()
print("Logged in")

tokens = {"Rainbow Dash": "weight_wd1zz2z8av48j9k7z3dtkg58j",
          "Applejack": "weight_a24e7sx6qgqpwamjsff3b3vef",
          "Twilight Sparkle": "",
          "Pinkie Pie": "weight_xzdr5a4cqhakdkshc96r32nv3",
          "Rarity": "weight_4j661zfzd3wm7sh3ks7eghx3w",
          "Fluttershy":"weight_25rdhte22qb0n6xtzk0h6s4xj",
          "Spike":"weight_p0t7d8tqk35v6q8a50n5d2vke"}

class FakeYou():
	
    """ A class to interact with FakeYou API for various operations like login, 
    voice listing, text-to-speech conversion, and more. """

    def __init__(self, verbose: bool = False):
        """ Initializes the FakeYou instance. """
        self.baseurl = "https://api.fakeyou.com/"
        self.headers = {
            "accept": "application/json",
            "content-Type": "application/json"
        }
        self.session = requests.Session()
        self.session.headers = self.headers
        if verbose:
            logging.basicConfig(level=logging.DEBUG)
        logging.debug("Session created")
	
    def _handle_response(self, response, success_codes=[200], fail_exceptions={}):
        """ Generic handler for API responses. """
        if response.status_code in success_codes:
            return response.json()
        else:
            exception = fail_exceptions.get(response.status_code, RequestError)
            raise exception()

    def login(self, username, password):
        """ Logs in to the FakeYou API and returns the session information. """
        login_payload = {"username_or_email": username, "password": password}
        logging.debug("Sending Login request")
        response = self.session.post(self.baseurl + "login", json=login_payload)
        logging.debug("Login request sent")
        fail_exceptions = {401: InvalidCredentials, 429: TooManyRequests}
        return self._handle_response(response, fail_exceptions=fail_exceptions)

    def list_voices(self):
        """
        Retrieves a list of available voices.
        """
        response = self._get_request("tts/voices")
        return response.get('voices', [])

    def list_voice_categories(self):
        """
        Retrieves a list of voice categories.
        """
        response = self._get_request("tts/categories")
        return response.get('categories', [])

    def get_voices_by_category(self, category_token):
        """
        Retrieves voices available in a specific category.
        """
        response = self._get_request(f"tts/voices/{category_token}")
        return response.get('voices', [])

    def _get_request(self, endpoint):
        """
        Performs a GET request to the specified API endpoint and handles responses.
        """
        response = self.session.get(url=self.baseurl + endpoint)
        if response.status_code == 200:
            return response.json()
        else:
            raise RequestError(f"Failed to fetch data from {endpoint}: {response.text}")
	
#make_tts_job

    def make_tts_job(self, text: str, tokens: str):
        """ Creates a text-to-speech job and returns its token. """
        payload = {
            "uuid_idempotency_token": str(uuid4()),
            "tts_model_token": tokens,
            "inference_text": text
        }
        response = self.session.post(
            url=self.baseurl + "tts/inference", 
            data=json.dumps(payload)
        )
        fail_exceptions = {400: RequestError, 429: TooManyRequests}
        return self._handle_response(response, fail_exceptions=fail_exceptions)
	
    def tts_poll(self, poll_id):
        """
        Polls the status of a text-to-speech request.

        Args:
            poll_id (str): The ID of the TTS request to poll.

        Returns:
            dict: A dictionary containing the status and result of the TTS request.

        Raises:
            RequestError: If the request to the API fails.
        """
        endpoint = f"tts/poll/{poll_id}"
        response = self._get_request(endpoint)

        if 'status' in response:
            return response
        else:
            raise RequestError(f"Invalid response received for poll ID {poll_id}")

    def say(self, voice, text):
        """
        Converts text to speech using a specified voice.

        Args:
            voice (str): The token of the voice to use.
            text (str): The text to convert to speech.

        Returns:
            dict: A dictionary containing the poll ID for the TTS request.

        Raises:
            RequestError: If the TTS request fails.
        """
        data = {"voice": voice, "text": text}
        response = self.session.post(url=self.baseurl + "tts/say", json=data)

        if response.status_code == 200:
            return response.json()
        else:
            raise RequestError(f"TTS request failed: {response.text}")
	
    def tts_status(self, poll_id):
        """
        Retrieves the status of a text-to-speech conversion process.

        This method polls the current status of a TTS request using its unique ID,
        returning information about whether the TTS conversion is complete,
        and if completed, the URL to download the generated audio.

        Args:
            poll_id (str): The unique ID of the TTS request.

        Returns:
            dict: A dictionary with two keys: 'completed' (bool) indicating if the TTS 
                  conversion is finished, and 'download_url' (str or None) containing 
                  the URL to download the audio if conversion is complete.

        Raises:
            RequestError: If the polling request fails or returns an unexpected response.
        """
        poll_response = self.tts_poll(poll_id)

        if poll_response['status'] == 'done':
            return {
                'completed': True,
                'download_url': poll_response.get('download_url')
            }
        elif poll_response['status'] in ['in_progress', 'pending']:
            return {'completed': False, 'download_url': None}
        else:
            raise RequestError(f"Unexpected status received: {poll_response['status']}")

    def get_queue(self):
        """
        Retrieves the current status of the TTS and W2L processing queues.

        This method provides insights into the workload and pending tasks
        in the FakeYou conversion queues, useful for estimating wait times
        and overall system load.

        Returns:
            dict: A dictionary with details about the current queue status,
                  including number of pending conversions and average wait time.
        """
        response = self.session.get(f'{self.api_url}/queue')
        self._check_response(response)
        return response.json()

            
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

#Creates the script using the OpenAI API
def chat_gen(script, content):
    try:
        logging.info("Script Generation Started")
        reply = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": script},
                {"role": "user", "content": content},
            ]
        )
        print(reply.choices[0].message)

        #Cleanup of the response 
        #if 'choices' not in reply:
            #logging.error("Script Generation Failed: 'choices' not in reply")
            #return None

        response = reply.choices[0].message.content # type: ignore
        response = response.replace("\n\n","\n")
        response = response.split("\n")
        logging.info("Script Generation Finished")

        return response
    except Exception as e:
        logging.error(f"Error occurred in chat_gen: {e}")
        return None

#Creates the script file
def create_script(text, speaker, pos):
    try:
        logging.info("Script Creation Started")
        with open("script.txt", 'a') as f:
            d = sf.SoundFile(f"speech{pos}.wav")
            f.write(f'{speaker}:{text}:{(d.frames / d.samplerate)}\n')
        logging.info("Script Creation Finished")
    except FileNotFoundError:
        logging.error(f"File speech{pos}.wav not found.")
    except Exception as e:
        logging.error(f"An unexpected error occurred while creating script: {e}")

#Merges the audio files  
def merge_wav_files(file_list, output_filename):
    try:
        logging.info("Audio Merge Started")
        # Open first valid file and get details
        params = None
        for filename in file_list:
            try:
                with wave.open(filename, 'rb') as wave_file:
                    params = wave_file.getparams()
                    break
            except wave.Error:
                logging.warning(f"Skipping invalid file: {filename}")
                continue

        if params is None:
            logging.error("Audio Merge Failed: No valid files found in the list")
            return

        # Open output file with same details
        with wave.open(output_filename, 'wb') as output_wav:
            output_wav.setparams(params)

            # Go through input files and add each to output file
            for filename in file_list:
                try:
                    with wave.open(filename, 'rb') as wave_file:
                        output_wav.writeframes(wave_file.readframes(wave_file.getnframes()))
                except wave.Error:
                    logging.warning(f"Skipping invalid file: {filename}")
        logging.info("Audio Merge Finished")

    except Exception as e:
        logging.error(f"An unexpected error occurred in merge_wav_files: {e}")

#Cleans up file that will be made later
def cleanup():
    try:
        logging.info("Cleanup Started")
        for filename in os.listdir(os.getcwd()):
            if filename.startswith(("speech", "output", "script")):
                try:
                    os.remove(filename)
                    logging.info(f"Deleted file: {filename}")
                except Exception as e:
                    logging.error(f"Error deleting file {filename}: {e}")
        logging.info("Cleanup Finished")
    except Exception as e:
        logging.error(f"An unexpected error occurred during cleanup: {e}")

#Main function
def run():
    try:
        logging.info("Program Started")
        #Cleans up the files
        cleanup()

        #Chooses a random topic and creates the script
        rand_prompt = random.choice(prompts)
        script = chat_gen(base_prompt,rand_prompt)

        if script is None:
            logging.error("Script generation failed")
            return

        futures = []
        with ThreadPoolExecutor() as executor:
            for line in script:
                if line.split(":")[0] in tokens.keys():
                    voice_id = tokens[line.split(":")[0]].strip()
                    text = line.split(":")[1].strip()
                    speaker = line.split(":")[0].strip()
                    pos = script.index(line)

                    futures.append(executor.submit(FakeYou.make_tts_job, text, voice_id))

        wait(futures)

        for future in futures:
            pos, file_path = future.result()
            if file_path is not None:
                create_script(script[pos].split(":")[1].strip(), script[pos].split(":")[0].strip(), pos)

        #Check if all the speech.wav files are there
        for i in range(len(script)):
            if not os.path.isfile(f"speech{i}.wav"):
                logging.error(f"Audio file speech{i}.wav was not created correctly")
                return

        #Merges the audio files into one
        merge_wav_files([f"speech{i}.wav" for i in range(len(script))], "output.wav")

        #Cleans up the audio files
        for filename in os.listdir(os.getcwd()):
            if filename.startswith("speech"):
                try:
                    os.remove(filename)
                    logging.info(f"Removed file: {filename}")
                except Exception as e:
                    logging.error(f"Failed to remove file {filename}: {e}")

        logging.info("Program Finished")

    except Exception as e:
        logging.error(f"An unexpected error occurred in run: {e}")

x = 1
while True:
    run()
    if 'output.wav' in os.listdir(os.getcwd()):
        print(f"Run {x} is successful. Output.wav is created.")
    else:
        print(f"Run {x} is unsuccessful. Output.wav is not created.")
    x += 1
