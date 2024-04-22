import dotenv
import os
import requests

dotenv.load_dotenv()
DARC_REVIEW_URL = 'https://hurlstor.soest.hawaii.edu:5000'

"""
{
    media_id: {
      scientific_name: str,
      id_reference: int,
      ids: [int],
    },
    
}
"""
groups = {}

darc_comments = requests.get(
    f'{DARC_REVIEW_URL}/comment/all',
    headers={
        'API-Key': os.getenv('DARC_REVIEW_API_KEY')
    }
).json()

print(f'Total comments: {len(darc_comments.keys())}')
current_id = 1

for uuid, comment in darc_comments.items():
    if 'scientific_name' in comment and comment['scientific_name'] is not None:
        if comment['video_url'] is None:
            print(comment)
            continue
        media_id = comment['video_url'].split('/')[-1].split('.')[0]
        if media_id not in groups.keys():
            groups[media_id] = {
                'scientific_name': comment['scientific_name'],
                'id_reference': comment['sequence'],
                'ids': [comment['uuid']],
            }
        else:
            groups[media_id]['ids'].append(comment['uuid'])


for key, value in groups.items():
    if len(value['ids']) > 1:
        value['id_reference'] += f':{current_id}'
        current_id += 1
        for comment_id in value['ids']:
            update = requests.patch(
                f'{DARC_REVIEW_URL}/comment/id-reference/{comment_id}',
                headers={
                    'API-Key': os.getenv('DARC_REVIEW_API_KEY')
                },
                data={
                    'id_reference': value['id_reference']
                }
            )
            print(update.status_code)
