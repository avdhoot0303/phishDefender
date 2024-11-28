import falcon



class TestCorsResource:
    def on_get(self, req, resp):
        resp.status = falcon.HTTP_200
        resp.media = {"message": "CORS test successful"}

