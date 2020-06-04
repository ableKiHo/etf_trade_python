import requests


class LineNotify():
    # pip install requests
    def __init__(self):
        self.token = 'Bearer XXXXXXXXX'

    def notification(self, message):
        headers = {'Authorization': self.token}
        url = 'https://notify-api.line.me/api/notify'
        data = {"message": message}

        resp = requests.post(url, headers=headers, data=data)
        # print("response status: %d" % resp.status_code)
        # print("response headers: %s" % resp.headers)
        # print("response body: %s" % resp.text)
