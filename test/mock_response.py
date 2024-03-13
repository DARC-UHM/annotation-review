from test.data.annotations import annotations


class MockResponse:
    def __init__(self, req_url):
        self.req_url = req_url
        self.status_code = 200

    def json(self):
        match self.req_url:
            case 'NO_MATCH':
                return {}
            case 'http://hurlstor.soest.hawaii.edu:8086/query/dive/Deep%20Discoverer%2023060001':
                return annotations
        return None

