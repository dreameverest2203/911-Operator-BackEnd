from itertools import tee
from flask import Flask, request
from flask_cors import CORS, cross_origin


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
        return request.method
