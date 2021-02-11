from selenium import webdriver 
from selenium.webdriver.common.desired_capabilities import DesiredCapabilities
import time
import json
import random
from http_request_randomizer.requests.proxy.requestProxy import RequestProxy
import requests

# If need for a proxy
PROXY = #some proxy address

#INIT DRIVER
caps = DesiredCapabilities.FIREFOX
caps['proxy'] = {
    "httpProxy":PROXY,
    "ftpProxy":PROXY,
    "sslProxy":PROXY,
    "proxyType":"MANUAL",   
}
driver = webdriver.Firefox(desired_capabilities=caps)

#60 seconds to connect with your strava account. Once connected go to strava homepage, it may need to refresh
driver.get("https://accounts.google.com/o/oauth2/auth?access_type=offline&client_id=541588808765.apps.googleusercontent.com&redirect_uri=https%3A%2F%2Fwww.strava.com%2Fo_auth%2Fgoogle&response_type=code&scope=https%3A%2F%2Fwww.googleapis.com%2Fauth%2Fplus.login+https%3A%2F%2Fwww.googleapis.com%2Fauth%2Fplus.me+email+profile&state=%7B%22context%22%3A%22google_web_signin%22%2C%22state%22%3A%22eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.eyJzdGF0ZV9wYXJhbSI6ImM2dGowZjNyN2pvOGcxbGVsN29mYXYxNjBtY2gwNWdtIn0.eP7jWxMDyLM3mtFnxv2RwGMGJcdL-ZIUOlm17LCqAAM%22%7D")
time.sleep(60)
 
#SCRAPPING 
cpt = #Some value here
filenumber = 0
while(1):
    print(cpt)
    driver.get("https://www.strava.com/activities/"+str(cpt)+"/overview")
    el = driver.find_elements_by_xpath("//*[contains(text(), 'Course à pied')]")#This is in french but can be replaced with run instead of Course à pied
    if(len(el)!=0):#Checks if it's a run
        r = random.randint(1,5)
        time.sleep(r)
        try:
            driver.get("https://www.strava.com/activities/"+str(cpt)+"/streams?stream_types%5B%5D=altitude&stream_types%5B%5D=heartrate&stream_types%5B%5D=distance&stream_types%5B%5D=time") #Can add more features in the url if needed
            loaded_data = json.loads(driver.find_element_by_tag_name('body').text)
            #Saves the data
            with open('Data/'+str(filenumber)+'.json', 'w') as json_file:
                json.dump(loaded_data, json_file)
        except:
            pass
    cpt = cpt + 1
    filenumber = filenumber +1
    r = random.randint(1,10)
    time.sleep(r)

driver.close()
