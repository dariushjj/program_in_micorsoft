import json


class Models(object):
    def __init__(self, model_path):
        self.model_path = model_path
        self.models = self.load_models()

    def load_models(self): 
        models = {}
        with open(self.model_path, encoding='utf-8') as f:
            while True:
                line = f.readline()
                if line:
                    model = json.loads(line.strip('\n'))                    
                    domain = model['domain']
                    model.pop('domain', None)
                    models.update({domain: model})
                else:
                    break
        return models
