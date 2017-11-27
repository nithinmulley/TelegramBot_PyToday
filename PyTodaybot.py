import requests
import json
import time
from datetime import datetime, timedelta
from pytz import timezone
from pytz import utc
import re
from os.path import expanduser


# Store and your Bot token in your home directory -> ~/.tokens/telegram_bot
home = expanduser("~")
token_file = str(home) + '/.tokens/telegram_bot'
with open(token_file) as f:
    token = f.readline().strip()


tg_url = 'https://api.telegram.org/bot{token}/'.format(**locals())
meetup_dict = {'hydpy': 'Hyderabad-Python-Meetup-Group',
               'coderplex': 'coderplex'}


def get_url(url):
    response = requests.get(url)
    return json.loads(response.text)


def get_updates(offset=None):
    if offset:
        return get_url(tg_url+'getUpdates?timeout=100'+"&offset={offset}".format(**locals()))
    return get_url(tg_url+'getUpdates?timeout=100')


def send_updates(chat_id, text):
    return get_url(tg_url+'sendMessage?chat_id={chat_id}&text={text}'.format(**locals()))


def send_inline(answer):
    return requests.post(url=tg_url + 'answerInlineQuery', params=answer)


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
            # print('Received from ' + from_id + ' > ' + text)
            send_updates(chat_id, text)
            print('Chat Echoed ' + from_id + ' > ' + text)
        except Exception as e:
            print(e)


def prt_recd_from(data, method, query):
    try:
        from_id = data['from']['username']
        if method == 'inline_query':
            print('Inline Query Received from ' + from_id + ' > ' + query)
        elif method == 'message':
            print('Chat Received from ' + from_id + ' > ' + query)
        return from_id
    except Exception as e:
        print(e)
    return


def prt_sent_to(from_id, method, action):
    try:
        if from_id:
            if method == 'inline_query':
                print('Inline Query answered to ' + from_id + ' > ' + action)
            elif method == 'message':
                print('Chat Replied to ' + from_id + ' > ' + action)
    except Exception as e:
        print(e)
    return


def meetup_api(group_name=None):
    if group_name is not None:
        group_urlname = meetup_dict[group_name]
        response = requests.get(r'https://api.meetup.com/{group_urlname}/events'
                                '?&sign=true&photo-host=public&page=20'.format(**locals()))
        parsed_json = json.loads(response.text)
        meetup_list = []
        if len(parsed_json) > 0:
            for i in range(len(parsed_json)):
                utc_dt = utc.localize(datetime.utcfromtimestamp(parsed_json[i]['time']//1000))
                ist_dt = utc_dt.astimezone(timezone('Asia/Kolkata'))
                try:
                    venue = parsed_json[i]['venue']['name']
                except Exception as e:
                    print(e)
                    venue = 'Location unavailable'
                text = ('Meetup Name: ' + parsed_json[i]['name'] + '\n' +
                        'Location: ' + venue + '\n' +
                        'Time: ' + str(ist_dt.strftime('%I:%M %p, %b %d,%Y (%Z)')) + '\n' +
                        'RSVP Here: ' + parsed_json[i]['link'])
                meetup_list.append({'name': parsed_json[i]['name'],
                                    'location': venue,
                                    'time': str(ist_dt.strftime('%I:%M %p, %b %d,%Y (%Z)')),
                                    'url': parsed_json[i]['link'],
                                    'going': parsed_json[i]['yes_rsvp_count'],
                                    'who': parsed_json[i]['group']['who'],
                                    'groupname': parsed_json[i]['group']['name'],
                                    'text': text},)
        return meetup_list
    return


def send_inline_meetups(meetup_list, inline_query_id, from_id):
    results = []
    if len(meetup_list) > 0:
        for u_id, meetup in enumerate(meetup_list):
            results.append({'type': 'article',
                            'id': u_id,
                            'title': meetup['name'],
                            'parse_mode': 'Markdown',
                            'message_text': meetup['text'],
                            'description': '{} {} are going'.format(meetup['going'], meetup['who'])})
        answer = {'inline_query_id': inline_query_id, 'results': json.dumps(results), 'cache_time': '30'}
        send_inline(answer)
        prt_sent_to(from_id, 'inline_query', meetup_list[0]['groupname'] + ' Meetup Details')
    else:
        results.append({'type': 'article',
                        'id': 0,
                        'title': 'No Meetups scheduled in this group',
                        'parse_mode': 'Markdown',
                        'message_text': 'No Meetups scheduled in this group',
                        'description': 'Check again later'})
        answer = {'inline_query_id': inline_query_id, 'results': json.dumps(results), 'cache_time': '30'}
        send_inline(answer)
        prt_sent_to(from_id, 'inline_query',  ' No meetups scheduled')
    return


def send_chat_meetups(meetup_list, chat_id, from_id):
    if len(meetup_list) > 0:
        send_updates(chat_id, 'I noticed ' + str(len(meetup_list)) + ' Meetups')
        for meetup in meetup_list:
            send_updates(chat_id, meetup['text'].replace('&','%26'))
        prt_sent_to(from_id, 'message', meetup_list[0]['groupname'] + ' Meetup Details')
    else:
        send_updates(chat_id, 'There are no new Meetups scheduled :(')
        prt_sent_to(from_id, 'message', ' No meetups scheduled')
    return


def process_meetups(query, query_type, send_id, from_id):
    if query in meetup_dict:
        meetup_list = meetup_api(query)
        if query_type == 'inline':
            send_inline_meetups(meetup_list, send_id, from_id)
        elif query_type == 'chat':
            send_chat_meetups(meetup_list, send_id, from_id)
    else:
        return None
    return True


def commander(updates):
    for update in updates['result']:
        if 'inline_query' in update:
            inline_query = update['inline_query']
            inline_query_id = inline_query['id']
            query = inline_query['query'].lower().strip('/')
            from_id = prt_recd_from(inline_query, 'inline_query', query)
            process_meetups(query, 'inline', inline_query_id, from_id)
        else:
            try:
                message = update['message']
                chat_id = message['chat']['id']
                query = message['text'].strip('/')
                from_id = prt_recd_from(message, 'message', query)
                check = process_meetups(query, 'chat', chat_id, from_id)
                if check is None:
                    echo_all(updates)
            except Exception as e:
                print(e)


def main():
    offset = None
    while True:
        try:
            all_updates_json = get_updates(offset)
            if len(all_updates_json['result']) > 0:
                offset = last_update_id(all_updates_json) + 1
                commander(all_updates_json)
        except Exception as e:
            print(e)
        time.sleep(0.4)


if __name__ == '__main__':
    main()