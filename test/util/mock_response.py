from test.data.vars_responses import ex_23060001, ex_23060002, pomacentridae, hydroidolina


class MockResponse:
    def __init__(self, url: str):
        self.url = url
        self.status_code = 200

    def json(self):
        match self.url:
            case 'http://hurlstor.soest.hawaii.edu:8086/query/dive/Deep%20Discoverer%2023060001':
                return ex_23060001
            case 'http://hurlstor.soest.hawaii.edu:8086/query/dive/Deep%20Discoverer%2023060002':
                return ex_23060002
            case 'http://hurlstor.soest.hawaii.edu:8083/v1/phylogeny/up/Pomacentridae':
                return pomacentridae
            case 'http://hurlstor.soest.hawaii.edu:8083/v1/phylogeny/up/Hydroidolina':
                return hydroidolina
        return {}
