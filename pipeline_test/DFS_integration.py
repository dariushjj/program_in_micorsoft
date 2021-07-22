import constants
from urllib import parse
import csv
import utils
import json
import logging
import concurrent.futures
import re
import networkx as nx
import multiprocessing
from networkx.readwrite import json_graph

# import feature_extractor
# import kmeans_only
logger = logging.getLogger('dfs')
logger.setLevel(logging.INFO)


def load_source():  # todo: this function is for testing
    # sites = set()
    with constants.HDFS_client.read("/user/ubuntu/dedup.json", encoding="UTF-8") as f:
        source_sites = json.load(f)
        assert constants.source_site_lower_bound < constants.source_site_upper_bound
        partition_workload = source_sites[constants.source_site_lower_bound:constants.source_site_upper_bound]
    return partition_workload


def workload_balance(total_workload, partitions, index):
    basic_share = total_workload//partitions
    remainder = total_workload % partitions
    if index < remainder:
        partition_workload = ((basic_share+1)*index, (basic_share+1)*(index+1))
    else:
        partition_workload = (basic_share*index+remainder, basic_share*(index+1)+remainder)
    return partition_workload


def dump_hdfs(base_site, url_list):
    try:
        assert isinstance(url_list, list)
    except AssertionError:
        logger.critical("input url_list must be a list")
    else:
        with constants.HDFS_client.write('/user/ubuntu/dfs-list/'+re.sub(r'https?://', "", base_site),
                                         encoding="UTF-8", overwrite=True) as f:
            json.dump(url_list, f)


def dfs_search_urls(domain):
    if domain[-1] != '/':
        domain += '/'
    soup_dict = {}
    graph_input = nx.DiGraph()
    full_url_list = list(utils.dfs_get_sub_page_hrefs_within_domain_hdfs(set(), utils.get_base_site_url(domain), domain,
                                                                         graph_input, soup_dict,  max_degree=constants.dfs_degree))

    with constants.HDFS_client.write(constants.dfs_file_dir + utils.url_fine_grinding(domain) + '_soup.csv', encoding='utf-8',
                                     overwrite=True) as hdfs_writer:  #todo: filename would be unsafe when running in clusers, will use hash
        header = ['url', 'soup']
        csv_writer = csv.DictWriter(hdfs_writer, fieldnames=header)
        csv_writer.writerow({'url': domain, 'soup': 'this_row_contains_domain'})
        for href in soup_dict.keys():
            csv_writer.writerow({'url': href, 'soup': soup_dict[href]})
        # json.dump({domain: {"all_soup": soup_dict, "all_url": full_url_list,
        #                     "graph_feature": json_graph.node_link_data(graph_input)}}, hdfs_writer)

    with constants.HDFS_client.write(constants.dfs_file_dir + utils.url_fine_grinding(domain) + '_graph_feature.json', encoding='utf-8',
                                     overwrite=True) as hdfs_writer:
        json.dump({'domain': domain, 'graph_feature': json_graph.node_link_data(graph_input)}, hdfs_writer)

    if full_url_list:
        return full_url_list
    else:
        return []


def start_multi_thread_dfs_search(threads=multiprocessing.cpu_count()+1):
    source_sites = load_source()
    with concurrent.futures.ThreadPoolExecutor(max_workers=threads) as executor:
        future_dict = {}
        for site in source_sites:
            future_dict.update({executor.submit(dfs_search_urls, site): site})

        for future in future_dict.keys():
            collected_site = future_dict[future]
            try:
                test = future.result()
                full_url_num = len(test)
                logger.info('site ' + collected_site + ' ' + str(full_url_num))
            except Exception as e:
                logger.exception(e)
                logger.info('failed site ' + collected_site)


if __name__ == '__main__':
    start_multi_thread_dfs_search()
