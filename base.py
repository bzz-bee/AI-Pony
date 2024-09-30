from concurrent.futures import ProcessPoolExecutor, wait
import wave, logging, random, os, fakeyou, requests, prompts
from time import sleep
import soundfile as sf
from fakeyou import FakeYou
from objects import *
from exception import *
from openai import OpenAI
client = OpenAI(
api_key = ""
)

#Settup up logging
logging.basicConfig(filename='test.log', encoding='utf-8', level=logging.DEBUG)

#set up fakeyou
token_list = {"Rainbow Dash": "weight_21arwhqhkg5d0nbe5ex7yj6br",
          "Applejack": "weight_tv7k02rkycj4jta9hqttm0s4r",
          "Pinkie Pie": "weight_eejesc1m4pyn8vb4bc08dqnkj",
          "Rarity": "weight_4j661zfzd3wm7sh3ks7eghx3w",
          "Fluttershy":"weight_fc61hzs4exsc9pj6g1x3xh9mv",
          }
            
#Instructions for ChatGPT
base_prompt = """
    You are to create scripts based on a topic.
    Make sure you are in character.
    You are to act like the character you are given. 
    Do not do any actions, only speak.
    The script must be over 10 lines long, but under 15. 
    Make the conversation dumb and funny.
"""
# prompts in prompts.py
p = prompts.prompts

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
        response = reply.choices[0].message.content # type: ignore
        response = response.replace("\n\n","\n")
        response = response.split("\n")
        logging.info("Script Generation Finished")

        return response
    except Exception as e:
        logging.error(f"Error occurred in chat_gen: {e}")
        return None

#Create the voice using fakeyou.py
def gen_voice(text, ttsModelToken, pos):
    try:
        logging.info("Voice Request Started")
        for _ in range(10):
            Fy = FakeYou(ttsModelToken)
            for t in range(50):
                sleep(5)
                job = FakeYou.make_tts_job(Fy, text, ttsModelToken)
                logging.info("Voice Request Finished")
                for t in range(50):
                    sleep(5)
                    output = FakeYou.tts_poll(Fy, job)
                    logging.info("Audio Download Started")
                    for t in range(50):
                        sleep(5)
                        if output != None:
                            file_path = f"speech{pos}.wav"
                            with open(file_path, "wb") as f:
                                    f.write(output.content)
                            return pos, file_path
                        for t in range(50):
                            sleep(5)

        logging.error("Download Failed: Unable to download audio after 50 attempts")
    except Exception as e:
        logging.error(f"Error occurred in gen_voice: {e}")
        return None, None
    finally:
        logging.info("Audio Download Finished")

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
        rand_prompt = random.choice(p)
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
        with ProcessPoolExecutor(3) as executor:
            for line in script:
                if line.split(":")[0] in token_list.keys():
                    ttsModelToken = token_list[line.split(":")[0]].strip()
                    text = line.split(":")[1].strip()
                    speaker = line.split(":")[0].strip()
                    pos = script.index(line)
                    futures.append(executor.submit(gen_voice, text, ttsModelToken, pos))

        
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