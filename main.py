import smtplib
from datetime import date, time, datetime
import sys
import keyboard

def onKeyPress():
    print("OVER")
    sys.exit(0)

client_date = date(2026,8,12)
client_time = time(19,49)

while True:
    if date.today() == client_date and datetime.now().time() == client_time:
        #Variables for sender email and receiver email
        email = input("Enter Your Email: ")
        receiver = input("Send To: ")

        #Email Text
        subject = input("Subject: ")
        message = input("Message Body: ")

        text = f"Subject: {subject}\n\n{message}"

        #Connecting to server and sending the Email
        server = smtplib.SMTP("smtp.gmail.com", 587)
        server.starttls()

        server.login(email, "vwpy hybu acgk jelf")

        server.sendmail(email, receiver, text)
        print("Email Has Been Sent!")

        break;