import nltk
from nltk.stem.lancaster import LancasterStemmer
stemmer = LancasterStemmer()
import random
from twilio.rest import Client
import numpy
import tflearn
import tensorflow
import json
import pickle
import mysql.connector
from time import sleep

mydb = mysql.connector.connect(
host="localhost",
user="root",
passwd="12345678",
database="chatbot"
)

mycursor = mydb.cursor()

with open("intents.json") as file:
    data = json.load(file)

try:
    with open("data.pickle", "rb") as f:
        words, labels, training, output = pickle.load(f)
except:
    words = []
    labels = []
    docs_x = []
    docs_y = []

    for intent in data["intents"]:
        for pattern in intent["patterns"]:
            wrds = nltk.word_tokenize(pattern)
            words.extend(wrds)
            docs_x.append(wrds)
            docs_y.append(intent["tag"])

        if intent["tag"] not in labels:
            labels.append(intent["tag"])

    words = [stemmer.stem(w.lower()) for w in words if w != "?"]
    words = sorted(list(set(words)))

    labels = sorted(labels)

    training = []
    output = []

    out_empty = [0 for _ in range(len(labels))]

    for x, doc in enumerate(docs_x):
        bag = []

        wrds = [stemmer.stem(w.lower()) for w in doc]

        for w in words:
            if w in wrds:
                bag.append(1)
            else:
                bag.append(0)

        output_row = out_empty[:]
        output_row[labels.index(docs_y[x])] = 1

        training.append(bag)
        output.append(output_row)


    training = numpy.array(training)
    output = numpy.array(output)

    with open("data.pickle", "wb") as f:
        pickle.dump((words, labels, training, output), f)

tensorflow.compat.v1.reset_default_graph()

net = tflearn.input_data(shape=[None, len(training[0])])
net = tflearn.fully_connected(net, 8)
net = tflearn.fully_connected(net, 8)
net = tflearn.fully_connected(net, len(output[0]), activation="softmax")
net = tflearn.regression(net)

model = tflearn.DNN(net)

try:
    model.load("model.tflearn")
except:
    model.fit(training, output, n_epoch=1000, batch_size=8, show_metric=True)
    model.save("model.tflearn")

def bag_of_words(s, words):
    bag = [0 for _ in range(len(words))]

    s_words = nltk.word_tokenize(s)
    s_words = [stemmer.stem(word.lower()) for word in s_words]

    for se in s_words:
        for i, w in enumerate(words):
            if w == se:
                bag[i] = 1
            
    return numpy.array(bag)

def verify_and_transfer():
    global otp, otpByUser, user, Sacc_no, Racc_no, amountT, ifsc, tag
    tag = " "
    if str(otp) == otpByUser:
        mycursor = mydb.cursor()
        mycursor.execute(f"SELECT Current_balance from Account_Details WHERE Account_no = {Sacc_no}")
        balance = mycursor.fetchone()
        mydb.commit()
        if float(balance[0]) < float(amountT):
            return ("Insufficient balance")
        else:
            try:
                if user == 0:
                    mycursor = mydb.cursor()
                    mycursor.execute(f"UPDATE {ifsc} SET Current_balance = Current_balance + {amountT} where Account_no = {Racc_no} ")
                    mycursor.fetchone()
                else:
                    mycursor = mydb.cursor()
                    mycursor.execute(f"UPDATE Account_Details SET Current_balance = Current_balance + {amountT} where Account_no = {Racc_no} ")
                    mycursor.fetchone()
                mycursor = mydb.cursor()
                mycursor.execute(f"UPDATE Account_Details SET Current_balance = Current_balance - {amountT} where Account_no = {Sacc_no} ")
                mycursor.fetchone()
                mydb.commit()
                return ("Transaction successful")
            except:
                return ("Unable to process data.")
    else:
        return ("OTP did not matched.")
        
def show_balance():
    global otp, otpByUser, user, Sacc_no,tag
    tag = " "
    if str(otp) == otpByUser:
        mycursor = mydb.cursor()
        mycursor.execute(f"SELECT Current_balance from Account_Details WHERE Account_no = {Sacc_no}")
        res = mycursor.fetchone()

        mydb.commit()

        if res != None:
            return ("Awesome. Here is your Account Balance. INR "+ str(res[0]))
        else:
            return ("Provided Account Number does not exist.")
    else:
        return ("OTP did not matched.")

def three_lines():
    global tag
    for tg in data["intents"]:
        if tg['tag'] == tag:
            responses = tg['responses']
    try:
        return random.choice(responses)
    except:
        tag = " "
        return "Sorry I can't understand. Please try again."

def get_amountT():
    global tag
    response = three_lines()
    tag = "store_amountT"
    return response

def get_R_acc_no():
    global tag
    response = three_lines()
    tag = "store_R_Account_no"
    return response

def get_S_acc_no():
    global tag
    response = three_lines()
    tag = "store_S_Account_no"
    return response

def twilio(Mobile):
    client=Client("AC320620032d4c21cac411a09797fe5c39","88e0c5537e030e061e17f8d21de42426") #cb64a8a8718da52f9cb5a12b76d64e3048be0d67
    #4c2226a15af7e1c41517cbf8fc3a0329dae767bd
    n= random.randint(1000,9999)
    client.messages.create(to=[f"+91 {Mobile}"],
    from_ = "+13347218595", 
    body=(f"Your OTP {n}"))
    print(n)
    global otp
    otp = n

