import requests
import json
import time
from datetime import datetime, timedelta
from pytz import timezone
from pytz import utc
import re

token = '425349659:AAHF19iJ1hvVC_ihXQo2TAAPgLOY6biTjAU'
url = 'https://api.telegram.org/bot{token}/'.format(**locals())
temp_user_list =[]

def get_url(url):
    response = requests.get(url)
    return json.loads(response.text)

def send_updates(chat_id,text):
    return get_url(url+'sendMessage?chat_id={chat_id}&text={text}'.format(**locals()))

def get_updates(offset=None):
    if offset:
        return get_url(url+'getUpdates?timeout=100'+"&offset={offset}".format(**locals()))
    return get_url(url+'getUpdates?timeout=100')

def last_update_id(updates):
    update_ids = []
    for update in updates['result']:
        update_ids.append(int(update['update_id']))
    return max(update_ids)

def echo_all(updates):
    for update in updates['result']:
        try:
            chat_id = update['message']['chat']['id']
            text = update['message']['text']
            from_id = update['message']['from']['username']
            #print('Received from ' + from_id + ' > ' + text)
            send_updates(chat_id, text)
            print('Replied to ' + from_id + ' > ' + text)
        except Exception as e:
            print(e)

def get_hydpy_meetup(chat_id):
    response = requests.get('https://api.meetup.com/2/events?offset=0&format=json&limited_events=False'\
                            '&group_urlname=Hyderabad-Python-Meetup-Group&photo-host=public&page=20&fields='\
                            '&order=time&desc=false&status=upcoming&sig_id=8101615&sig=47907134e718c42220aa2e8a7de154be8757318b')
    parsed_json = json.loads(response.text)
    if len(parsed_json['results'])>0:
        send_updates(chat_id, 'I noticed there are ' + str(len(parsed_json['results'])) + ' Meetups')
        for i in range(len(parsed_json['results'])):
            utc_dt = utc.localize(datetime.utcfromtimestamp(parsed_json['results'][i]['time']//1000))
            ist_dt = utc_dt.astimezone(timezone('Asia/Kolkata'))
            try:
                venue = parsed_json['results'][i]['venue']['name']
            except:
                venue = 'Location unavailable'
            text = ('Meetup Name: ' + parsed_json['results'][i]['name'] + '\n' +\
                    'Location: ' + venue + '\n' +\
                    'Time: ' + str(ist_dt.strftime('%I:%M %p, %b %d,%Y (%Z)')) + '\n' +\
                    'RSVP Here: ' + parsed_json['results'][i]['event_url'])
            send_updates(chat_id, text)
    else:
        send_updates(chat_id, 'There are no new Meetups scheduled :(')


def commander(updates):
    for update in updates['result']:
        try:
            chat_id = update['message']['chat']['id']
            text = update['message']['text']
            from_id = update['message']['from']['username']
            print('Received from ' + from_id + ' > ' + text)
            if re.search('hydpy',text,re.IGNORECASE):
                get_hydpy_meetup(chat_id)
                print('Replied to ' + from_id + ' > ' + 'Meetup Details')
            else:
                echo_all(updates)
        except Exception as e:
            print(e)

def main():
    offset = None
    while True:
        try:
            all_updates_json = get_updates(offset)
        except:
            pass
        if len(all_updates_json['result']) > 0:
            offset = last_update_id(all_updates_json) + 1
            #echo_all(all_updates_json)
            commander(all_updates_json)
        time.sleep(0.4)

if __name__ == '__main__':
    main()

# if len(parsed_content['result'])>0:
#     for i in parsed_content['result']:
#         if parsed_content['result'][0]['message']['from']['username'] not in temp_user_list:
#             temp_user_list.append(parsed_content['result'][0]['message']['from']['username'])
#             first_name = parsed_content['result'][0]['message']['from']['first_name']
#             send_text='Hello {first_name}'.format(**locals())
#             send_updates(parsed_content['result'][0]['message']['chat']['id'],send_text)
#         send_updates(parsed_content['result'][0]['message']['chat']['id'],'Howdy!')
