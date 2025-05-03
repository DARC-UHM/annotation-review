import os

import dotenv
import tator

dotenv.load_dotenv()

try:
    section_list = tator.get_api(
        host='https://cloud.tator.io',
        token=os.getenv('TATOR_TOKEN'),
    ).get_section_list('26')
    for section in section_list:
        print(f'{section.name}: {section.id}')
except tator.openapi.tator_openapi.exceptions.ApiException:
    print('Error getting Tator sections')
