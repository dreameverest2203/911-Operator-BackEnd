from itertools import tee
from flask import Flask, request
from flask_cors import CORS, cross_origin
from google.cloud import speech
from google.cloud import language_v1
from google.protobuf.json_format import MessageToDict, MessageToJson
import io
import json

speechClient = speech.SpeechClient()
languageClient = language_v1.LanguageServiceClient()
app = Flask(__name__)
CORS(app)

text = """hi on medical I need to have the address of an emergency
I don't know the address it's the coffee being in Carmel Mountain
if there's somebody you can ask what the addresses I can go inside and ask
okay there was no fire has decided I guess the gas and the fire pit
okay there was no fire has decided I guess the gas and the fire pit yes I'm at 1207
call Mountain Road and then 3 number 296 is your telephone number
how old is a baby 7 months old male or female
female if she awake she was away she's crying and if she breathing 
yes she's booty know we should be too close to it or did 
she actually get burned by the Flames we were sitting around it 
to the pizza mother and the other people that we're 
with her sitting around at 2 and then all sober
but I'm not sure it it did the fire pit explode or what 
happened yeah I guess what I left the gas they must've exploded or 
something and it was a huge birthday flame and all the people that are 
sitting around it we're just and it but when they accept the waiting and 
no one was on fire so I seem to be Osburn if everybody safe and out of danger now
how many people are actually in heard her just a baby I think the baby out of the work
I can go to that for 5 people
but actually have Burns I don't know if they actually have burns the people work
on the cleaning of everything there can you ask me I'm I need to know because
I need to know how many ambulance has we have to send all these people
so they do babies injure 3 people with Burns please
hi Kelly this is Cynthia give you a heads up on Carmel Mountain it's multiple people
are burned that they were on the Coffee Bean at all sitting around one of those little
fires are not on fire fire superficial yeah okay so I don't have them okay thank you bye
"""


@app.route("/")
def hello():
    return text
    # return "Hello, World!"

@cross_origin()
@app.route("/transcribe", methods = ['GET', 'POST'])
def transcribe():
    if request.method == 'GET':
        return text
    if request.method == 'POST':
        file_bytes = request.files['myFile'].read()
        audio = speech.RecognitionAudio(content=file_bytes)
        config = speech.RecognitionConfig(
            encoding=speech.RecognitionConfig.AudioEncoding.LINEAR16,
            sample_rate_hertz=8000,
            language_code="en-US",
            # audio_channel_count=2
        )
        response = speechClient.recognize(config=config, audio=audio)
        speech_to_text = ""
        for result in response.results:
            # The first alternative is the most likely one for this portion.
            speech_to_text += result.alternatives[0].transcript
        return speech_to_text

@cross_origin()
@app.route("/recognize", methods = ['POST'])
def recognize_entities():
    text_content = request.form['transcription']
    type_ = language_v1.Document.Type.PLAIN_TEXT
    language = "en"
    encoding_type = language_v1.EncodingType.UTF8

    document = {"content": text_content, "type_": type_, "language": language}
    response = languageClient.analyze_entities(request = {'document': document, 'encoding_type': encoding_type})
    print(response)

    responseDict = dict()
    for entity in response.entities:
        if language_v1.Entity.Type(entity.type_).name == "ADDRESS":
            responseDict['address'] = MessageToDict(entity._pb)
    return json.dumps(responseDict)
