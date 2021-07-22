import utils
import info_extractor
import logging
import encodings
import random
import re
import datetime
import numpy as np
import science_kit
import json
import sys
from bs4 import BeautifulSoup


class PageIdentifier(object):
    def __init__(self, vocab, models):                    
        self.vocab = vocab        
        self.models = models
           
    def get_single_training_features(self, url):#input under domain url          
        vocab = self.vocab        
        extr = info_extractor.PageInfoExtractor(url, vocab)
        soup = extr.soup  
        if soup:            
            max_sib_count = utils.get_max_consecutive_siblings_count(soup, ['div', 'p'])
            english_words_count = utils.count_english_words_in_url(url, vocab)
            _, content_set = extr.dfs_get_all_ele_and_content()                        
            content_to_len = [len(ele.split()) for ele in content_set]
            ratio = science_kit.mean(science_kit.fetch_extreme_ele(content_to_len, 0.125, True))/science_kit.mean(science_kit.fetch_extreme_ele(content_to_len, 0.125, False))                 
        else:
            pass
        return [max_sib_count, english_words_count, ratio]
        
    def identify_pages(self, urls):    
        predict_classes = []
        for url in urls:
            domain = utils.get_base_site_url(url)
            model = self.models.get(domain, None)
            if model:
                features = self.get_single_training_features(url)
                feature_bucket_boundaries_list = model['feature_bucket_boundaries_list'] 
                bucketized_feature = []
                for i in range(len(features)):
                    bucketized_feature.append(science_kit.data_to_bucket_map(features[i], feature_bucket_boundaries_list[i]))
                #do predict
                if science_kit.l2_distance(model['cluster_centers'][0], bucketized_feature) > science_kit.l2_distance(model['cluster_centers'][1], bucketized_feature):
                    predict_classes.append(model['label_to_class']['0'])
                else:
                    predict_classes.append(model['label_to_class']['1'])
                          
        url_to_class = {k:v  for k,v in zip(urls, predict_classes)}
        return url_to_class

    def predict(models, url_to_features):
        result = {}
        for url in url_to_features:
            domain = utils.get_base_site_url(url)
            features = url_to_features[url]
            model = models.get(domain, 0)
            if not model:
                pass
            else:
                label_to_class = model['label_to_class']
                cluster_centers = model['cluster_centers']
                label = 0
                min_distance = sys.maxsize
                for i in range(len(cluster_centers)):
                    distance = science_kit.l2_distance(features, cluster_centers[i])
                    if distance < min_distance:
                        min_distance = distance
                        label = i
                    else:
                        pass
                cls = label_to_class[label]
                result.update({url:cls})