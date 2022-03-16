import ast
import json
import requests
import time
import paho.mqtt.client as mqtt						# importing mqtt library
from datetime import datetime

from pprint import pprint

BROKER_HOST="io.adafruit.com" 							# variable for mqtt broker address
PORT=1883									# mqtt broker port
TOPIC="JustSM/feeds/cardinput"							# topic to publish cpu
ADAFRUIT_USER="JustSM"
ADAFRUIT_KEY="aio_AiBf478n0PcDn2TB5yE4to2wWtSH"



SPOTIFY_GET_CURRENT_TRACK_URL = 'https://api.spotify.com/v1/me/player/currently-playing'
GET_USER_PROFILE = 'https://api.spotify.com/v1/me'
PAUSE = 'https://api.spotify.com/v1/me/player/pause'
PLAY = 'https://api.spotify.com/v1/me/player/play'
NEXT = 'https://api.spotify.com/v1/me/player/next'
PREV = 'https://api.spotify.com/v1/me/player/previous'
PLAYER = 'https://api.spotify.com/v1/me/player'


ACCESS_TOKEN = 'BQDQQ5L12crAq9TCIgeB740Ogqi3Vnen9B1lHWuqF8yvvPShm4Kltlmhn_aIXh3HAaXkYz75dQ2quMehC6DPIS3XzYGHtrADBHxPzISwzbOP5XLvg2Q80pUWB40Tj13ljyExiS2_lNaS49IEHqU4W92Zf4oVIRE2m936pRdcO6NFQBhQTQ'


def on_connect(client, userdata, flags, rc):		                        # function called on connected
    if rc==0:
        client.connected_flag=True 					        # set flag
        # print("Connected OK")
        client.subscribe(TOPIC, qos=0)
    else:
        print("Bad connection Returned code=",rc)




class MusicStation(object):

    cardMap = {}
    cardMode = False
    newCardData = ""

    def ping(self):
        response = requests.get(
            GET_USER_PROFILE,
            headers={
                "Authorization": f"Bearer {ACCESS_TOKEN}"
            }
        )
        if response.status_code != 200:
            print(response)
            return False
        else:
            return True
    

    def get_current_track(self,access_token):
        response = requests.get(
            SPOTIFY_GET_CURRENT_TRACK_URL,
            headers={
                "Authorization": f"Bearer {access_token}"
            }
        )
        json_resp = response.json()

        track_id = json_resp['item']['id']
        track_name = json_resp['item']['name']
        artists = [artist for artist in json_resp['item']['artists']]

        link = json_resp['item']['external_urls']['spotify']

        artist_names = ', '.join([artist['name'] for artist in artists])

        current_track_info = {
            "id": track_id,
            "track_name": track_name,
            "artists": artist_names,
            "link": link
        }

        return current_track_info

    def goNext(self):
        response = requests.post(NEXT,headers={"Authorization": f"Bearer {ACCESS_TOKEN}"})
        print(response)

    def goPrev(self):
        response = requests.post(PREV,headers={"Authorization": f"Bearer {ACCESS_TOKEN}"})
        print(response)

    def goStopResume(self,newTrack):

        if newTrack != None:
            response = requests.put(PLAY,headers={"Authorization": f"Bearer {ACCESS_TOKEN}","Content-Type": "application/json"},data= "{\"context_uri\": \""+newTrack+"\",\"offset\": {\"position\": 0},\"position_ms\": 0}")
        else:
            response = requests.put(PAUSE,headers={"Authorization": f"Bearer {ACCESS_TOKEN}"})
            if response.status_code !=204:
                response = requests.put(PLAY,headers={"Authorization": f"Bearer {ACCESS_TOKEN}"})
        print(response.text)

    def  cardInsert(self,num):
        if self.cardMode:
            self.saveCard(num,self.newCardData)
            self.cardMode = False
        else:
            if num in self.cardMap:
                self.goStopResume(self.cardMap.get(num)) 
            else:
                print("@Card not found ")

    def startUp(self):
        print("@Start up ")
        if self.ping():
            print("@Connection - OK")
            print("@LED: Green")
        else:
            print("@Connection - Falied")
            print("@LED: Yellow")
            time.sleep(10)
            self.startUp()
        print("@Loading data")
        try:
            a_file = open("data.json", "r")
            output = a_file.read()
            a_file.close()
            print("@File loaded")
            self.cardMap = ast.literal_eval(output)
            print(self.cardMap)
        except :
            print("@File not found, creating new")
            a_file = open("data.json", "w")
            a_file.close()

    def saveCard(self,num,val):
        self.cardMap[num] = val
        try:
            a_file = open("data.json", "w")
            json.dump(self.cardMap,a_file)
            a_file.close()
            print(f"@Card saved, value - {val}")
        except:
            print(f"@Error durig saving !")
    

    def on_message(self,client, userdata, msg):
        now = datetime.now().time()
        payload = msg.payload.decode("utf-8")
        print("Msg received {}, topic: {} value: {}".format(now, msg.topic, payload))
        print("@Card update reviced, Insert card for new data")
        print("LED: GREEN/YELLOW")
        self.newCardData = payload
        self.cardMode = True
    


def main():
    music = MusicStation()

    mqtt.Client.connected_flag=False
    client = mqtt.Client("Subscriber1")					# creating client object
    client.on_connect = on_connect						# defining function o handler on connected
    client.on_message = music.on_message

    client.username_pw_set(ADAFRUIT_USER, password=ADAFRUIT_KEY)
    client.connect(BROKER_HOST, port=PORT, keepalive=60)
    client.loop_start()

    
    # music.saveCard(0,'spotify:playlist:1dQy3jYyuAhOceBwDogoHQ')
    # music.goStopResume(1)
    music.startUp()
    while True:
        command = input("Waiting for command #")
        match command.split():
            case ["exit"]:
                client.loop_stop()    						# stop internal mqtt loop
                client.disconnect() 
                break
            case ["next"]:
                music.goNext()
            case ["prev"]:
                music.goPrev()
            case ["sr"]:
                music.goStopResume(None)
            case ["card",num]:
                music.cardInsert(num)
            case _:
                print(f"Unnknown command : {command}    | Try again ! ")


if __name__ == '__main__':
    main()