from transformers import AutoTokenizer, AutoModelForTokenClassification
from transformers import pipeline
from itertools import tee
from flask import Flask, request
# from flask_cors import CORS, cross_origin
from google.cloud import speech
from google.cloud import language_v1
from google.protobuf.json_format import MessageToDict, MessageToJson
import io
import json
import os

os.environ[
    "GOOGLE_APPLICATION_CREDENTIALS"
] = "friendly-maker-340500-0a1a144d21e5.json"
speechClient = speech.SpeechClient()
languageClient = language_v1.LanguageServiceClient()


tokenizer = AutoTokenizer.from_pretrained("dslim/bert-base-NER")
model = AutoModelForTokenClassification.from_pretrained("dslim/bert-base-NER")

nlp = pipeline("ner", model=model, tokenizer=tokenizer)
example = "14305 San Pasqual Valley Road in Escondido another chair from property Department of Public Utilities regarding material."

ner_results = nlp(example)
print(ner_results)

type_ = language_v1.Document.Type.PLAIN_TEXT
language = "en"
encoding_type = language_v1.EncodingType.UTF8

document = {"content": example, "type_": type_, "language": language}
response = languageClient.analyze_entities(
    request={"document": document, "encoding_type": encoding_type}
)
responseDict = dict()
for entity in response.entities:
    # print(entity)
    if language_v1.Entity.Type(entity.type_).name == "ADDRESS":
        print(entity._pb.mentions[0].text.content)