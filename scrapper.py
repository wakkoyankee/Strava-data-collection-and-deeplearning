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
driver.get("//google authentification address")
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
