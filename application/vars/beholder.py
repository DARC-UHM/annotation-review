import json

import requests


class Beholder:
    """
    Extracts on-demand images from VARS videos.
    """

    def __init__(self, base_url: str, api_key: str):
        self.base_url = base_url
        self.headers = {'X-API-Key': api_key}

    def get_frame(self, video_url: str, elapsed_time_millis: int):
        data = {
            'videoUrl': video_url,
            'elapsedTimeMillis': elapsed_time_millis,
        }

        res = requests.post(
            url= f'{self.base_url}/capture',
            data=json.dumps(data),
            headers=self.headers,
        )

        if res.status_code == 200:
            print(res.text)
            return res.content

        raise ValueError("Failed to capture image")
