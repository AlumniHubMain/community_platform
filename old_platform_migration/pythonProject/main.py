import json
import os
from logging import exception
import shutil
import requests

import psycopg2
import json

def download_data():
    conn = psycopg2.connect(dbname='YNDXFamily_db', user='',
                            password='', host='rc1b-mgzhxwi08xpp4neh.mdb.yandexcloud.net', port=6432)
    cursor = conn.cursor()
    cursor.execute('DECLARE cur CURSOR FOR SELECT * FROM alh_communities_members.profiles;')
    while True:
        try:
            cursor.execute('FETCH 10 FROM cur;')
            for row in cursor.fetchall():
                current_json = dict((cursor.description[j][0], value)
                                    for j, value in enumerate(row))
                with open(f'downloaded/{current_json['id']}.json', 'w+') as output:
                    output.write(json.dumps(current_json, indent=4, default=str, ensure_ascii=False))
                print(current_json)
        except Exception as e:
            print(e)
            break
    cursor.close()
    conn.close()


def convert_user(old_format_json):
    try:
        result = dict()
        result['name'] = old_format_json['name']
        result['surname'] = old_format_json['surname']
        result['email'] = old_format_json['email']

        result['avatars'] = ['https://storage.googleapis.com/community_platform_media1/a3021a9be9dd238254a5b9aa7203a255/webp.webp']
        result['about'] = ''
        result['interests'] = [] # ToDo(evseev.dmsr) Change to when enum issue will be closed -> [i.strip() for i in old_format_json.get('hobbies').lower().split(,)]

        result['linkedin_link'] = old_format_json.get('linkedin_link')
        result['telegram_name'] = old_format_json.get('telegram_name')
        result['telegram_id'] = old_format_json.get('telegram_id')

        result['expertise_area'] = []  # ToDo(evseev.dmsr) Change to when enum issue will be closed -> [i.strip() for i in old_format_json.get('expertise_raw').lower().split(,)]
        result['specialisation'] = []  # ToDo(evseev.dmsr) Change to when enum issue will be closed -> [i.strip() for i in old_format_json.get('speciality_raw').lower().split(,)]
        result['grade'] = None

        result['industry'] = []
        result['skills'] = []

        result['current_company'] = old_format_json.get('current_job')
        result['company_services'] = []

        result['location'] = None # ToDo(evseev.dmsr) Change to when enum issue will be closed -> f'{old_format_json.get('town_live')} {old_format_json.get('country_live')}'.lower().strip()
        result['referral'] = False

        result['requests_to_community'] = []

        result['available_meetings_pendings_count'] = 0
        result['available_meetings_confirmations_count'] = 0
        result['who_to_date_with'] = 'anyone'
        result['who_sees_profile'] = 'anyone'
        result['who_sees_current_job'] = 'anyone'
        result['who_sees_contacts'] = 'anyone'
        result['who_sees_calendar'] = 'anyone'
        result['profile_type'] = 'migrated_has_issues'

        return result

    except Exception as e:
        print (f'not_converted {old_format_json['id']}')
        raise e


def convert_users():
    for input_file in os.listdir('downloaded'):
        with open(f'downloaded/{input_file}') as input:
            try:
                input_json = json.loads(input.read())
                output_json = convert_user(input_json)
                with open(f'converted/{input_file}', 'w+') as output:
                    output.write(json.dumps(output_json, indent=4, default=str, ensure_ascii=False))
            except Exception as e:
                print(input_file)
                shutil.copyfile(f'downloaded/{input_file}', f'not_converted/{input_file}')


def upload_data():
    headers = {
        'Content-Type': 'application/json'
    }

    for input_file in os.listdir('converted'):
        with open(f'converted/{input_file}') as input:
            try:
                profile = input.read()
                result = requests.post('http://0.0.0.0:8000/user', data=profile, headers=headers)
                continue
            except Exception as e:
                print(input_file)
                shutil.copyfile(f'converted/{input_file}', f'not_converted/{input_file}')


# download_data()
# convert_users()
upload_data()

