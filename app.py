from itertools import tee
from flask import Flask, request
from flask_cors import CORS, cross_origin
from google.cloud import speech, language_v1, storage
from google.cloud import translate_v2 as translate
from googleplaces import GooglePlaces, types, lang
import googlemaps
from google.protobuf.json_format import MessageToDict, MessageToJson
import io
import json
import os
import requests
import pdb
import time
from gensim import models
import nltk
from nltk.corpus import stopwords

nltk.download("stopwords")
from nltk.tokenize import word_tokenize
import numpy as np


word_to_vec = models.KeyedVectors.load_word2vec_format(
    "GoogleNews-vectors-negative300.bin.gz", binary=True
)
os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = "friendly-maker-340500-0a1a144d21e5.json"
speechClient = speech.SpeechClient()
languageClient = language_v1.LanguageServiceClient()
storage_client = storage.Client()
translate_client = translate.Client()
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
            # sample_rate_hertz=8000,
            language_code="en-US",
            audio_channel_count=2,
            # enable_separate_recognition_per_channel=True,
            enable_automatic_punctuation="noPunctuation" not in request.form,
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
    responseDict["location"] = "Not Found"
    for entity in response.entities:
        if language_v1.Entity.Type(entity.type_).name == "ADDRESS":
            responseDict["address"] = str(entity._pb.mentions[0].text.content)
            request_url = f"https://maps.googleapis.com/maps/api/geocode/json?key=AIzaSyCkQUJ2dXJ9z0EaM-NnVMlJJIrMbBt3yqg&address={str(entity._pb.mentions[0].text.content)}"
            response = requests.get(request_url)
            resp_json_payload = response.json()
            responseDict["address"] = resp_json_payload["results"][0]['formatted_address']

        if language_v1.Entity.Type(entity.type_).name == "LOCATION" and any(
            map(str.isdigit, str(entity._pb.mentions[0].text.content))
        ):
            responseDict["location"] = str(entity._pb.mentions[0].text.content)

    response = (
        responseDict["address"]
        if "address" in responseDict
        else responseDict["location"]
    )
    return json.dumps({"address": response})


@cross_origin
@app.route("/coordinates", methods=["POST"])
def get_loc():
    requested_location = "+".join(request.form["location"].split(" "))
    request_url = f"https://maps.googleapis.com/maps/api/geocode/json?key=AIzaSyCkQUJ2dXJ9z0EaM-NnVMlJJIrMbBt3yqg&address={requested_location}"
    response = requests.get(request_url)
    resp_json_payload = response.json()
    return resp_json_payload["results"][0]["geometry"]["location"] if len(resp_json_payload["results"]) > 0 else {'lat': 0, 'lng': 0}


@cross_origin
@app.route("/nearest", methods=["POST"])
def get_nearest():

    API_KEY = "AIzaSyCkQUJ2dXJ9z0EaM-NnVMlJJIrMbBt3yqg"
    google_places = GooglePlaces(API_KEY)
    gmaps = googlemaps.Client(API_KEY)

    lat, lng = request.form["lat"], request.form["lng"]
    hospital = google_places.nearby_search(
    lat_lng={"lat": lat, "lng": lng}, radius=10000, types=[types.TYPE_HOSPITAL]
    )
    fire = google_places.nearby_search(
        lat_lng={"lat": lat, "lng": lng}, radius=10000, types=[types.TYPE_FIRE_STATION]
    )
    police = google_places.nearby_search(
        lat_lng={"lat": lat, "lng": lng}, radius=10000, types=[types.TYPE_POLICE]
    )
    if len(hospital.places) > 0:
        hospital = {
            "name": hospital.places[0].name,
            "lat": float(hospital.places[0].geo_location["lat"]),
            "lng": float(hospital.places[0].geo_location["lng"]),
        }
        hospital["dist"] = gmaps.distance_matrix([{'lat': lat, 'lng': lng}], [{'lat': hospital['lat'], 'lng': hospital['lng']}])['rows'][0]['elements'][0]['distance']['text'].split(" ")[0]
    else:
        hospital = {}

    if len(fire.places) > 0:
        fire = {
            "name": fire.places[0].name,
            "lat": float(fire.places[0].geo_location["lat"]),
            "lng": float(fire.places[0].geo_location["lng"]),
        }
        fire["dist"] = gmaps.distance_matrix([{'lat': lat, 'lng': lng}], [{'lat': fire['lat'], 'lng': fire['lng']}])['rows'][0]['elements'][0]['distance']['text'].split(" ")[0]
    else:
        fire = {}

    if len(police.places) > 0:
        police = {
            "name": police.places[0].name,
            "lat": float(police.places[0].geo_location["lat"]),
            "lng": float(police.places[0].geo_location["lng"]),
        }
        police["dist"] = gmaps.distance_matrix([{'lat': lat, 'lng': lng}], [{'lat': police['lat'], 'lng': police['lng']}])['rows'][0]['elements'][0]['distance']['text'].split(" ")[0]
    else:
        police = {}
    
    di = {"hospital": hospital, "fire": fire, "police": police}
    print(di)
    return di


@cross_origin
@app.route("/emergency", methods=["POST"])
def get_emergency():
    emergencies = [
        "fire",
        "bleed",
        "confusion",
        "choke",
        "robbery",
        "accident"
    ]
    transcription = request.form["transcription"]
    transcription_tokens = word_tokenize(transcription)
    transcription_without_sw = list(
        set([word for word in transcription_tokens if not word in stopwords.words()])
    )

    emergency_vectors = [word_to_vec[emergency] for emergency in emergencies]
    vectorized_words = [
        word for word in transcription_without_sw if word in word_to_vec
    ]
    transcription_vectors = [word_to_vec[word] for word in vectorized_words]

    distance_sums = []

    for i, emergency_vector in enumerate(emergency_vectors):
        curr_sum = float("inf")
        for j, transcription_vector in enumerate(transcription_vectors):
            if np.linalg.norm(transcription_vector - emergency_vector) < curr_sum:
                print(emergencies[i], vectorized_words[j])
            curr_sum = min(
                curr_sum, np.linalg.norm(transcription_vector - emergency_vector)
            )
        distance_sums.append(curr_sum)
    emergency = emergencies[np.argmin(distance_sums)]
    distance_sums = np.array(distance_sums)
    distance_sums += 0.01
    distance_sums = 1/distance_sums
    distance_sums = (distance_sums / np.sum(distance_sums)) * 100
    distance_sums = [(distance_sums[i], emergencies[i]) for i in range(len(distance_sums))]
    distance_sums.sort(reverse = True)
    distance_sums = [(str(a), b) for (a,b) in distance_sums]
    print(distance_sums)
    return json.dumps({"emergency": emergency, "scores": distance_sums})

@cross_origin
@app.route("/translate", methods=["POST"])
def translate():
    text = request.form["transcription"]
    result = translate_client.translate(text, target_language="es")
    return json.dumps({"text": result['translatedText']})
