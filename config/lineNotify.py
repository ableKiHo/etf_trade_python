import os

import requests


class LineNotify():
    # pip install requests
    def __init__(self):
        self.token = 'Bearer '
        self.getToken()

    def notification(self, message):
        headers = {'Authorization': self.token}
        url = 'https://notify-api.line.me/api/notify'
        data = {"message": message}

        resp = requests.post(url, headers=headers, data=data)
        # print("response status: %d" % resp.status_code)
        # print("response headers: %s" % resp.headers)
        # print("response body: %s" % resp.text)

    def getToken(self):
        token_file_path = "C:/stock/Authorization/Bearer.txt"
        if os.path.exists(token_file_path):
            f = open(token_file_path, "r", encoding="utf8")

            lines = f.readlines()
            for line in lines:
                if line != "":
                    self.token += line.rstrip('\n')

            f.close()