import random
import json
import pickle
import numpy as np
import nltk
from nltk.stem import WordNetLemmatizer
from tensorflow.keras.models import Sequential
from tensorflow.keras.layers import Dense, Activation, Dropout
from tensorflow.keras.optimizers import SGD
from tensorflow.keras.models import load_model
import speech_recognition as sr
import pyttsx3

nltk.download('punkt')
nltk.download('wordnet')

# Initialize lemmatizer
lemmatizer = WordNetLemmatizer()

model = load_model('../models/chatbot_model.h5')
intents = json.loads(open('../dataset/convo.json').read())
words = pickle.load(open('../obj2/words.pkl','rb'))
classes = pickle.load(open('../obj2/classes.pkl','rb'))

# Initialize text-to-speech engine
engine = pyttsx3.init()

# Function to clean and tokenize sentence
def clean_up_sentence(sentence):
    sentence_words = nltk.word_tokenize(sentence)
    sentence_words = [lemmatizer.lemmatize(word.lower()) for word in sentence_words]
    return sentence_words

# Function to create bag of words from sentence
def bag_of_words(sentence, words):
    sentence_words = clean_up_sentence(sentence)
    bag = [0]*len(words)
    for w in sentence_words:
        if w in words:
            bag[words.index(w)] = 1
    return np.array(bag)

# Function to perform speech recognition
def recognize_speech():
    recognizer = sr.Recognizer()
    with sr.Microphone() as source:
        print("Speak something:")
        audio = recognizer.listen(source)

    try:
        # Convert speech to text using Google Web Speech API
        message = recognizer.recognize_google(audio)
        print("You said:", message)
        return message
    except sr.UnknownValueError:
        print("Sorry, I didn't catch that.")
        return ""
    except sr.RequestError:
        print("Sorry, there was an error with the speech recognition service.")
        return ""
    
# Function to predict the class of the input sentence
def predict_class(sentence):
    ERROR_THRESHOLD = 0.25
    bow = bag_of_words(sentence, words)
    res = model.predict(np.array([bow]))[0]
    results = [[i, r] for i, r in enumerate(res) if r > ERROR_THRESHOLD]
    results.sort(key=lambda x: x[1], reverse=True)
    return_list = []
    for r in results:
        return_list.append({'intent': classes[r[0]], 'probability': str(r[1])})
    return return_list

# Function to get the response for the input sentence
def get_response(intents_list, intents_json):
    if intents_list:
        tag = intents_list[0]['intent']
        intents_dict = {i['tag']: i for i in intents_json['intents']}
        if tag in intents_dict:
            result = random.choice(intents_dict[tag]['responses'])
        else:
            result = "I am sorry, I am not sure how to respond to that."
    else:
        result = "No intent found"
    return result

# Initialize an empty list to store responses
recorded_responses = []

# Function to record responses
def record_response(response):
    recorded_responses.append(response)

# Main loop for the chatbot
while True:
    # Get user input through speech recognition
    message = recognize_speech()
    if message:
        # Predict intent and get response
        ints = predict_class(message)
        res = get_response(ints, intents)
        print("Bot:", res)
        # Record the response
        record_response(res)
        # Speak the response using text-to-speech
        engine.say(res)
        engine.runAndWait()