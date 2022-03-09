from gensim import models
import nltk
from nltk.corpus import stopwords
nltk.download('stopwords')
from nltk.tokenize import word_tokenize
import numpy as np

word_to_vec = models.KeyedVectors.load_word2vec_format(
    'GoogleNews-vectors-negative300.bin.gz', binary=True)

def get_emergency(transcription):
    emergencies = ['fire', 'bleed', 'cut', 'burn', 'confusion', 'vomit', 'seizure', 'choke', 'unconscious', 'asthama', 'stroke', 'robbery', 'accident']
    transcription_tokens = word_tokenize(transcription)
    transcription_without_sw = list(set([word for word in transcription_tokens if not word in stopwords.words()]))
    
    emergency_vectors = [word_to_vec[emergency] for emergency in emergencies]
    transcription_vectors = [word_to_vec[word] for word in transcription_without_sw if word in word_to_vec]

    distance_sums = []

    for transcription_vector in transcription_vectors:
        curr_sum = float("inf")
        for emergency_vector in emergency_vectors:
            curr_sum = min(curr_sum, np.linalg.norm(transcription_vector-emergency_vector))
        distance_sums.append(curr_sum)
    
    emergency = transcription_without_sw[np.argmin(distance_sums)]
    return emergency

print(get_emergency("Thursday December 8th 2016 1109 and 43 secondsThursday December 8th 2016 1109 and 43 seconds fire medical 44 what is the address of your emergency fire medical 44 what is the address of your emergency I'm glad Avenue address real quick if your address here address 2974 Garnet Avenue okay 2974 Garnett and is that a house or an apartment of business this business Napa Auto Care Collision Center okay and what's the phone number you're calling 2974 Garnet Avenue okay 2974 Garnett and is that a house or an apartment of business this business it's Napa Auto Care Collision Center okay and what's the phone number you're calling"))