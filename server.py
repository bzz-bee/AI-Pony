from flask import Flask, send_file
import voices
import os
app = Flask(__name__)

voices.cleanup()
@app.route("/audio", methods=["GET"])
def audio():
    voices.run()
    if os.path.exists("output.wav"):
        return send_file("output.wav")
    else:
        return "Error"

@app.route("/script", methods=["GET"])
def script():
    return send_file("script.txt")

app.run(threaded=True)