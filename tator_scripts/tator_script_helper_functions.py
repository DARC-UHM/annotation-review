import os
import sys
import tator


def get_deployment_section_id_map() -> dict:
    deployment_section_id_map = {}

    print('Fetching section details from Tator...', end='')
    sys.stdout.flush()

    try:
        section_list = tator.get_api(
            host='https://cloud.tator.io',
            token=os.getenv('TATOR_TOKEN'),
        ).get_section_list(26)  # hardcoded NGS-ExTech Project
        for section in section_list:
            if 'bad_imports' in section.path or 'TopLevelSectionName' in section.path:
                continue
            deployment_section_id_map[section.name] = section.id
    except tator.openapi.tator_openapi.exceptions.ApiException as e:
        print(f'ERROR: Unable to fetch Tator sections: {e}')
        exit(1)

    print('fetched!')

    return deployment_section_id_map


def print_progress_bar (iteration: int, total: int, prefix: str = '', suffix: str = ''):
    """
    Call in a loop to create terminal progress bar
    """
    length = 100
    term_blue = '\033[1;34m'
    term_normal = '\033[1;37;0m'
    percent = round((100 * (iteration / float(total))), 1)
    filled_length = int(length * iteration // total)
    bar = f'█' * filled_length + '-' * (length - filled_length)
    print(f'\r{prefix} {term_blue}|{bar}|{term_normal} {percent}% {suffix}', end='\r')
    if iteration == total:
        print()