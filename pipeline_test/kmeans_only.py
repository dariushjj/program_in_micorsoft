import utils
import os
import concurrent.futures
import json
from sklearn.cluster import KMeans
import constants
from json import load
import logging

logger = logging.getLogger('kmeans')
logger.setLevel(logging.INFO)

def k_means_clustering(feature_dict, filename):

    # def label_to_class(cluster_centers):
    #     assert (len(cluster_centers) == 2)
    #     if (sum([cluster_centers[0][0] > cluster_centers[1][0], cluster_centers[0][1] > cluster_centers[1][1],
    #              cluster_centers[0][0] > cluster_centers[1][0]])
    #             > sum([cluster_centers[0][0] < cluster_centers[1][0], cluster_centers[0][1] < cluster_centers[1][1],
    #                    cluster_centers[0][0] < cluster_centers[1][0]])):
    #         return {0: 'article_page', 1: 'list_of_view'}
    #     else:
    #         return {1: 'article_page', 0: 'list_of_view'}

    def label_to_class(cluster_centers):
        assert (len(cluster_centers) == 2)
        if (sum([2*(cluster_centers[0][0] > cluster_centers[1][0]), cluster_centers[0][1] > cluster_centers[1][1],
                 cluster_centers[0][2] > cluster_centers[1][2], cluster_centers[0][3] < cluster_centers[1][3],
                 cluster_centers[0][4] < cluster_centers[1][4]])
                > sum([2*(cluster_centers[0][0] < cluster_centers[1][0]), cluster_centers[0][1] < cluster_centers[1][1],
                       cluster_centers[0][2] < cluster_centers[1][2], cluster_centers[0][3] > cluster_centers[1][3],
                       cluster_centers[0][4] > cluster_centers[1][4]])):
            return {0: 'article_page', 1: 'list_of_view'}
        else:
            return {1: 'article_page', 0: 'list_of_view'}

    url_list = list(feature_dict.keys())
    feature_list = [feature_dict[url] for url in url_list]
    kmeans = KMeans(n_clusters=2, random_state=0).fit(feature_list)
    labels = kmeans.labels_.tolist()

    cluster_centers = kmeans.cluster_centers_.tolist()
    label_to_class = label_to_class(cluster_centers)
    classes = [label_to_class[label] for label in labels]
    url_to_class = {k: v for k, v in zip(url_list, classes)}
    print(url_to_class)
    with constants.HDFS_client.write(constants.kmeans_result_dir+filename+'.json', encoding="UTF-8", overwrite=True) as f:
        json.dump(url_to_class, f)

    article_page_urls = []
    list_of_view_urls = []
    for url in url_to_class.keys():
        if url_to_class[url] == 'list_of_view':
            list_of_view_urls.append(url)
        else:
            article_page_urls.append(url)

    with constants.HDFS_client.write(constants.list_of_view_file_dir+filename+'.json', encoding='utf-8', overwrite=True) as f:
        json.dump(list_of_view_urls, f)
    with constants.HDFS_client.write(constants.article_page_dir+filename+'.json', encoding='utf-8', overwrite=True) as f:
        json.dump(article_page_urls, f)
    # return url_to_class, kmeans, label_to_class, cluster_centers, url_to_class  # data:dictionary[success_url:class]


def test_handle():
    file_name_list = constants.HDFS_client.list(constants.feature_file_dir)
    for index, filename in enumerate(file_name_list):
        with constants.HDFS_client.read(constants.feature_file_dir+filename, encoding='utf-8') as reader:
            url_feature_dict = load(reader)
            k_means_clustering(url_feature_dict, filename.split('_')[0])


def multi_thread_test_handle(threads=os.cpu_count()+1):
    file_name_list = constants.HDFS_client.list(constants.feature_file_dir)
    future_dict = {}
    with concurrent.futures.ThreadPoolExecutor(max_workers=threads) as executor:
        for index, filename in enumerate(file_name_list):
            if hash(filename) % constants.partition_size == constants.partition_index:
                with constants.HDFS_client.read(constants.feature_file_dir+filename, encoding='utf-8') as reader:  # 5features
                    url_feature_dict = load(reader)
                    future_dict.update({executor.submit(k_means_clustering, url_feature_dict, filename): filename})
        for future in future_dict.keys():
            try:
                _ = future.result()
            except Exception as e:
                logger.exception(e)
                logger.info('kmeans failed ')


if __name__ == '__main__':
    # logging.basicConfig(level=logging.INFO)
    multi_thread_test_handle()
