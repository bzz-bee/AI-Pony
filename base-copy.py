from concurrent.futures import ThreadPoolExecutor, wait
from time import sleep
import soundfile as sf
import wave, logging, random, os, fakeyou, requests, json
from fakeyou import FakeYou
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
token_list = {"Rainbow Dash": "weight_wd1zz2z8av48j9k7z3dtkg58j",
          "Applejack": "weight_a24e7sx6qgqpwamjsff3b3vef",
          "Pinkie Pie": "weight_xzdr5a4cqhakdkshc96r32nv3",
          "Rarity": "weight_4j661zfzd3wm7sh3ks7eghx3w",
          "Fluttershy":"weight_25rdhte22qb0n6xtzk0h6s4xj",
          "Spike":"weight_p0t7d8tqk35v6q8a50n5d2vke"}

            
#Set up the base prompt
base_prompt = """
    You are to create scripts. 
    You will be giving the topic and who to act like. 
    Make sure you are in character.
    You are the act like the person you are given. 
    You dont need actions just what they say.
    Dont do any actions.
    Make sure the script is over 10 lines long, but under 15.
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
        
        fy = fakeyou.FakeYou()
        try:
            fy.login(username="", password="")
        except fakeyou.exception.InvalidCredentials:
            print("Login failed")
            exit()
        print("Logged in")

        futures = []
        with ThreadPoolExecutor() as executor:
            for line in script:
                if line.split(":")[0] in token_list.keys():
                    ttsModeltoken = token_list[line.split(":")[0]].strip()
                    text = line.split(":")[1].strip()
                    speaker = line.split(":")[0].strip()
                    pos = script.index(line)
                    futures.append(executor.submit(FakeYou.make_tts_job, ttsModelToken, text))

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
