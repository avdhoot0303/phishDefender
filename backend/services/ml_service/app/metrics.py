import falcon

class MetricsResource:
    def on_get(self, req, resp):
        metrics = {
            "accuracy": 0.97,
            "precision": 0.95,
            "recall": 0.96,
            "f1_score": 0.95,
        }
        resp.media = metrics
        resp.status = falcon.HTTP_200
