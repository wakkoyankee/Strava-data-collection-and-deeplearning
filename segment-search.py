import geocoder
import requests
import urllib3
import json
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
myloc = geocoder.ip('me')

bounds = myloc.latlng
activity_type = "running"


auth_url = "https://www.strava.com/oauth/token"
seg_ex_url = "https://www.strava.com/api/v3/segments/explore"

payload = { # Get API accesses
    'client_id':"",
    'client_secret':'',
    'refresh_token':'',
    'grant_type':"refresh_token",
    'f': 'json'  
}

res = requests.post(auth_url, data=payload, verify=False)
access_token = res.json()['access_token']
print("Access token = {}\n".format(access_token))

header = {'Authorization': 'Bearer '+ access_token}
param = {'bounds' : bounds, 'activityType': activity_type}

data = requests.get(seg_ex_url,headers=header,params=param).json()
print(data)
with open('test.json', 'w') as json_file:
                json.dump(data, json_file)
