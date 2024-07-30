import nltk
from nltk.stem import WordNetLemmatizer
import pickle
import numpy as np
import json
import random
from keras.models import load_model
from tensorflow.keras.preprocessing.sequence import pad_sequences
import os
import requests
import time
import threading
import mysql.connector
from datetime import datetime

# Define paths relative to the script's directory
MODEL_PATH = os.path.join(os.path.dirname(__file__), '../models/chatbot_model.h5')
INTENTS_PATH = os.path.join(os.path.dirname(__file__), '../dataset/convo.json')
WORDS_PATH = os.path.join(os.path.dirname(__file__), '../obj2/words.pkl')
CLASSES_PATH = os.path.join(os.path.dirname(__file__), '../obj2/classes.pkl')

lemmatizer = WordNetLemmatizer()

# Load model and other necessary data
model = load_model(MODEL_PATH)
intents = json.loads(open(INTENTS_PATH).read())
words = pickle.load(open(WORDS_PATH, 'rb'))
classes = pickle.load(open(CLASSES_PATH, 'rb'))

# Define global variable for location tracking thread
location_tracking_thread = None
stop_location_tracking = False

# Dictionary to track user sessions
user_sessions = {}

def get_db_connection():
    config = {
        'user': 'root',
        'password': '',
        'host': 'localhost',
        'database': 'projectai',
        'raise_on_warnings': True
    }
    try:
        conn = mysql.connector.connect(**config)
        return conn
    except mysql.connector.Error as err:
        print(f"Error connecting to MySQL: {err}")
        return None

def clean_up_sentence(sentence):
    sentence_words = nltk.word_tokenize(sentence)
    sentence_words = [lemmatizer.lemmatize(word.lower()) for word in sentence_words]
    return sentence_words

def bow(sentence, words, show_details=True):
    sentence_words = clean_up_sentence(sentence)
    bag = [0] * len(words)
    for s in sentence_words:
        for i, w in enumerate(words):
            if w == s:
                bag[i] = 1
                if show_details:
                    print("found in bag: %s" % w)
    return np.array(bag)

def predict_class(sentence, model):
    p = bow(sentence, words, show_details=False)
    res = model.predict(np.array([p]))[0]
    ERROR_THRESHOLD = 0.25
    results = [[i, r] for i, r in enumerate(res) if r > ERROR_THRESHOLD]
    results.sort(key=lambda x: x[1], reverse=True)
    return_list = []
    for r in results:
        return_list.append({"intent": classes[r[0]], "probability": str(r[1])})
    return return_list

def getResponse(ints, intents_json):
    if not ints:
        return "I'm sorry, I'm not sure how to respond to that.", None
    
    tag = ints[0]['intent']
    list_of_intents = intents_json.get('intents', [])
    for intent in list_of_intents:
        if intent['tag'] == tag:
            responses = intent.get('responses', [])
            if responses:
                result = random.choice(responses)
                return result, tag
    
    return "I'm sorry, I'm not sure how to respond to that.", None

def get_user_location():
    try:
        response = requests.get('https://ipinfo.io')
        data = response.json()
        location = data['loc']  # 'lat,lon'
        return location
    except Exception as e:
        print(f"Error getting location: {e}")
        return "Unknown location"

def alert_authorities(user_id, location, alert_type, update_existing=False):
    conn = get_db_connection()
    if conn is None:
        print("Failed to connect to database.")
        return

    try:
        cursor = conn.cursor()
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

        if update_existing:
            cursor.execute('''
                UPDATE alerts
                SET location=%s, alert_type=%s, timestamp=%s
                WHERE user_id=%s AND timestamp=(SELECT MAX(timestamp) FROM alerts WHERE user_id=%s)
            ''', (location, alert_type, timestamp, user_id, user_id))
        else:
            cursor.execute('''
                INSERT INTO alerts (user_id, location, alert_type, timestamp)
                VALUES (%s, %s, %s, %s)
            ''', (user_id, location, alert_type, timestamp))
        
        conn.commit()
        cursor.close()
    except mysql.connector.Error as err:
        print(f"Error inserting/updating alert into database: {err}")
        conn.rollback()
    finally:
        conn.close()

def start_location_tracking(interval):
    global stop_location_tracking
    while not stop_location_tracking:
        location = get_user_location()
        print(f"Tracking location: {location}")
        time.sleep(interval)

def chatbot_response(text, user_id):
    global location_tracking_thread
    global stop_location_tracking

    ints = predict_class(text, model)
    response, tag = getResponse(ints, intents)

    alert_type = None
    location_interval = None

    if tag == "attempt":
        alert_type = "concern"
    elif tag == "emergency":
        alert_type = "critical"
        location_interval = 20
    elif tag == "validation":
        alert_type = "emergency"
        location_interval = 10
    elif tag == "validation_yes":
        alert_type = "crisis"
        location_interval = 5
    elif tag == "validation_no":
        alert_type = "safe (warning)"
        stop_location_tracking = True

    if alert_type:
        location = get_user_location()
        update_existing = False

        # Check if the user's session already has an alert
        if user_id in user_sessions:
            last_alert_type = user_sessions[user_id].get('last_alert_type')
            if last_alert_type and last_alert_type != alert_type:
                update_existing = True
        else:
            user_sessions[user_id] = {}

        user_sessions[user_id]['last_alert_type'] = alert_type
        alert_authorities(user_id, location, alert_type, update_existing=update_existing)

    if location_interval:
        stop_location_tracking = False
        if location_tracking_thread is not None and location_tracking_thread.is_alive():
            stop_location_tracking = True
            location_tracking_thread.join()

        location_tracking_thread = threading.Thread(target=start_location_tracking, args=(location_interval,))
        location_tracking_thread.daemon = True
        location_tracking_thread.start()

    return response

def main():
    print("Start chatting with Ethereal (type 'quit' to stop)!")
    while True:
        user_id = input("Enter your user ID: ")
        message = input("You: ")
        if message.lower() == "quit":
            print("Goodbye!")
            break
        response = chatbot_response(message, user_id)
        print(f"Bot: {response}")

if __name__ == "__main__":
    main()
