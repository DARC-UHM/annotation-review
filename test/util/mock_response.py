from test.data.vars_responses import ex_23060001, ex_23060002, pomacentridae, hydroidolina


class MockResponse:
    VARS_CHARYBDIS_URL = 'https://my.little.charybdis'
    VARS_KB_URL = 'https://all.the.knowledge'

    def __init__(self, url: str):
        self.url = url
        self.status_code = 200

    def json(self):
        print(self.url)
        match self.url:
            case 'https://my.little.charybdis/query/dive/Deep%20Discoverer%2023060001':
                return ex_23060001
            case 'https://my.little.charybdis/query/dive/Deep%20Discoverer%2023060002':
                return ex_23060002
            case 'https://all.the.knowledge/phylogeny/up/Pomacentridae':
                return pomacentridae
            case 'https://all.the.knowledge/phylogeny/up/Hydroidolina':
                return hydroidolina
        return {}