def send_otp():
    global Sacc_no
    mycursor = mydb.cursor()
    mycursor.execute(f"SELECT Contact_no from Account_Details WHERE Account_no = {Sacc_no}")
    mobno = mycursor.fetchone()

    mydb.commit()
    
    if mobno != None:
        Mobile = str(mobno[0])
        twilio(Mobile)
        global tag
        response = three_lines()
        tag = "store_user_OTP"
        return response
    else:
        tag = " "
        return ("Account number does not exists.")

def send_otp_acc_bal():
    global Sacc_no
    mycursor = mydb.cursor()
    mycursor.execute(f"SELECT Contact_no from Account_Details WHERE Account_no = {Sacc_no}")
    mobno = mycursor.fetchone()

    mydb.commit()
    
    if mobno != None:
        Mobile = str(mobno[0])
        twilio(Mobile)
        global tag
        response = three_lines()
        tag = "store_user_OTP_acc_bal"
        return response
    else:
        tag = " "
        return ("Account number does not exists.")

def start_transfer(inp):
    global tag
    possibleTags = ["transfer_money_to_external_bank_user","transfer_money_initial"]
    results = model.predict([bag_of_words(inp, words)])
    results_index = numpy.argmax(results)
    tag = labels[results_index]
    global user
    if tag not in possibleTags:
        tag = " "
        return ("I didn't understand. Try again.")
    elif tag == possibleTags[0]:
        response = three_lines()
        user = 0
        tag = "store_IFSC"
        return response
    else:
        response = three_lines()
        tag = "store_R_Account_no"
        user = 1
        return response


def chat():
    print("Start talking with the bot (type quit to stop)!")
    while True:
        inp = request.args.get('msg')
        if inp.lower() == "quit":
            break
        global tag, Sacc_no, otpByUser
        if tag == "store_S_acc_no_acc_bal":
            Sacc_no = inp
            tag = "account_balance_get_otp"
            return send_otp_acc_bal()
        elif tag == "store_user_OTP_acc_bal":
            otpByUser = inp
            tag = "account_balance_final"
            return show_balance()
        elif tag == "Inside_transfer":
            return start_transfer(inp)
        elif tag == "store_IFSC":
            global ifsc
            ifsc = inp
            tag = "transfer_money_initial"
            return get_R_acc_no()
        elif tag == "store_R_Account_no":
            global Racc_no
            Racc_no = inp
            tag = "transfer_money_getAmount"
            return get_amountT()
        elif tag == "store_amountT":
            global amountT
            amountT =  inp
            tag = "transfer_money_getSenders_acc_no"
            return get_S_acc_no()
        elif tag == "store_S_Account_no":
            Sacc_no = inp
            tag = "transfer_money_get_otp"
            return send_otp()
        elif tag == "store_user_OTP":
            otpByUser = inp
            tag = "transfer_money_final"
            return verify_and_transfer()
        else:
            results = model.predict([bag_of_words(inp, words)])
            results_index = numpy.argmax(results)
            tag = labels[results_index]

            for tg in data["intents"]:
                if tg['tag'] == tag:
                    responses = tg['responses']
            if tag == "account_balance":
                tag = "store_S_acc_no_acc_bal"

            if tag == "transfer_money":
                tag = "Inside_transfer"

            return random.choice(responses)


from flask import Flask, render_template, request

app = Flask(__name__)
app.static_folder = 'static'

from flask_mysqldb import MySQL


@app.route('/')
def main_page():
    return render_template("bank_web.html")

'''@app.route('/chatbot')
def bot_page():
    return render_template("bot.html")'''


@app.route('/second')
def about():
    return render_template("about.html")

@app.route('/fourth')
def contact():
    return render_template("contact.html")

@app.route('/loginReg', methods=['GET', 'POST'])
def loginReg():
    return render_template("sign.html")
    
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        userDetails = request.form
        name = userDetails['user_name']  # s_name in html file
        password = userDetails['password']
        name = userDetails['user_name']  # s_name in html file
        password = userDetails['password']
        mycursor = mydb.cursor()
        mycursor.execute( "SELECT * FROM login WHERE username LIKE %s and password LIKE %s", [name,password] )
        data = mycursor.fetchone()
        mydb.commit()
        mycursor.close()
        if(data != None):
            return render_template("index.html")
        else:
            print("failed")
            return render_template("sign.html")


@app.route('/Reg', methods=['GET', 'POST'])
def reg():
    if request.method == 'POST':
        userDetails = request.form
        name = userDetails['user_name']  # s_name in html file
        email = userDetails['email']
        password = userDetails['password']
        contact = userDetails['contact']
        mycursor = mydb.cursor()
        mycursor.execute("INSERT INTO login(username,email,contact_no,password) VALUES(%s, %s,%s,%s)", (name, email, contact,password))
        mydb.commit()
        mycursor.close()
        return render_template("sign.html")


''''@app.route("/")
def home():
    return render_template("index.html")'''

@app.route("/get")
def get_bot_response():
    return chat()

if __name__ == "__main__":
    tag = " "
    ifsc = " "
    Racc_no = " "
    Sacc_no = " "
    amountT = " "
    otp = " "
    otpByUser = " "
    user = 100
    app.run()