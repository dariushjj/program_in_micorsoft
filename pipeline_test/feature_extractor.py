import utils
import science_kit
from bs4 import BeautifulSoup
import networkx as nx
import json
import constants
import logging
import csv
import sys
import concurrent.futures
import os
csv.field_size_limit(sys.maxsize)

logger = logging.getLogger('feature_extractor')
logger.setLevel(logging.INFO)

class FeatureExtractor(object):
    def __init__(self, filename, vocab):
        self.domain = None
        # self.domain_data = dfs_data_line[self.domain]
        self.filename = filename
        self.url_to_features = dict()
        self.feature_bucket_boundaries_list = []

        self.success_href = []
        self.english_words_count_list = []
        self.article_count_list = []
        self.ratio_list = []
        self.max_sib_count_list = []
        self.authority_list = []
        self.vocab = vocab
        self.graph_of_url = None
        self.authority = {}

    def calc_raw_features(self):
        with constants.HDFS_client.read(constants.dfs_file_dir + self.filename, encoding='utf-8') as hdfs_reader:
            csv_reader = csv.DictReader(hdfs_reader, fieldnames=['url', 'soup'])
            for row in csv_reader:
                url = row['url']
                raw_html = row['soup']
                if raw_html == 'this_row_contains_domain':
                    self.domain = url
                    with constants.HDFS_client.read(constants.dfs_file_dir + utils.url_fine_grinding(self.domain) + '_graph_feature.json', encoding='utf-8') as graph_reader:
                        json_graph = json.load(graph_reader)['graph_feature']
                        self.graph_of_url = nx.readwrite.node_link_graph(json_graph)
                        _, self.authority = nx.hits(self.graph_of_url, max_iter=1000, tol=1e-08)
                        # todo: convergence not guaranteed, add try catch clause

                if raw_html:
                    try:
                        soup = BeautifulSoup(raw_html, 'html.parser')
                    except Exception as e:
                        logger.exception(e)
                    else:
                        self.success_href.append(url)
                        self.english_words_count_list.append(utils.count_english_words_in_url(url, self.vocab))
                        self.article_count_list.append(len(soup.find_all('article')))
                        self.max_sib_count_list.append(utils.get_max_consecutive_siblings_count(soup, ['p']))
                        self.ratio_list.append(utils.ratio_of_text_length(soup))
                        self.authority_list.append(self.authority[url])

    def calc_bucket_features(self):
        self.english_words_count_list, english_words_count_bucket_boundaries = science_kit.bucket_data(self.english_words_count_list)
        self.article_count_list, article_count_bucket_boundaries = science_kit.bucket_data(self.article_count_list)
        self.ratio_list, ratio_bucket_boundaries = science_kit.bucket_data(self.ratio_list)
        self.max_sib_count_list, max_sib_count_bucket_boundaries = science_kit.bucket_data(self.max_sib_count_list)
        self.authority_list, authority_bucket_boundaries = science_kit.bucket_data(self.authority_list)
        self.url_to_features.update(
            {self.success_href[i]: [self.max_sib_count_list[i], self.english_words_count_list[i],
                                    self.ratio_list[i], self.article_count_list[i], self.authority_list[i]]
             for i in range(len(self.success_href))}
        )

        self.feature_bucket_boundaries_list = [max_sib_count_bucket_boundaries, english_words_count_bucket_boundaries,
                                               ratio_bucket_boundaries, article_count_bucket_boundaries,
                                               authority_bucket_boundaries]

    def get_bucket_features(self):
        self.calc_raw_features()
        raw_feature = {self.success_href[i]: [self.max_sib_count_list[i], self.english_words_count_list[i],
                                              self.ratio_list[i], self.article_count_list[i], self.authority_list[i]]
                       for i in range(len(self.success_href))}
        self.calc_bucket_features()
        return self.url_to_features, self.feature_bucket_boundaries_list, raw_feature, self.domain


def test_handle(filename, vocab):
    ext = FeatureExtractor(filename, vocab)
    result = ext.get_bucket_features()
    with constants.HDFS_client.write("/user/ubuntu/raw_features/" + utils.url_fine_grinding(result[3]) + '_raw_features', encoding='utf-8', overwrite=True) as f:
        print(result[2])
        json.dump(result[2], f)
    with constants.HDFS_client.write("/user/ubuntu/features/" + utils.url_fine_grinding(result[3]) + '_features', encoding='utf-8', overwrite=True) as f:
        json.dump(result[0], f)


def multi_thread_test_handle(threads=os.cpu_count()+1):
    vocab = utils.build_english_vocab()
    future_dict = {}
    #file_name_list = constants.HDFS_client.list(constants.dfs_file_dir)
    file_name_list = {'https://codeascraft.com/category/search/', 'https://uxdesign.cc/ux-design-methods-deliverables-657f54ce3c7d',
     'https://codeascraft.com/category/api/', 'https://codeascraft.com/category/monitoring/',
     'https://codeascraft.com/category/people/', 'https://codeascraft.com/category/uncategorized/'}

    with concurrent.futures.ThreadPoolExecutor(max_workers=threads) as executor:
        for index, filename in enumerate(file_name_list):
            if '.json' not in filename and hash(filename) % constants.partition_size == constants.partition_index:
                future_dict.update({executor.submit(test_handle, filename, vocab): filename})
        for future in future_dict.keys():
            try:
                _ = future.result()
            except Exception as e:
                logger.exception(e)
                logger.info('fail')


if __name__ == '__main__':
    # logging.basicConfig(level=logging.INFO)
    multi_thread_test_handle()
