from simon.scrap import Scrap
import falcon
import json

app = falcon.API()

scrap = Scrap()

class Home(object):
    def on_get(self, req, resp):
        resp.status = falcon.HTTP_200
        resp.content_type = 'text/html'
        with open('html/index.html', 'r') as f:
            resp.body = f.read()

app.add_route('/', Home())


class Scraping(object):
    def on_post(self, req, resp):
        resp.status = falcon.HTTP_200
        raw_json = req.stream.read()
        result_json = json.loads(raw_json)

        url = result_json['url']
        resp.body = scrap.getHTMLContent(url)


app.add_route('/scrap', Scraping())