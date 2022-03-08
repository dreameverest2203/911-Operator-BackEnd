from itertools import tee
from flask import Flask, request
from flask_cors import CORS, cross_origin
from google.cloud import speech, language_v1, storage
from google.protobuf.json_format import MessageToDict, MessageToJson
import io
import json
import os
import requests
import time

os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = "friendly-maker-340500-0a1a144d21e5.json"
speechClient = speech.SpeechClient()
languageClient = language_v1.LanguageServiceClient()
storage_client = storage.Client()
app = Flask(__name__)
CORS(app)


@app.route("/")
def hello():
    return "Hello, World!"


@cross_origin()
@app.route("/transcribe", methods=["GET", "POST"])
def transcribe():
    if request.method == "POST":
        output_filename = str(int(time.time())) + ".wav"
        bucket_name = "329s-asr"
        bucket = storage_client.bucket(bucket_name)
        blob = bucket.blob(output_filename)
        blob.upload_from_string(request.files["myFile"].read())

        gcs_uri = "gs://" + bucket_name + "/" + output_filename
        audio = speech.RecognitionAudio(uri=gcs_uri)
        config = speech.RecognitionConfig(
            encoding=speech.RecognitionConfig.AudioEncoding.LINEAR16,
            sample_rate_hertz=8000,
            language_code="en-US",
            audio_channel_count=2,
            enable_separate_recognition_per_channel=True,
        )
        operation = speechClient.long_running_recognize(config=config, audio=audio)

        print("Waiting for operation to complete...")
        response = operation.result(timeout=180)
        speech_to_text = ""
        for result in response.results:
            # The first alternative is the most likely one for this portion.
            speech_to_text += result.alternatives[0].transcript
        return speech_to_text


@cross_origin()
@app.route("/recognize", methods=["POST"])
def recognize_entities():
    text_content = request.form["transcription"]
    type_ = language_v1.Document.Type.PLAIN_TEXT
    language = "en"
    encoding_type = language_v1.EncodingType.UTF8

    document = {"content": text_content, "type_": type_, "language": language}
    response = languageClient.analyze_entities(
        request={"document": document, "encoding_type": encoding_type}
    )
    responseDict = dict()
    for entity in response.entities:
        if language_v1.Entity.Type(entity.type_).name == "LOCATION":
            print(entity._pb.mentions[0].text.content)
            if "address" not in responseDict:
                responseDict["address"] = ""
            responseDict["address"] += str(entity._pb.mentions[0].text.content) + " "
    return json.dumps(responseDict)

@cross_origin
@app.route('/coordinates', methods=["POST"])
def get_loc():
    requested_location = "+".join(request.form["location"].split(" "))
    response = requests.get(
        f"https://maps.googleapis.com/maps/api/geocode/json?key=AIzaSyCkQUJ2dXJ9z0EaM-NnVMlJJIrMbBt3yqg&address={requested_location}"
    )

    resp_json_payload = response.json()
    return resp_json_payload["results"][0]["geometry"]["location"]