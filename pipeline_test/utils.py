import csv
from scipy import stats
import numpy as np
import sys
import functools
import requests
import time
from bs4 import BeautifulSoup
import logging as log
import re
import constants
import urllib.parse
import random
import json
from ast import literal_eval
import urllib
# import hdfs # imported for its Exception todo: import its exception only

logging = log.getLogger('utils')  # todo:this is the wrong method
logging.setLevel(log.INFO)

def is_english_paragraph(text, vocab):
    if text:
        pos_count = 0
        for w in text.split():
            if w.lower() in vocab or w in vocab:
                pos_count += 1
            else:
                pass
        if len(text.split()) == 0:
            return False
        else:
            if pos_count / len(text.split()) > 0.7:
                return True
            else:
                return False
    else:
        return False


def get_fresh_page_soup(url, timeout=3):
    try:
        cafile = constants.cafile
        headers = constants.headers
        html = requests.get(url, verify=cafile, headers=headers)
    except Exception as e:
        logging.exception(e)
        return None
    if html.status_code != 200:
            return None
    else:
        html.encoding = 'utf-8'
        logging.info("crawl succeed")
        soup = BeautifulSoup(html.text, 'html.parser')
        return soup

def get_page_soup(url, timeout=3):
    # try:
    #     cafile = constants.cafile
    #     headers = constants.headers
    #     proxy=random.choice(constants.proxies)
    #     proxy="117.196.237.71:45711"
    #     proxies={
    #              "https": proxy
    #              }
    #     html = requests.get(url, verify=cafile, headers=headers, timeout = 3)
    #     if html.status_code != 200:
    #         return None
    #     html.encoding = 'utf-8'
    #     logging.info("crawl succeed")
    #     soup = BeautifulSoup(html.text, 'html.parser')
    #     return soup
    # except Exception as e:
    #     logging.exception(e)
    #     return None
    try:
        cafile = constants.cafile
        headers = constants.headers1
        proxy = random.choice(constants.proxies)
        # proxies = {
        #                   "https": proxy
        #              }
        proxies = {'https':'https://' + proxy}
        # html = requests.get(url, verify=cafile, headers=constants.headers, proxies=proxies, timeout=3)
        html = requests.get(url, verify=cafile, headers=constants.headers, timeout=3)
    except Exception as e:
        logging.debug(e)
        logging.info("connection error on "+url)
        return None
    if html.status_code != 200:
            return None
    else:
        html.encoding = 'utf-8'
        logging.info("crawl succeed")
        soup = BeautifulSoup(html.text, 'html.parser')
        return soup


def float_range(x, upper, lower):
    if x >= upper and x < lower:
        return True
    else:
        return False


def test_generate_priorities(url_to_raw_priorities, std_num=3):
    raw_priorities = list(url_to_raw_priorities.values())
    assert (functools.reduce(lambda x, y: x and y, [p >= 0 for p in raw_priorities]))
    is_normal = False
    if len(url_to_raw_priorities) > 7:
        alpha = 1e-2
        _, p = stats.normaltest(list(url_to_raw_priorities.values()))
        if p > alpha:
            is_normal = True

    url_to_priorities = dict()
    std = np.std(raw_priorities)
    mean = np.mean(raw_priorities)
    if is_normal:
        bucket_boundaries = list(filter(lambda x: x > 0, [mean + i * std for i in range(-std_num, std_num + 1)]))
        bucket_boundaries.insert(0, 0)
        bucket_boundaries.append(sys.maxsize)
        for url in url_to_raw_priorities:
            for i in range(len(bucket_boundaries) - 1):
                if float_range(url_to_raw_priorities[url], bucket_boundaries[i], bucket_boundaries[i + 1]):
                    url_to_priorities.update({url: -i})
        return url_to_priorities
    else:
        step = std / 2
        bucket_boundaries = list(
            filter(lambda x: x > 0, [mean + i * step for i in range(-std_num * 2, std_num * 2 + 1)]))
        bucket_boundaries.insert(0, 0)
        bucket_boundaries.append(sys.maxsize)
        for url in url_to_raw_priorities:
            for i in range(len(bucket_boundaries) - 1):
                if float_range(url_to_raw_priorities[url], bucket_boundaries[i], bucket_boundaries[i + 1]):
                    url_to_priorities.update({url: -i})
        return url_to_priorities


def get_all_within_domain_href_from_url(domain, url):
    def get_href(ele):
        if ele.has_attr('href'):
            if ele['href'] not in ["", '/']:
                if '#' in ele['href']:
                    striped_block_link = ele['href'].split('#')[0]
                    if striped_block_link == '':
                        return None
                    elif striped_block_link[0] == '/':
                        return domain + ele['href'].split('#')[0]
                    else:
                        return domain + '/' + ele['href'].split('#')[0]
                else:
                    if bool(re.match(re.compile('^' + domain), ele['href'])):
                        return ele['href']
                    else:
                        if bool(re.match(re.compile('^www'), ele['href'])) or bool(
                                re.match(re.compile('^http'), ele['href'])):
                            return None
                        elif bool(re.match(re.compile('^//www'), ele['href'])):
                            return ele['href'][2:]
                        elif ele['href'][0] == '/':
                            return domain + ele['href']
                        else:
                            return domain + '/' + ele['href']

            else:
                return None
        else:
            return None

    try:
        soup = get_page_soup(url)
        a_elements = soup.find_all('a')
        result = set()
        for e in a_elements:
            get_href_result = get_href(e)
            if get_href_result:
                result.add(get_href_result)
            else:
                pass
        return result
    except Exception as e:
        logging.exception(e)
        return None


def get_all_within_domain_href_ele_from_url(domain, url):
    def get_href(ele):
        if ele.has_attr('href'):
            if ele['href'] not in ["", '/']:
                if '#' in ele['href']:
                    if ele['href'].split('#')[0]:
                        return ele
                    else:
                        return None
                else:
                    if bool(re.match(re.compile('^' + domain), ele['href'])):
                        return ele
                    else:
                        if bool(re.match(re.compile('^www'), ele['href'])) or bool(
                                re.match(re.compile('^http'), ele['href'])) or bool(
                                re.match(re.compile('^//www'), ele['href'])):
                            return None
                        else:
                            return ele
            else:
                return None
        else:
            return None

    try:
        soup = get_page_soup(url)
        a_elements = soup.find_all('a')
        result = set()
        for e in a_elements:
            get_href_result = get_href(e)
            if get_href_result:
                result.add(get_href_result)
            else:
                pass
        return result
    except Exception as e:
        logging.exception(e)
        return None


def get_all_href_ele_from_soup(soup, domain):  # this function now returns href: element dict
    def get_target_ele(ele):
        if ele.has_attr('href'):
            if ele['href'] not in ["", '/']:

                if '#' in ele['href']:
                    core_link = ele['href'].split('#')[0]
                    if core_link == '':
                        return None
                else:
                    core_link = ele['href']

                if bool(re.match(re.compile('^https?://'), core_link)):
                    if url_fine_grinding(domain) == url_fine_grinding(core_link):
                        return core_link
                    else:
                        return None

                elif bool(re.match(re.compile('^www'), core_link)):
                    if url_fine_grinding('http://' + core_link) == url_fine_grinding(domain):
                        return 'http://' + core_link
                    else:
                        return None

                elif bool(re.match(re.compile('^/[a-zA-Z0-9]'), core_link)):
                    return domain + core_link

                elif bool(re.match(re.compile('^//[a-zA-Z0-9]'), core_link)):
                    possible_full_url = core_link[2:]

                    if bool(re.match(re.compile('^https?://'), possible_full_url)):
                        if url_fine_grinding(possible_full_url) == url_fine_grinding(domain):
                            return possible_full_url
                        else:
                            return None

                    elif bool(re.match(re.compile('^www'), possible_full_url)):
                        if url_fine_grinding('http://' + possible_full_url) == url_fine_grinding(domain):
                            return 'http://' + possible_full_url
                        else:
                            return None

                    else:
                        if url_fine_grinding('http://' + possible_full_url) == url_fine_grinding(domain):
                            return 'http://' + possible_full_url
                        else:
                            return None    # a dangerous assumption
                else:
                    return None
        else:
            return None

    try:
        a_elements = soup.find_all('a')
        existing_hrefs = set()
        valid_elements = {}
        for element in a_elements:
            href = get_target_ele(element)
            if href is not None and href not in existing_hrefs:
                valid_elements.update({href: element})
                existing_hrefs.add(href)
        return valid_elements
    except Exception as e:
        logging.exception(e)
        return


def get_all_hrefs_from_soup(soup, domain):  # get all internal hrefs
    def get_href(ele):
        if ele.has_attr('href'):
            if ele['href'] not in ["", '/']:

                if '#' in ele['href']:
                    core_link = ele['href'].split('#')[0]
                    if core_link == '':
                        return None
                else:
                    core_link = ele['href']

                if bool(re.match(re.compile('^https?://'), core_link)):
                    if url_fine_grinding(domain) == url_fine_grinding(core_link):
                        return core_link
                    else:
                        return None

                elif bool(re.match(re.compile('^www'), core_link)):
                    if url_fine_grinding('http://' + core_link) == url_fine_grinding(domain):
                        return 'http://' + core_link
                    else:
                        return None

                elif bool(re.match(re.compile('^/[a-zA-Z0-9]'), core_link)):
                    return domain + core_link

                elif bool(re.match(re.compile('^//[a-zA-Z0-9]'), core_link)):
                    possible_full_url = core_link[2:]

                    if bool(re.match(re.compile('^https?://'), possible_full_url)):
                        if url_fine_grinding(possible_full_url) == url_fine_grinding(domain):
                            return possible_full_url
                        else:
                            return None

                    elif bool(re.match(re.compile('^www'), possible_full_url)):
                        if url_fine_grinding('http://' + possible_full_url) == url_fine_grinding(domain):
                            return 'http://' + possible_full_url
                        else:
                            return None

                    else:
                        if url_fine_grinding('http://' + possible_full_url) == url_fine_grinding(domain):
                            return 'http://' + possible_full_url
                        else:
                            return None    # a dangerous assumption
                else:
                    return None
        else:
            return None
    try:
        assert soup is not None
        a_elements = soup.find_all(re.compile('a'))
        result = set()
        for e in a_elements:
            get_href_result = get_href(e)
            if get_href_result and not url_contains_unwanted_elements(get_href_result):  # filter for videos
                result.add(get_href_result)
            else:
                pass
        return result

    except AssertionError:
        logging.info("soup is None")

    except Exception as e:
        logging.exception(e)
        return set()


def get_all_external_hrefs_from_soup(soup, domain):
    def get_href(ele):
        if ele.has_attr('href'):
            if ele['href'] not in ["", '/']:

                if '#' in ele['href']:
                    core_link = ele['href'].split('#')[0]
                    if core_link == '':
                        return None
                else:
                    core_link = ele['href']

                if bool(re.match(re.compile('^https?://'), core_link)):
                    if url_fine_grinding(domain) != url_fine_grinding(core_link):
                        return core_link
                    else:
                        return None

                elif bool(re.match(re.compile('^www'), core_link)):
                    if url_fine_grinding('http://' + core_link) != url_fine_grinding(domain):
                        return 'http://' + core_link
                    else:
                        return None

                elif bool(re.match(re.compile('^/[a-zA-Z0-9]'), core_link)):
                    return None

                elif bool(re.match(re.compile('^//[a-zA-Z0-9]'), core_link)):
                    possible_full_url = core_link[2:]

                    if bool(re.match(re.compile('^https?://'), possible_full_url)):
                        if url_fine_grinding(possible_full_url) != url_fine_grinding(domain):
                            return possible_full_url
                        else:
                            return None

                    elif bool(re.match(re.compile('^www'), possible_full_url)):
                        if url_fine_grinding('http://' + possible_full_url) != url_fine_grinding(domain):
                            return 'http://' + possible_full_url
                        else:
                            return None

                    else:
                        if url_fine_grinding('http://' + possible_full_url) != url_fine_grinding(domain):
                            return 'http://' + possible_full_url
                        else:
                            return None    # a dangerous assumption
                else:
                    return None
        else:
            return None
    try:
        a_elements = soup.find_all(re.compile('a'))
        result = set()
        for e in a_elements:
            get_href_result = get_href(e)
            if get_href_result and not url_contains_unwanted_elements(get_href_result):  # filterred videos
                result.add(get_href_result)
            else:
                pass
        return result

    except Exception as e:
        print(e)
        logging.exception(e)
        return set()


def get_all_hrefs_from_url(url):
    soup = get_page_soup(url)
    if soup:
        domain = get_base_site_url(url)
        hrefs = get_all_hrefs_from_soup(soup, domain)
        return hrefs
    else:
        return set()


# def get_all_hrefs_ele_from_url(url):
#     soup = get_page_soup(url)
#     href_eles = get_all_href_ele_from_soup(soup)
#     return href_eles


def dfs_get_sub_page_hrefs(visited_urls, url, max_degree=3):
    if url:
        visited_urls.add(url)
        hrefs = get_all_hrefs_from_url(url)
        result = hrefs
        if max_degree == 0:
            return result
        else:
            if not hrefs:
                return None
            else:
                for href in hrefs:
                    if href in visited_urls:
                        continue
                    else:
                        visited_urls.add(href)
                        sub_page_result = dfs_get_sub_page_hrefs(visited_urls, href, max_degree=max_degree - 1)
                        if sub_page_result:
                            result = result.union(sub_page_result)
                return result
    else:
        return None


def get_page_html(url):
    try:
        cafile = constants.cafile
        headers = constants.headers1
        proxy = random.choice(constants.proxies)
        # proxies = {
        #                   "https": proxy
        #              }
        proxies = {'https':'https://' + proxy}
        # html = requests.get(url, verify=cafile, headers=constants.headers, proxies=proxies, timeout=3)
        html = requests.get(url, verify=cafile, headers=constants.headers, timeout=3)
    except Exception as e:
        logging.debug(e)
        logging.info("connection error on "+url)
        return None
    if html.status_code != 200:
        logging.info("soupless: "+url)
        return None
    elif '\x00' in html.text:
        logging.info('wrong encoding on '+url)
        return None
    else:
        html.encoding = 'utf-8'
        logging.info("crawl succeed: "+url)
        return html.text


def dfs_get_sub_page_hrefs_within_domain_hdfs(visited_urls, domain, url, graph_input, soup_dict, max_degree=3):
    if url:
        visited_urls.add(url)
        html_text = get_page_html(url)
        logging.info("dfs degree: "+str(max_degree)+'_'+url)
        if not html_text:
            return set()
        soup_dict.update({url: html_text})
        soup = BeautifulSoup(html_text, 'html.parser')
        hrefs = get_all_hrefs_from_soup(soup, domain)
        time.sleep(0.5)
        result = hrefs
        update_graph(url, list(hrefs), graph_input)
        if max_degree == 0:
            if hrefs:
                soup_dict.update({href: get_page_html(href) for href in hrefs})
            return result
        else:
            if not hrefs:
                return None
            else:
                for href in hrefs:
                    if href in visited_urls:
                        continue
                    else:
                        visited_urls.add(href)
                        sub_page_result = dfs_get_sub_page_hrefs_within_domain_hdfs(visited_urls, domain, href, graph_input, soup_dict, max_degree=max_degree - 1)
                        if sub_page_result:
                            result = result.union(sub_page_result)
                        else:
                            pass
                return result
    else:
        return None


def dfs_get_sub_page_hrefs_within_domain(visited_urls, domain, url, max_degree=3):
    if url:
        visited_urls.add(url)
        soup = get_page_soup(url)
        hrefs = get_all_hrefs_from_soup(soup, domain)
        time.sleep(0.5)
        #hrefs = get_all_within_domain_href_from_url(domain, url)
        result = hrefs
        if max_degree == 0:
            return result
        else:
            if not hrefs:
                return None
            else:
                for href in hrefs:
                    if href in visited_urls:
                        continue
                    else:
                        visited_urls.add(href)
                        sub_page_result = dfs_get_sub_page_hrefs_within_domain(visited_urls, domain, href,
                                                                               max_degree=max_degree - 1)
                        if sub_page_result:
                            result = result.union(sub_page_result)
                        else:
                            pass
                return result
    else:
        return None


def build_english_vocab(vocab_path='/user/ubuntu/enriched_vocab.txt'):
    vocab = set()
    with constants.HDFS_client.read(vocab_path, encoding='utf-8', delimiter='\n') as f:
        for line in f:
            if line != "":
                vocab.add(line.strip('\r\n'))
    return vocab


def get_base_site_url(url):
    if str(url[:4]) == 'http':
        count_slash = 0
        result = ""
        for i, letter in enumerate(url):
            if letter == '/':
                if count_slash < 2:
                    count_slash += 1
                else:
                    result = url[:i]
                    break
        return result
    else:
        return ""


def get_relative_url(url):
    if url[:4] == 'http':
        count_slash = 0
        result = ""
        for i, letter in enumerate(url):
            if letter == '/':
                if count_slash < 2:
                    count_slash += 1
                else:
                    result = url[i + 1:]
                    break
        return result
    else:
        return url


def update_dictionary(dic, key, score_to_add):
    if key in dic:
        dic[key] += score_to_add
    else:
        dic[key] = 0
    return dic


def count_english_words_in_url(url, vocab):
    spl_relative_url = get_relative_url(url).split('/')
    max_english_count = 0
    for ele in spl_relative_url:
        english_word_count = 0
        for w in re.split('[^a-zA-Z\d\s]', ele):
            if w in vocab:
                english_word_count += 1
        if english_word_count > max_english_count:
            max_english_count = english_word_count

    return max_english_count


def get_max_consecutive_siblings_count(soup, target_tags):  # input a list of tags ['p','div']
    cur_consecutive_siblings_count = 0
    max_consecutive_siblings_count = 0
    p_eles = soup.find_all(target_tags)
    for i in range(1, len(p_eles)):
        if p_eles[i] == p_eles[i - 1].find_next_sibling():# do not use next_sibling, as it might yield '\n'
            cur_consecutive_siblings_count += 1
            if cur_consecutive_siblings_count > max_consecutive_siblings_count:
                max_consecutive_siblings_count = cur_consecutive_siblings_count
            else:
                continue
        else:
            cur_consecutive_siblings_count = 0

    return (max_consecutive_siblings_count + 1)


def get_relative_level(url):
    return get_relative_url(url).split('/')


def url_fine_grinding(url):
    domain_netloc = urllib.parse.urlparse(url)[1] # return value of urlparser is a tuple of 6 components
    fine_grind_domain_netloc = domain_netloc.split('.')
    useful_domain = ""
    if len(fine_grind_domain_netloc) <= 2:
        return fine_grind_domain_netloc[0]
    else:
        for index in range(1, len(fine_grind_domain_netloc)-1, 1):
            useful_domain += fine_grind_domain_netloc[index]
            if index != len(fine_grind_domain_netloc)-2:
                useful_domain += '.'
    return useful_domain


###new added
def ratio_of_text_length(soup):
    #soup = utils.get_page_soup(url=url)

    if soup:
        [s.extract() for s in soup(['script', 'span'])]
        contents = soup.find_all(['div', 'article', 'section'], {'class': re.compile('content|body|a|article|section|post')})
        length_list = []
        for idx, text_region in enumerate(contents):
            current_len = len(text_region.text.split())
            if current_len != 0:
                length_list.append(current_len)

        numofsentence = len(length_list)
        # sample_num_sentence = numofsentence // 8
        length_list.sort()
        if numofsentence == 0:
            return 0
        elif numofsentence < 8:
            upper = length_list[-1]
            lower = length_list[0]
            return upper/lower
        else:
            sample_num_sentence = numofsentence // 8
            upper_mean = sum(length_list[-sample_num_sentence:]) / sample_num_sentence
            lower_mean = sum(length_list[sample_num_sentence - 1:2 * sample_num_sentence - 1]) / sample_num_sentence
            upper_lower_mean_ratio = upper_mean / lower_mean
            # print("upper_lower_mean_ratio",upper_lower_mean_ratio)
            return upper_lower_mean_ratio
    else:
        return 0


def sum_target_amount_depth_product(soup, target):
    target_list = soup.find_all(target)
    result = 0
    depth = 0
    count = 0
    every_depth=[]
    for tgt in target_list:
        depth=0
        count += 1
        for parent in tgt.parents:
            depth += 1
        every_depth.append(depth)
        result += 1/depth
    return result, every_depth


def url_contains_unwanted_elements(url):           #filter urls that have unwanted elements
    #url_splitted=re.split('[^a-zA-Z\d\s]', url)
    #url_splitted = url.split('/')
    url_splitted = re.split('[./]', url)
    unwanted_elements = ['video', 'about', 'signup', 'sign-up', 'privacy', 'rss', 'login', 'pdf', 'useragreement',
                         'privacy-policy', 'privacy', 'policy', 'jpg', 'png', 'xml', 'facebook', 'instagram', 'twitter', 'linkedin']
    if any(ele in url_splitted for ele in unwanted_elements):
        return True
    else:
        return False


def update_graph(current_url, list_of_all_hrefs, graph):
    edge_list=[(current_url, href) for href in list_of_all_hrefs]
    graph.add_edges_from(edge_list)


##################### functions for Graph_Builder   #####################


def two_souce_sites_are_the_same(site_1, site_2, ratio):         #make sure two sites are same, for instance: bbc.com, bbc.co.uk
    if re.sub('^https?://', '', site_1) == re.sub('^https?://', '', site_2):
        return True
    else:
        site_1_soup = get_page_soup(site_1)
        site_2_soup = get_page_soup(site_2)
        site_1_hrefs = set(get_all_hrefs_from_soup(site_1_soup, site_1))
        site_2_hrefs = set(get_all_hrefs_from_soup(site_2_soup, site_2))
        intersection_hrefs_count = len(site_1_hrefs.intersection(site_2_hrefs))
        if intersection_hrefs_count >= ratio*max((len(site_1_hrefs), len(site_2_hrefs))):
            return True
        else:
            return False


def get_all_internal_and_external_hrefs_from_soup(soup, domain):
    def get_href(ele):
        if ele.has_attr('href'):
            if ele['href'] not in ["", '/']:

                if '#' in ele['href']:
                    core_link = ele['href'].split('#')[0]
                    if core_link == '':
                        return None
                else:
                    core_link = ele['href']

                if bool(re.match(re.compile('^https?://'), core_link)):
                    if url_fine_grinding(domain) != url_fine_grinding(core_link):
                        return ("external", core_link)
                    else:
                        return ("internal", core_link)

                elif bool(re.match(re.compile('^www'), core_link)):
                    if url_fine_grinding('http://' + core_link) != url_fine_grinding(domain):
                        return ("external", 'http://' + core_link)
                    else:
                        return ("internal", 'http://' + core_link)

                elif bool(re.match(re.compile('^/[a-zA-Z0-9]'), core_link)):
                    return None

                elif bool(re.match(re.compile('^//[a-zA-Z0-9]'), core_link)):
                    possible_full_url = core_link[2:]

                    if bool(re.match(re.compile('^https?://'), possible_full_url)):
                        if url_fine_grinding(possible_full_url) != url_fine_grinding(domain):
                            return ("external", possible_full_url)
                        else:
                            return ("internal", possible_full_url)

                    elif bool(re.match(re.compile('^www'), possible_full_url)):
                        if url_fine_grinding('http://' + possible_full_url) != url_fine_grinding(domain):
                            return ("external", 'http://' + possible_full_url)
                        else:
                            return ("internal", 'http://' + possible_full_url)

                    else:
                        if url_fine_grinding('http://' + possible_full_url) != url_fine_grinding(domain):
                            return ("external", 'http://' + possible_full_url)
                        else:
                            return ("internal", 'http://' + possible_full_url)    # a dangerous assumption
                else:
                    return None
        else:
            return None
    try:
        a_elements = soup.find_all(re.compile('a'))
        result_internal = set()
        result_external = set()
        for e in a_elements:
            get_href_result = get_href(e)
            if get_href_result and not url_contains_unwanted_elements(get_href_result[1]):      #filterred unwanted elements
                if get_href_result[0] == "external":
                    result_external.add(get_href_result[1])
                else:
                    result_internal.add(get_href_result[1])
            else:
                pass
        return (result_internal, result_external)

    except Exception as e:
        print(e)
        logging.exception(e)
        return (set(), set())

def dfs_get_external_hrefs_from_domain(visited_urls, domain, url, max_degree=3):
    if url:
        visited_urls.add(url)
        soup=get_page_soup(url)
        internal_hrefs, external_hrefs = get_all_internal_and_external_hrefs_from_soup(soup, domain)  #combined to one function finding external and internal hrefs
        # internal_hrefs=get_all_hrefs_from_soup(soup, domain)
        # external_hrefs=get_all_external_hrefs_from_soup(soup, domain)
        time.sleep(constants.sleep_time)
        #hrefs = get_all_within_domain_href_from_url(domain, url)
        result = {(url, external_href) for external_href in external_hrefs}
        if max_degree == 0:
            return result
        else:
            if not internal_hrefs:         #if get no internal_hrefs, return None
                return None
            else:
                for internal_href in internal_hrefs:
                    if internal_href in visited_urls:
                        continue
                    else:
                        visited_urls.add(internal_href)
                        sub_page_result = dfs_get_external_hrefs_from_domain(visited_urls, domain, internal_href,
                                                                               max_degree=max_degree - 1)
                        if sub_page_result:
                            result = result.union(sub_page_result)
                        else:
                            pass
                return result
    else:
        return None




def update_graph_external_version(current_url, list_of_all_hrefs, graph, source_sites):
    #input a list of external hrefs
    #firstly, make sure all sites within the range of 2300 source_sites
    #secondly, create a dictionary based on the frequence
    #thridly, make a list of edges in the format of (source_site, destination_site, weight)
    #lastly, add the edges to the graph

    # trimed_list_of_all_hrefs = [get_base_site_url(href) if get_base_site_url(href) != current_url and destination_site_is_part_of_source_site(href, source_sites)
    #                                                     else None for href in list_of_all_hrefs]
    trimed_list_of_all_hrefs = [get_base_site_url(href) if get_base_site_url(href) != current_url else None for href in list_of_all_hrefs]  #include hrefs out of range
    destination_sites_not_in_range = list(set(list_of_all_hrefs) - set(trimed_list_of_all_hrefs))  # find destination sites that not in range of 2300 source_sites
    frequency_dictionary = create_dictionary_of_frequency(trimed_list_of_all_hrefs)
    edge_list=[(current_url, destination_site, frequency_dictionary[destination_site]) for destination_site in frequency_dictionary]
    graph.add_weighted_edges_from(edge_list)
    print(edge_list)
    return edge_list

def create_dictionary_of_frequency(hrefs_list):
    frequency_dict={}
    for href in hrefs_list:
        if href:
            if not bool(re.match(re.compile('^https'), href)):        # if not start with https, must start with http, then replace http with https
                href = href.replace('http', 'https')
            if href in frequency_dict:
                frequency_dict[href] += 1
            else:
                frequency_dict[href] = 1
    return frequency_dict

def destination_site_is_part_of_source_site(href, source_urls):     #determine if the href is in the source_sites file, ignore https or http
    if not bool(re.match(re.compile('/$'), href)):       #if not end with '/', add it on
        href = href + '/'
    base_url=get_base_site_url(href)
    if not bool(re.match(re.compile('/$'), base_url)):       #if not end with '/', add it on
        base_url = base_url + '/'
    if bool(re.match(re.compile('^https'), base_url)):
        base_url = base_url.replace('htttps','http')

    if base_url in source_urls:
        return True
    else:
        base_url = base_url.replace('http', 'https')
        if base_url in source_urls:
            return True
        else:
            return False

command_for_CEMSEC_algorithm = 'python src/embedding_clustering.py --input data/graph_builder_edges.csv --embedding-output output/embeddings/graph_builder_embedding.csv --log-output output/cluster_means/graph_builder_means.csv --cluster-mean-output output/logs/graph_builder.json --assignment-output output/assignments/graph_of_url.json --cluster-number 6'
command_for = 'python src/main.py --layers 32 7 --edge-path input/graph_builder_edges.csv --output-path output/graph_builder_edges.csv --membership-path output/graph_builder_result.json'
def graph_to_int_node_edges_file(url_graph):    #save the file for GEMSEC algorithm
    edges_data = list(url_graph.edges.data())
    #edges_data = (url_graph.edges())
    #edges_without_weight = edges_data
    edges_without_weight = [[tuple[0], tuple[1], tuple[2]] for tuple in edges_data]
    new_source_urls_list = set()
    [new_source_urls_list.update({lst[0],lst[1]}) for lst in edges_without_weight]  #create it a new source_urls_list because of formatting problem
    num_to_url = {}   #create two dictionaries for us to change from num to url and reverse
    url_to_num = {}

    count = 0
    for url in new_source_urls_list:
        num_to_url[count] = url
        url_to_num[url] = count
        count = count + 1
    rows = [ [url_to_num[lst[0]], url_to_num[lst[1]], lst[2]['weight']] for lst in edges_without_weight ]  # change the edges to the format of numbers
    heads = ['node_1', 'node_2', 'weight']
    #save the data as csv file
    with open('graph_builder_edges_weight.csv', 'w')as f:
        f_csv = csv.writer(f)
        f_csv.writerow(heads)
        f_csv.writerows(rows)
    return num_to_url
#testing purpose
num_to_url_dict_testing = {0: 'https://mesosphere.com', 1: 'http://chiefexecutive.net/', 2: 'https://www.hanselman.com/', 3: 'https://www.cjr.org', 4: 'https://ello.co/', 5: 'http://gingearstudio.com/', 6: 'http://amir.rachum.com/', 7: 'http://www.foodtechconnect.com/', 8: 'http://uxmovement.com/', 9: 'http://blog.fullstory.com/', 10: 'https://www.niemanlab.org', 11: 'http://www.internethistorypodcast.com/', 12: 'https://cloudplatform.googleblog.com/', 13: 'https://blog.wealthfront.com', 14: 'https://growthhackers.com', 15: 'https://www.evanmiller.org', 16: 'https://thebolditalic.com/', 17: 'http://perspectives.mvdirona.com/', 18: 'https://25iq.com/', 19: 'https://entrepreneurs.maqtoob.com/', 20: 'http://www.techrepublic.com/', 21: 'http://lithub.com/', 22: 'https://marketingland.com', 23: 'https://www.artofmanliness.com', 24: 'https://www.racked.com/', 25: 'https://alistapart.com/', 26: 'https://lifehacker.com/', 27: 'https://intoli.com/', 28: 'https://blog.gojekengineering.com/', 29: 'http://blog.frontapp.com/', 30: 'https://madebymany.com/', 31: 'https://software-carpentry.org', 32: 'https://rachelbythebay.com', 33: 'https://platformed.info', 34: 'https://www.petekeen.net/', 35: 'https://tim.blog/', 36: 'https://slatestarcodex.com', 37: 'http://www.breakit.se/', 38: 'https://blogmaverick.com', 39: 'https://blogs.msdn.microsoft.com/', 40: 'https://sumome.com', 41: 'http://shayfrendt.com/', 42: 'http://www.breakingvc.com/', 43: 'https://www.drdobbs.com', 44: 'https://konklone.com', 45: 'https://robotlolita.me', 46: 'https://www.youtube.com/', 47: 'http://www.mtv.com/', 48: 'https://marshallhaas.com/', 49: 'https://amplitude.com/', 50: 'https://www.mercatus.org/', 51: 'https://konklone.com/', 52: 'https://panic.com', 53: 'http://robotlolita.me/', 54: 'http://mikeknoop.com/', 55: 'http://bits.blogs.nytimes.com/', 56: 'https://blog.jessfraz.com/', 57: 'https://www.jetbrains.com', 58: 'https://www.poynter.org/', 59: 'https://stackoverflow.blog', 60: 'https://blog.vivekpanyam.com/', 61: 'https://davidyat.es/', 62: 'https://42floors.com/', 63: 'https://www.danielk.se/', 64: 'https://www.usnews.com', 65: 'https://feross.org', 66: 'https://blog.openocean.vc/', 67: 'https://en.wikinews.org/', 68: 'https://rmurphey.com', 69: 'http://code.joejag.com/', 70: 'https://jacquesmattheij.com/', 71: 'http://www.wsj.com/', 72: 'https://www.hackisition.com/', 73: 'https://www.zdnet.com', 74: 'https://spin.atomicobject.com/', 75: 'https://blog.simon-frey.eu/', 76: 'http://www.useit.com/', 77: 'https://www.engadget.com', 78: 'http://www.tnooz.com/', 79: 'https://www.netmeister.org/', 80: 'http://engineering.skybettingandgaming.com/', 81: 'https://blog.usejournal.com', 82: 'https://akaptur.com', 83: 'https://www.adweek.com', 84: 'http://adage.com/', 85: 'https://python.sh/', 86: 'https://danluu.com', 87: 'https://startupljackson.com', 88: 'https://www.innoq.com/', 89: 'https://www.citylab.com/', 90: 'http://jrsinclair.com/', 91: 'https://boagworld.com/', 92: 'https://taylordavidson.com/', 93: 'https://www.ft.com', 94: 'https://fourweekmba.com/', 95: 'https://blog.httpwatch.com', 96: 'https://www.businessinsider.com', 97: 'https://mashable.com', 98: 'https://www.macrumors.com/', 99: 'https://blog.eladgil.com', 100: 'https://www.confluent.io/', 101: 'http://philippe.bourgau.net/', 102: 'https://blog.appcanary.com/', 103: 'http://crashworks.org/', 104: 'https://raptureinvenice.com/', 105: 'https://8thlight.com', 106: 'https://dzone.com/', 107: 'https://www.kennorton.com', 108: 'http://www.marcandangel.com/', 109: 'https://yourstory.com', 110: 'http://www.comscore.com/', 111: 'https://multithreaded.stitchfix.com', 112: 'https://motherboard.vice.com', 113: 'https://www.cosmopolitan.com', 114: 'https://blog.marvelapp.com', 115: 'https://ayende.com', 116: 'http://greatresearch.org/', 117: 'https://www.institutionalinvestor.com', 118: 'http://www.jetbrains.com/', 119: 'http://onstartups.com/', 120: 'https://engineering.pinterest.com', 121: 'http://blog.hootsuite.com/', 122: 'https://www.usv.com', 123: 'http://dupress.com/', 124: 'http://blog.rubygems.org/', 125: 'https://backlinko.com', 126: 'https://robgo.org', 127: 'http://www.motherjones.com/', 128: 'http://theanthill.org/', 129: 'https://bol.bna.com/', 130: 'https://www.uxpin.com/', 131: 'https://www.allthingsdistributed.com', 132: 'https://blog.alinelerner.com', 133: 'https://stackshare.io/', 134: 'http://lacker.io/', 135: 'https://startupboy.com', 136: 'https://al3x.net', 137: 'https://drewdevault.com', 138: 'https://gist.github.com/', 139: 'https://smallbusinessforum.co/', 140: 'https://www.gamasutra.com', 141: 'https://opensource.com/', 142: 'https://code.fb.com', 143: 'http://www.stilldrinking.org/', 144: 'https://www.bbc.com/', 145: 'https://www.airpair.com', 146: 'http://paulbuchheit.blogspot.com/', 147: 'https://dancounsell.com', 148: 'https://blog.eat24.com/', 149: 'https://moz.com/', 150: 'http://gabrielhauber.net/', 151: 'http://coglode.com/', 152: 'http://www.forentrepreneurs.com/', 153: 'http://www.publicbooks.org/', 154: 'http://robertheaton.com/', 155: 'http://www.telegraph.co.uk/', 156: 'http://blog.capwatkins.com/', 157: 'https://digital.com/', 158: 'https://rkoutnik.com/', 159: 'https://www.buzzfeed.com/', 160: 'http://ianlandsman.com/', 161: 'http://humbledmba.com/', 162: 'http://brucefwebster.com/', 163: 'https://iwantmyname.com', 164: 'https://blog.evernote.com', 165: 'https://timberry.bplans.com', 166: 'https://blog.algolia.com/', 167: 'https://www.gigamonkeys.com', 168: 'https://blog.alexmaccaw.com', 169: 'http://thenewandthenext.com/', 170: 'http://gsvtomorrow.com/', 171: 'https://www.mercurynews.com', 172: 'http://www.paperplanes.de/', 173: 'https://blog.samaltman.com', 174: 'http://simpleprogrammer.com/', 175: 'https://blog.lateral.io/', 176: 'http://freddestin.com/', 177: 'https://nymag.com', 178: 'https://mir.aculo.us', 179: 'http://journal.stuffwithstuff.com/', 180: 'http://elliot.land/', 181: 'http://blog.hubstaff.com/', 182: 'https://battellemedia.com', 183: 'https://www.ianhathaway.org', 184: 'https://om.co', 185: 'https://www.polygon.com/', 186: 'https://tynan.com', 187: 'https://nplusonemag.com/', 188: 'https://knowledge.sparkcapital.com', 189: 'https://www.anandtech.com', 190: 'https://threadreaderapp.com', 191: 'https://blog.sourcing.io', 192: 'https://hitenism.com/', 193: 'https://lemire.me/', 194: 'https://www.quora.com', 195: 'https://blog.gitprime.com', 196: 'http://blog.erratasec.com/', 197: 'https://theamericanscholar.org', 198: 'http://patshaughnessy.net/', 199: 'https://blog.ltse.com/', 200: 'http://goingconcern.com/', 201: 'http://wgross.net/', 202: 'http://www.startup-marketing.com/', 203: 'https://www.dataquest.io/', 204: 'http://blog.thefirehoseproject.com/', 205: 'https://gds.blog.gov.uk', 206: 'https://zandercutt.com/', 207: 'http://blog.arkency.com/', 208: 'https://www.nature.com', 209: 'http://blog.runkit.com/', 210: 'http://www.alistdaily.com/', 211: 'http://klinger.io/', 212: 'https://stackoverflow.blog/', 213: 'https://venturehacks.com', 214: 'https://joel.is', 215: 'https://joshbersin.com/', 216: 'https://openai.com/', 217: 'https://www.entrepreneur.com/', 218: 'https://markmanson.net', 219: 'https://www.aboveavalon.com/', 220: 'https://blog.doordash.com/', 221: 'https://www.gatesnotes.com', 222: 'https://www.box.com', 223: 'https://idlewords.com', 224: 'http://www.betaboston.com/', 225: 'https://techbeacon.com', 226: 'https://www.mindtheproduct.com/', 227: 'https://cpbotha.net/', 228: 'https://www.inc.com/', 229: 'https://auth0.com', 230: 'https://oversharing.substack.com/', 231: 'https://developers.soundcloud.com/', 232: 'http://whoo.ps/', 233: 'https://blog.rescuetime.com', 234: 'https://blog.acolyer.org', 235: 'https://news.greylock.com', 236: 'https://www.mckinsey.com', 237: 'https://www.vox.com/', 238: 'http://www.mr-stingy.com/', 239: 'https://johnmcelborough.com/', 240: 'https://blog.nugget.one/', 241: 'https://blakemasters.com', 242: 'http://www.universityaffairs.ca/', 243: 'https://varianceexplained.org', 244: 'http://bijansabet.com/', 245: 'http://calacanis.com/', 246: 'http://lizthedeveloper.com/', 247: 'https://www.kennorton.com/', 248: 'http://effinamazing.com/', 249: 'https://remysharp.com', 250: 'https://www.ft.com/', 251: 'https://www.institutionalinvestor.com/', 252: 'https://laughingmeme.org', 253: 'http://arnander.com/', 254: 'https://philipwalton.com', 255: 'https://eev.ee/', 256: 'http://cdixon.org/', 257: 'https://www.groovehq.com/', 258: 'http://kosamari.com/', 259: 'https://www.nylas.com', 260: 'https://www.epicgames.com', 261: 'https://www.latimes.com', 262: 'https://www.robinsloan.com/', 263: 'https://www.smashcompany.com', 264: 'https://realmensch.org/', 265: 'https://www.battery.com', 266: 'https://www.sequoiacap.com', 267: 'https://benbernardblog.com/', 268: 'https://summation.net/', 269: 'https://www.technologyreview.com', 270: 'https://www.crazyegg.com', 271: 'http://inessential.com/', 272: 'https://www.buzzfeednews.com', 273: 'http://blog.idonethis.com/', 274: 'https://blog.sentry.io/', 275: 'https://arxiv.org/', 276: 'http://hapgood.us/', 277: 'http://blog.sumall.com/', 278: 'https://engineering.udacity.com/', 279: 'http://www.dn.no/', 280: 'http://edunham.net/', 281: 'https://blog.scrapinghub.com/', 282: 'https://www.econsultancy.com/', 283: 'https://www.starterstory.com', 284: 'http://mailchi.mp/', 285: 'https://seldo.com', 286: 'https://joshtronic.com/', 287: 'https://founderchats.com/', 288: 'http://pointsandfigures.com/', 289: 'https://www.weave.works/', 290: 'https://blog.jessfraz.com', 291: 'https://c9.io/', 292: 'https://www.infoworld.com', 293: 'http://fractio.nl/', 294: 'https://www.wbur.org/', 295: 'https://blog.plan99.net/', 296: 'https://www.wikiwand.com', 297: 'https://www.nirandfar.com/', 298: 'https://blog.yell.com/', 299: 'https://bits.blogs.nytimes.com', 300: 'https://www.forentrepreneurs.com', 301: 'http://www.themarketingagents.com/', 302: 'https://thread.engineering/', 303: 'https://fymhotsauce.rocks/', 304: 'https://larahogan.me', 305: 'http://beets.io/', 306: 'http://www.conversion-uplift.co.uk/', 307: 'https://www.opensourcery.co.za/', 308: 'http://www.devdungeon.com/', 309: 'https://sethgodin.typepad.com', 310: 'https://www.robinsloan.com', 311: 'https://www.useit.com', 312: 'https://martinfowler.com/', 313: 'https://www.propublica.org/', 314: 'http://www.hokstad.com/', 315: 'https://www.wsj.com', 316: 'https://aeon.co', 317: 'https://redef.com', 318: 'https://www.zerotier.com/', 319: 'http://craigconnects.org/', 320: 'https://blog.kubernetes.io', 321: 'https://www.huffingtonpost.com', 322: 'https://factoryjoe.com/', 323: 'http://sz-magazin.sueddeutsche.de/', 324: 'http://movingfulcrum.com/', 325: 'http://www.barnetttalks.com/', 326: 'https://shkspr.mobi/', 327: 'https://blog.readme.io', 328: 'https://mattgemmell.com', 329: 'https://vimeo.com', 330: 'https://lethain.com/', 331: 'https://ma.tt/', 332: 'http://blog.aweissman.com/', 333: 'https://www.citusdata.com', 334: 'https://tech.affirm.com/', 335: 'https://thestyleofelements.org/', 336: 'https://sensortower.com', 337: 'https://savagethoughts.com/', 338: 'https://jocelyngoldfein.com/', 339: 'http://joelcalifa.com/', 340: 'https://bitquabit.com/', 341: 'https://www.benkuhn.net', 342: 'https://thinkgrowth.org/', 343: 'https://blog.drafted.us/', 344: 'https://lauraroeder.com/', 345: 'https://alexiskold.net', 346: 'https://charity.wtf', 347: 'https://delicioustacos.com/', 348: 'https://stripe.com', 349: 'https://www.axios.com', 350: 'https://scaleyourcode.com/', 351: 'http://paulhammant.com/', 352: 'https://unbounce.com', 353: 'https://blog.alexmaccaw.com/', 354: 'https://www.sonyaellenmann.com/', 355: 'https://www.polygon.com', 356: 'https://brandur.org', 357: 'https://www.fastcompany.com', 358: 'https://jocelyngoldfein.com', 359: 'https://www.deconstructconf.com', 360: 'https://www.sfgate.com', 361: 'https://trackchanges.postlight.com/', 362: 'https://www.motherjones.com', 363: 'https://blog.eat24.com', 364: 'https://www.washingtonpost.com/', 365: 'https://belitsoft.com/', 366: 'https://www.groupon.com/', 367: 'http://schlaf.me/', 368: 'https://theoutline.com/', 369: 'https://www.hidefsoftware.co.uk/', 370: 'https://www.kitchensoap.com', 371: 'https://www.appcues.com/', 372: 'https://www.marieclaire.com', 373: 'https://firstround.com/', 374: 'https://timharford.com', 375: 'https://42floors.com', 376: 'https://www.midiaresearch.com/', 377: 'https://redislabs.com/', 378: 'https://insimpleterms.blog/', 379: 'http://jakewins.com/', 380: 'http://www.zhubert.com/', 381: 'https://blog.doist.com/', 382: 'https://www.bvp.com/', 383: 'http://www.taos.com/', 384: 'https://babich.biz', 385: 'https://theintercept.com', 386: 'http://www.jeffbullas.com/', 387: 'http://jkglei.com/', 388: 'http://omerio.com/', 389: 'https://www.thestar.com', 390: 'https://www.productmanagerhq.com/', 391: 'https://www.kpcb.com', 392: 'https://firstround.com', 393: 'https://timeline.com/', 394: 'https://www.eugenewei.com/', 395: 'https://meltingasphalt.com/', 396: 'https://www.bbc.com', 397: 'https://www.atrium.co', 398: 'http://www.datastax.com/', 399: 'https://ferrucc.io/', 400: 'https://sivers.org/', 401: 'https://www.box.com/', 402: 'https://unclutterer.com/', 403: 'https://blog.aweissman.com', 404: 'https://blog.instapaper.com', 405: 'http://ben.balter.com/', 406: 'https://thebolditalic.com', 407: 'https://www.espn.com', 408: 'http://www.gamesradar.com/', 409: 'http://www.nature.com/', 410: 'https://ayende.com/', 411: 'http://joeyh.name/', 412: 'https://www.linux.com/', 413: 'http://variety.com/', 414: 'https://alexiskold.net/', 415: 'https://www.ybrikman.com/', 416: 'https://icons8.com/', 417: 'http://brianchang.info/', 418: 'http://www.mgadams.com/', 419: 'http://donmelton.com/', 420: 'http://initialized.com/', 421: 'http://www.designprinciplesftw.com/', 422: 'https://jameshfisher.com/', 423: 'http://www.complex.com/', 424: 'http://www.daemonology.net/', 425: 'http://hintjens.com/', 426: 'https://quoteinvestigator.com', 427: 'https://www.hackingwithswift.com/', 428: 'https://blog.mixpanel.com', 429: 'http://thewirecutter.com/', 430: 'https://seekingalpha.com', 431: 'https://waxy.org/', 432: 'http://hackingrevenue.com/', 433: 'https://www.asymco.com', 434: 'https://cloudplatform.googleblog.com', 435: 'http://www.jessyoko.com/', 436: 'https://www.defmacro.org', 437: 'https://blog.agilebits.com', 438: 'https://keen.io', 439: 'https://bgr.com', 440: 'https://venturehacks.com/', 441: 'https://increment.com', 442: 'https://hynek.me/', 443: 'https://www.weforum.org/', 444: 'https://increment.com/', 445: 'https://sensortower.com/', 446: 'https://www.macstories.net/', 447: 'https://aerotwist.com/', 448: 'https://hecate.co/', 449: 'https://futurism.com', 450: 'https://www.airpair.com/', 451: 'https://news.crunchbase.com/', 452: 'https://www.process.st', 453: 'http://atomico.com/', 454: 'https://dupress.com', 455: 'https://mailchi.mp', 456: 'https://staltz.com', 457: 'http://blog.capitalandgrowth.org/', 458: 'https://sprint.ly/', 459: 'https://www.pierrelechelle.com/', 460: 'https://80x24.net', 461: 'https://daniel.haxx.se/', 462: 'https://www.crainsnewyork.com', 463: 'https://www.businessweek.com', 464: 'http://elementaryos.org/', 465: 'http://www.goodhousekeeping.com/', 466: 'https://blog.honey.is/', 467: 'https://unreasonable.is/', 468: 'https://blogs.scientificamerican.com/', 469: 'http://www.netinstructions.com/', 470: 'https://www.epicgames.com/', 471: 'http://danlebrero.com/', 472: 'https://theamericanscholar.org/', 473: 'https://zef.me/', 474: 'http://dariusforoux.com/', 475: 'https://customerdevlabs.com', 476: 'https://stackingthebricks.com', 477: 'https://digiday.com/', 478: 'https://blog.hubstaff.com', 479: 'https://venturegeneratedcontent.com', 480: 'http://www.boredpanda.com/', 481: 'https://www.pgbovine.net', 482: 'https://medium.learningbyshipping.com', 483: 'http://www.apptamin.com/', 484: 'http://calebmadrigal.com/', 485: 'https://redmonk.com/', 486: 'https://blog.hubspot.com', 487: 'https://blog.jaredfriedman.com', 488: 'https://www.phillymag.com', 489: 'https://machinelearnings.co', 490: 'https://sudophilosophical.com', 491: 'http://blog.yhat.com/', 492: 'https://www.keyvalues.com', 493: 'https://sethvargo.com/', 494: 'https://carta.com', 495: 'https://blog.capwatkins.com', 496: 'http://carlosrdrz.es/', 497: 'https://www.wezm.net/', 498: 'http://jlongster.com/', 499: 'https://www.mindtools.com', 500: 'https://www.siliconvalleywatcher.com', 501: 'https://medium.com/', 502: 'https://www.sendwithus.com', 503: 'https://timeline.com', 504: 'http://eng.localytics.com/', 505: 'https://www.reforge.com', 506: 'https://textslashplain.com', 507: 'http://thejunkland.com/', 508: 'https://mentalfloss.com', 509: 'https://neugierig.org', 510: 'https://entrepreneurshandbook.co/', 511: 'https://www.esquire.com', 512: 'https://frontendnews.io/', 513: 'https://www.adamdsigel.com', 514: 'https://bravenewgeek.com', 515: 'http://typeform.com/', 516: 'https://www.marcandangel.com', 517: 'https://www.curbed.com/', 518: 'http://mattturck.com/', 519: 'https://www.sciencemag.org', 520: 'https://blog.cryptographyengineering.com/', 521: 'https://www.skilled.io/', 522: 'https://loupventures.com', 523: 'https://spectrum.ieee.org', 524: 'https://elie.net/', 525: 'http://dev.otto.de/', 526: 'http://blog.niraj.io/', 527: 'https://www.helpscout.net', 528: 'https://www.inverse.com/', 529: 'http://www.kpcb.com/', 530: 'https://a16z.com/', 531: 'https://webkit.org', 532: 'https://stories.appbot.co/', 533: 'https://www.prisonpolicy.org/', 534: 'http://hothardware.com/', 535: 'https://blog.ndepend.com/', 536: 'http://versiononeventures.com/', 537: 'http://blog.scalyr.com/', 538: 'https://blog.hubspot.com/', 539: 'https://www.esquire.com/', 540: 'https://engineering.gusto.com/', 541: 'http://vpnscam.com/', 542: 'https://www.olark.com/', 543: 'http://braythwayt.com/', 544: 'https://blogs.oracle.com/', 545: 'http://www.adambourg.com/', 546: 'http://www.thestar.com/', 547: 'https://jvns.ca/', 548: 'https://beingfa.com/', 549: 'https://500.co', 550: 'https://www.goodhousekeeping.com', 551: 'https://www.ostraining.com/', 552: 'https://stratechery.com/', 553: 'https://www.redhat.com', 554: 'https://www.thumbtack.com/', 555: 'https://www.appcues.com', 556: 'https://blogs.nvidia.com/', 557: 'https://blog.bufferapp.com', 558: 'https://blog.pragmaticengineer.com', 559: 'http://code.krister.ee/', 560: 'http://www.virtuouscode.com/', 561: 'https://www.curbed.com', 562: 'https://readthink.com', 563: 'https://segment.com/', 564: 'http://goodui.org/', 565: 'http://www.cosmopolitan.com/', 566: 'https://www.makeuseof.com', 567: 'https://simplystatistics.org', 568: 'https://eng.uber.com/', 569: 'https://chadfowler.com', 570: 'http://videofruit.com/', 571: 'https://www.hotjar.com/', 572: 'http://jackealtman.com/', 573: 'https://andreasgal.com/', 574: 'http://wade.be/', 575: 'https://www.macstories.net', 576: 'https://www.seattletimes.com', 577: 'https://blog.bradfieldcs.com', 578: 'https://dancounsell.com/', 579: 'https://referralrock.com/', 580: 'https://www.sendwithus.com/', 581: 'https://aerotwist.com', 582: 'https://developers.soundcloud.com', 583: 'http://www.theeffectiveengineer.com/', 584: 'https://www.salesforce.com/', 585: 'http://mentalfloss.com/', 586: 'https://www.vox.com', 587: 'https://mikeindustries.com', 588: 'http://benjaminreinhardt.com/', 589: 'https://news.nationalpost.com', 590: 'https://sqlite.org', 591: 'https://corgibytes.com', 592: 'https://www.quirksmode.org', 593: 'https://www.speedshop.co/', 594: 'https://venngage.com', 595: 'https://www.cbsnews.com/', 596: 'https://www.candyjapan.com/', 597: 'https://aphyr.com/', 598: 'https://opensource.com', 599: 'https://hackernewslater.com/', 600: 'http://www.callumhart.com/', 601: 'https://www.mindtools.com/', 602: 'https://scotthurff.com', 603: 'https://www.greenbiz.com/', 604: 'http://www.huffingtonpost.com/', 605: 'https://www.digitalocean.com', 606: 'http://www.midnightdba.com/', 607: 'http://stephaniehurlburt.com/', 608: 'https://www.livechatinc.com/', 609: 'https://trackchanges.postlight.com', 610: 'https://www.saastr.com/', 611: 'http://www.dailymail.co.uk/', 612: 'https://gigster.com/', 613: 'https://www.farnamstreetblog.com/', 614: 'https://martinfowler.com', 615: 'https://austinkleon.com/', 616: 'https://observer.com', 617: 'http://www.elegantcoding.com/', 618: 'https://codewords.recurse.com', 619: 'http://hopperanddropper.com/', 620: 'https://mike-bland.com/', 621: 'http://fortune.com/', 622: 'http://ionutn.com/', 623: 'https://www.braintreepayments.com/', 624: 'http://ramblinjan.com/', 625: 'http://warpspire.com/', 626: 'http://www.startuplessonslearned.com/', 627: 'https://www.thecut.com', 628: 'https://blog.buoyant.io', 629: 'https://www.popsci.com', 630: 'http://blog.wix.engineering/', 631: 'https://www.marieclaire.com/', 632: 'http://blog.dscout.com/', 633: 'https://www.cnet.com', 634: 'https://www.topic.com', 635: 'https://www.usenix.org', 636: 'https://zviband.com', 637: 'https://latenightcoding.co/', 638: 'https://moz.com', 639: 'https://jobs.netflix.com', 640: 'https://torrentfreak.com', 641: 'https://joreteg.com/', 642: 'https://pspdfkit.com', 643: 'https://www.theglobeandmail.com', 644: 'https://www.thewrap.com', 645: 'https://gaps.com/', 646: 'https://blog.siftscience.com', 647: 'http://blog.referralcandy.com/', 648: 'https://webkit.org/', 649: 'http://ryanhoover.me/', 650: 'https://greig.cc', 651: 'https://versionone.vc', 652: 'http://sriramk.com/', 653: 'https://www.cockroachlabs.com/', 654: 'https://ny.eater.com', 655: 'https://www.mediapost.com/', 656: 'https://www.25hoursaday.com', 657: 'https://www.slideshare.net', 658: 'https://david-smith.org/', 659: 'https://mic.com/', 660: 'https://kellanem.com', 661: 'https://deadspin.com', 662: 'https://praxis.fortelabs.co', 663: 'http://zurb.com/', 664: 'https://www.mtv.com', 665: 'http://www.collegian.psu.edu/', 666: 'https://www.uschamber.com/', 667: 'https://www.nczonline.net', 668: 'http://smerity.com/', 669: 'https://zapier.com', 670: 'https://blog.pinboard.in', 671: 'https://priceonomics.com', 672: 'https://tomtunguz.com', 673: 'https://www.theverge.com', 674: 'http://underthehood.meltwater.com/', 675: 'https://blog.halide.cam/', 676: 'https://www.behaviormodel.org/', 677: 'https://tomtunguz.com/', 678: 'https://hackeducation.com', 679: 'https://singularityhub.com', 680: 'https://paul.kinlan.me/', 681: 'http://szafranek.net/', 682: 'https://www.usv.com/', 683: 'https://www.manton.org', 684: 'http://blog.kubernetes.io/', 685: 'https://www.betaboston.com', 686: 'http://news.nationalpost.com/', 687: 'https://venturebeat.com/', 688: 'http://www.thisisgoingtobebig.com/', 689: 'https://fivethirtyeight.com', 690: 'https://producthabits.com', 691: 'https://steveblank.com', 692: 'https://fusion.net', 693: 'https://www.parhamdoustdar.com/', 694: 'https://www.reuters.com/', 695: 'http://engineering.foursquare.com/', 696: 'http://johngreathouse.com/', 697: 'http://anewdomain.net/', 698: 'https://en.wikinews.org', 699: 'https://thedailywtf.com', 700: 'https://www.sfchronicle.com', 701: 'https://nickcraver.com', 702: 'https://www.thedailybeast.com', 703: 'https://www.cbsnews.com', 704: 'https://talkingpointsmemo.com', 705: 'https://venturebeat.com', 706: 'http://simplystatistics.org/', 707: 'http://talkingpointsmemo.com/', 708: 'http://www.storypick.com/', 709: 'http://blog.reemer.com/', 710: 'https://blog.cleancoder.com', 711: 'http://carlcheo.com/', 712: 'https://www.infoq.com', 713: 'https://www.pagerduty.com/', 714: 'https://finance.yahoo.com', 715: 'http://www.datacenterknowledge.com/', 716: 'https://blog.usejournal.com/', 717: 'http://philcalcado.com/', 718: 'http://www.codeofhonor.com/', 719: 'https://blog.jessitron.com', 720: 'https://theoutline.com', 721: 'https://www.kalzumeus.com/', 722: 'http://khanlou.com/', 723: 'http://blog.brandonwang.ca/', 724: 'https://www.searchenginejournal.com', 725: 'https://www.priceintelligently.com', 726: 'https://searchenginewatch.com/', 727: 'https://goinglongblog.com', 728: 'https://pmeenan.com/', 729: 'https://kevq.uk/', 730: 'https://justinjackson.ca', 731: 'https://www.groupon.com', 732: 'http://stephencoyle.net/', 733: 'https://www.garyvaynerchuk.com', 734: 'https://serverlesscode.com/', 735: 'https://www.olark.com', 736: 'https://infrequently.org', 737: 'https://www.nngroup.com/', 738: 'https://codeascraft.com/', 739: 'https://docs.browserless.io/', 740: 'https://conversionxl.com/', 741: 'https://adespresso.com', 742: 'https://fundersclub.com/', 743: 'http://www.scriptcrafty.com/', 744: 'https://rollbar.com', 745: 'http://habitatchronicles.com/', 746: 'https://news.microsoft.com', 747: 'https://blog.canny.io/', 748: 'http://lowlevelbits.org/', 749: 'https://www.twilio.com', 750: 'http://slatestarcodex.com/', 751: 'https://www.feld.com', 752: 'https://blog.evernote.com/', 753: 'http://gawkerdata.kinja.com/', 754: 'https://kadavy.net', 755: 'https://www.trevormckendrick.com/', 756: 'https://spin.atomicobject.com', 757: 'https://foundationinc.co/', 758: 'http://influitive.io/', 759: 'http://www.fastcolabs.com/', 760: 'https://www.feld.com/', 761: 'http://blog.githawk.com/', 762: 'https://www.ldeakman.com', 763: 'http://jdlm.info/', 764: 'http://howardism.org/', 765: 'http://engineroom.teamwork.com/', 766: 'https://genius.com/', 767: 'https://freakonomics.com', 768: 'https://www.codeproject.com', 769: 'http://www.mikemcgarr.com/', 770: 'https://mic.com', 771: 'http://babich.biz/', 772: 'https://corner.squareup.com/', 773: 'http://abovethecrowd.com/', 774: 'https://www.reforge.com/', 775: 'https://www.highsnobiety.com', 776: 'http://robnapier.net/', 777: 'http://www.asahi.com/', 778: 'https://explore.reallygoodemails.com/', 779: 'http://www.aaronstannard.com/', 780: 'https://zapier.com/', 781: 'https://icons8.com', 782: 'https://crawshaw.io/', 783: 'http://blog.curtisherbert.com/', 784: 'http://www.ryanjfarley.com/', 785: 'https://hynek.me', 786: 'http://www.smashcompany.com/', 787: 'http://www.evanmiller.org/', 788: 'https://www.alexkras.com/', 789: 'http://randsinrepose.com/', 790: 'https://allenpike.com/', 791: 'https://githubengineering.com', 792: 'https://getpocket.com', 793: 'https://www.troyhunt.com', 794: 'https://news.microsoft.com/', 795: 'https://digitalcontentnext.org/', 796: 'https://stackingthebricks.com/', 797: 'http://smethur.st/', 798: 'https://blog.wealthfront.com/', 799: 'https://lifehacker.com', 800: 'https://ma.tt', 801: 'https://blog.keras.io/', 802: 'http://sophieshepherd.com/', 803: 'https://blog.coinbase.com/', 804: 'https://rollbar.com/', 805: 'http://seldo.com/', 806: 'https://www.thrillist.com', 807: 'https://medium.freecodecamp.org/', 808: 'http://bokardo.com/', 809: 'http://blog.naytev.com/', 810: 'http://okdork.com/', 811: 'https://www.varnish-cache.org', 812: 'http://www.theequitykicker.com/', 813: 'https://antirez.com', 814: 'https://cheddar.com', 815: 'https://nginx.com', 816: 'https://openai.com', 817: 'https://iwantmyname.com/', 818: 'https://meyerweb.com/', 819: 'https://www.battery.com/', 820: 'http://www.moishelettvin.com/', 821: 'http://laughingmeme.org/', 822: 'https://spectrum.ieee.org/', 823: 'https://about.gitlab.com/', 824: 'https://www.themuse.com', 825: 'https://movio.co/', 826: 'https://amplitude.com', 827: 'http://scottberkun.com/', 828: 'https://blog.cryptographyengineering.com', 829: 'https://www.rollingstone.com', 830: 'https://mobiledevmemo.com', 831: 'https://www.thedailybeast.com/', 832: 'https://www.paypal-engineering.com', 833: 'https://hypercritical.co', 834: 'https://www.starterstory.com/', 835: 'http://www.aaronkharris.com/', 836: 'http://web.archive.org/', 837: 'https://www.jacobinmag.com/', 838: 'https://points.datasociety.net', 839: 'https://conversionxl.com', 840: 'https://sparktoro.com', 841: 'https://www.forbes.com/', 842: 'https://techblog.badoo.com/', 843: 'https://www.gamasutra.com/', 844: 'https://philcalcado.com', 845: 'https://www.kalzumeus.com', 846: 'http://rodneybrooks.com/', 847: 'https://remysharp.com/', 848: 'https://www.troyhunt.com/', 849: 'https://redislabs.com', 850: 'https://www.alexkras.com', 851: 'http://www.manton.org/', 852: 'https://thenextweb.com', 853: 'http://reidhoffman.org/', 854: 'https://espn.go.com', 855: 'http://tonsky.me/', 856: 'https://xkcd.com', 857: 'http://boz.com/', 858: 'https://robinrendle.com', 859: 'https://www.quantcast.com', 860: 'http://priceonomics.com/', 861: 'https://www.confluent.io', 862: 'https://techpinions.com', 863: 'https://blog.linode.com/', 864: 'http://www.ianhathaway.org/', 865: 'https://www.theringer.com', 866: 'https://redditblog.com/', 867: 'https://www.theeffectiveengineer.com', 868: 'https://gettingreal.37signals.com', 869: 'https://www.mapbox.com', 870: 'https://drewdevault.com/', 871: 'https://daedtech.com', 872: 'http://blog.froont.com/', 873: 'https://www.bloomberg.com', 874: 'https://www.weave.works', 875: 'https://www.fastcolabs.com', 876: 'https://melmagazine.com', 877: 'https://radreads.co/', 878: 'https://paulromer.net/', 879: 'https://www.behaviormodel.org', 880: 'https://blog.acolyer.org/', 881: 'http://www.star-telegram.com/', 882: 'http://kevinlondon.com/', 883: 'https://www.mattcutts.com/', 884: 'https://www.sethlevine.com/', 885: 'https://f2.svbtle.com/', 886: 'https://uxmag.com', 887: 'https://infrequently.org/', 888: 'https://calacanis.com', 889: 'https://referralrock.com', 890: 'https://blog.cloudflare.com/', 891: 'https://sanctum.geek.nz/', 892: 'http://developer.telerik.com/', 893: 'https://www.bradford-delong.com', 894: 'https://blog.timac.org', 895: 'http://rigsomelight.com/', 896: 'http://madusudanan.com/', 897: 'https://www.twilio.com/', 898: 'http://www.thedrum.com/', 899: 'https://www.kencochrane.net/', 900: 'http://marketingland.com/', 901: 'http://roj.as/', 902: 'https://growthhackers.com/', 903: 'https://tim.blog', 904: 'http://wpcurve.com/', 905: 'http://www.macworld.com/', 906: 'https://medium.muz.li', 907: 'https://threadreaderapp.com/', 908: 'http://john.do/', 909: 'https://dcurt.is', 910: 'https://torrentfreak.com/', 911: 'https://www.npr.org', 912: 'https://www.thriveglobal.com/', 913: 'https://www.theguardian.com/', 914: 'https://nomasters.io/', 915: 'http://subtractioncapital.com/', 916: 'http://jasonevanish.com/', 917: 'https://nplusonemag.com', 918: 'https://www.gamesindustry.biz', 919: 'http://www.siliconvalleywatcher.com/', 920: 'https://blog.wikimedia.org', 921: 'https://genius.com', 922: 'http://www.haneycodes.net/', 923: 'http://www.thehotiron.com/', 924: 'https://www.lukew.com/', 925: 'http://www.jessesquires.com/', 926: 'http://pingdom.com/', 927: 'https://ireneau.com/', 928: 'http://limn.it/', 929: 'https://www.crazyegg.com/', 930: 'http://www.seattletimes.com/', 931: 'https://blog.pragmaticengineer.com/', 932: 'https://danluu.com/', 933: 'http://www.shirky.com/', 934: 'https://www.startup-marketing.com', 935: 'https://www.catehuston.com', 936: 'https://points.datasociety.net/', 937: 'https://anewdomain.net', 938: 'http://www.marketingsherpa.com/', 939: 'https://bettereveryday.vc/', 940: 'https://www.tbray.org', 941: 'https://larahogan.me/', 942: 'http://blog.rongarret.info/', 943: 'https://engineering.pinterest.com/', 944: 'https://www.mountaingoatsoftware.com', 945: 'https://www.aarp.org/', 946: 'https://codeascraft.com', 947: 'http://blog.elizabethyin.com/', 948: 'https://hajak.se/', 949: 'https://savagethoughts.com', 950: 'https://gregoryszorc.com', 951: 'https://glyph.twistedmatrix.com/', 952: 'https://uxplanet.org/', 953: 'https://melmagazine.com/', 954: 'https://bravenewgeek.com/', 955: 'https://www.pipelinedb.com/', 956: 'https://www.datacenterknowledge.com', 957: 'https://www.computerhistory.org', 958: 'http://blogs.tedneward.com/', 959: 'http://www.yes-www.org/', 960: 'https://www.citusdata.com/', 961: 'http://www.omgubuntu.co.uk/', 962: 'https://svpow.com/', 963: 'http://nvie.com/', 964: 'https://www.theinformation.com/', 965: 'https://sloanreview.mit.edu/', 966: 'https://coglode.com', 967: 'http://jordansmith.io/', 968: 'https://shift.newco.co/', 969: 'https://itsyourturnblog.com/', 970: 'http://kamranahmed.info/', 971: 'https://paul.kinlan.me', 972: 'https://gds.blog.gov.uk/', 973: 'https://evertpot.com/', 974: 'http://etodd.io/', 975: 'https://thewalrus.ca/', 976: 'https://www.mediapost.com', 977: 'https://ronjeffries.com', 978: 'https://www.economist.com/', 979: 'https://eng.uber.com', 980: 'https://blog.flickr.net/', 981: 'http://baatz.io/', 982: 'http://casnocha.com/', 983: 'http://blog.garrytan.com/', 984: 'https://www.theequitykicker.com', 985: 'http://mobiledevmemo.com/', 986: 'https://nextviewventures.com', 987: 'https://www.aerogrammestudio.com/', 988: 'https://www.uie.com', 989: 'https://blog.doit-intl.com/', 990: 'http://www.afr.com/', 991: 'http://www.multunus.com/', 992: 'https://auth0.com/', 993: 'https://knowyourmeme.com', 994: 'https://www.sandimetz.com', 995: 'http://kk.org/', 996: 'http://www.bradford-delong.com/', 997: 'https://blog.disqus.com/', 998: 'http://www.gamification.co/', 999: 'https://daedtech.com/', 1000: 'http://www.marclaidlaw.com/', 1001: 'https://krebsonsecurity.com', 1002: 'https://www.informit.com', 1003: 'https://appium.io', 1004: 'https://uxdesign.cc', 1005: 'https://bokardo.com', 1006: 'http://jitha.me/', 1007: 'http://fusion.net/', 1008: 'https://stateofprogress.blog/', 1009: 'http://www.journalism.org/', 1010: 'https://www.washingtonpost.com', 1011: 'https://nathanbarry.com', 1012: 'https://olivierlacan.com/', 1013: 'https://jonathanmendezblog.com/', 1014: 'https://www.nytimes.com/', 1015: 'https://www.entrepreneur.com', 1016: 'https://kk.org', 1017: 'https://austinkleon.com', 1018: 'https://timkadlec.com', 1019: 'https://www.joshlehman.com', 1020: 'https://www.growthengblog.com/', 1021: 'https://blog.getcrossbeam.com/', 1022: 'https://codeblog.jonskeet.uk', 1023: 'https://www.recode.net/', 1024: 'http://blog.danielna.com/', 1025: 'http://www.computerhistory.org/', 1026: 'https://tinyletter.com', 1027: 'https://code.fb.com/', 1028: 'https://www.luca-dellanna.com/', 1029: 'https://insimpleterms.blog', 1030: 'http://www.nearform.com/', 1031: 'http://www.elasticsearch.org/', 1032: 'http://appium.io/', 1033: 'http://www.anandtech.com/', 1034: 'https://99u.com', 1035: 'https://blog.kissmetrics.com', 1036: 'https://patshaughnessy.net', 1037: 'https://www.voicebot.ai/', 1038: 'http://hypercritical.co/', 1039: 'https://dl.dropboxusercontent.com', 1040: 'https://www.startuplessonslearned.com', 1041: 'https://tech.instacart.com/', 1042: 'http://www.crainsnewyork.com/', 1043: 'https://arstechnica.com', 1044: 'http://99u.com/', 1045: 'https://highscalability.com', 1046: 'http://tribebooster.com/', 1047: 'https://geshan.com.np/', 1048: 'https://krebsonsecurity.com/', 1049: 'https://blog.prototypr.io/', 1050: 'http://www.activestate.com/', 1051: 'https://circleci.com', 1052: 'http://www.popsci.com/', 1053: 'http://reprints.longform.org/', 1054: 'https://www.bhorowitz.com', 1055: 'https://blog.even.com/', 1056: 'https://movio.co', 1057: 'https://blog.asana.com/', 1058: 'https://www.theverge.com/', 1059: 'http://www.davefarley.net/', 1060: 'https://philipwalton.com/', 1061: 'https://badassadvisors.com/', 1062: 'https://www.hanselman.com', 1063: 'https://www.theglobeandmail.com/', 1064: 'https://digitalcontentnext.org', 1065: 'https://www.raywenderlich.com', 1066: 'https://backlinko.com/', 1067: 'https://queue.acm.org', 1068: 'https://blog.flickr.net', 1069: 'https://www.wired.com/', 1070: 'https://onstartups.com', 1071: 'http://blog.wesleyac.com/', 1072: 'http://hackcareer.com/', 1073: 'https://uxdesign.cc/', 1074: 'https://seths.blog', 1075: 'https://blog.daftcode.pl/', 1076: 'http://freakonomics.com/', 1077: 'http://news.harvard.edu/', 1078: 'https://c9.io', 1079: 'http://www.informit.com/', 1080: 'https://www.intercom.com', 1081: 'http://sixteenventures.com/', 1082: 'https://blog.usefomo.com/', 1083: 'https://alexisohanian.com', 1084: 'https://mikeindustries.com/', 1085: 'https://www.indiehackers.com', 1086: 'https://news.techmeme.com', 1087: 'https://blog.clevertap.com', 1088: 'https://hacks.mozilla.org/', 1089: 'https://www.desiringgod.org', 1090: 'http://blog.andyjiang.com/', 1091: 'http://blog.cultureamp.com/', 1092: 'https://hunterwalk.com', 1093: 'https://www.l2inc.com/', 1094: 'https://www.artsy.net/', 1095: 'http://akaptur.com/', 1096: 'http://battellemedia.com/', 1097: 'http://blog.matthewskelton.net/', 1098: 'https://henrikwarne.com/', 1099: 'http://alifeofproductivity.com/', 1100: 'http://www.outkickthecoverage.com/', 1101: 'https://www.hotjar.com', 1102: 'https://www.elastic.co', 1103: 'https://mfbt.ca/', 1104: 'http://unbounce.com/', 1105: 'https://dresscode.renttherunway.com', 1106: 'https://anders.unix.se/', 1107: 'https://www.elephate.com/', 1108: 'https://www.paperplanes.de', 1109: 'https://m.subbu.org/', 1110: 'https://www.zenefits.com', 1111: 'https://blog.ladder.io/', 1112: 'https://www.thoughtworks.com/', 1113: 'https://pichsenmeister.com/', 1114: 'https://www.popularmechanics.com', 1115: 'https://www.citylab.com', 1116: 'https://engineeringblog.yelp.com/', 1117: 'https://daslee.me', 1118: 'https://digg.com', 1119: 'https://blog.scottnonnenberg.com/', 1120: 'https://denzhadanov.com/', 1121: 'http://learn.onemonth.com/', 1122: 'https://money.cnn.com', 1123: 'https://programmingisterrible.com', 1124: 'https://webaim.org/', 1125: 'http://theearlyhour.com/', 1126: 'https://sloanreview.mit.edu', 1127: 'https://marco.org', 1128: 'https://customer.io/', 1129: 'https://www.theatlantic.com', 1130: 'https://redmonk.com', 1131: 'http://multithreaded.stitchfix.com/', 1132: 'https://blog.marvelapp.com/', 1133: 'http://blog.launchdarkly.com/', 1134: 'https://seths.blog/', 1135: 'http://blog.d3in.org/', 1136: 'http://thecodist.com/', 1137: 'https://www.ebayinc.com/', 1138: 'https://aws.amazon.com', 1139: 'http://www.holovaty.com/', 1140: 'https://www.mercurynews.com/', 1141: 'https://18f.gsa.gov', 1142: 'http://scotthurff.com/', 1143: 'https://thehftguy.com/', 1144: 'https://blog.mixpanel.com/', 1145: 'https://empireflippers.com/', 1146: 'https://blog.semilshah.com', 1147: 'https://www.cl.cam.ac.uk', 1148: 'https://overreacted.io/', 1149: 'https://www.goodcall.com/', 1150: 'https://www.recode.net', 1151: 'https://chris.beams.io/', 1152: 'https://blog.risingstack.com', 1153: 'http://www.eofire.com/', 1154: 'https://blog.elev.io/', 1155: 'https://www.influxdata.com', 1156: 'https://brianbalfour.com', 1157: 'https://entrepreneurshandbook.co', 1158: 'https://blog.optimizely.com', 1159: 'https://blog.bradfieldcs.com/', 1160: 'https://www.igvita.com', 1161: 'https://articles.fortawesome.com/', 1162: 'https://techcrunch.com/', 1163: 'https://www.snellman.net', 1164: 'http://jeremyaboyd.com/', 1165: 'https://blog.longreads.com/', 1166: 'http://blog.benjamin-encz.de/', 1167: 'http://nobi.com/', 1168: 'http://lean.vc/', 1169: 'https://www.objc.io', 1170: 'http://blog.openviewpartners.com/', 1171: 'http://highscalability.com/', 1172: 'http://blog.jaredsinclair.com/', 1173: 'http://www.drmaciver.com/', 1174: 'https://hackernoon.com', 1175: 'https://www.nczonline.net/', 1176: 'https://sneakerheadvc.com/', 1177: 'https://queue.acm.org/', 1178: 'https://joecmarshall.com/', 1179: 'https://honeycomb.io', 1180: 'https://robhope.com/', 1181: 'https://www.minnpost.com', 1182: 'https://www.nateberkopec.com', 1183: 'https://slash7.com', 1184: 'http://www.gamesbrief.com/', 1185: 'https://infinum.co', 1186: 'https://thewirecutter.com', 1187: 'https://www.michaelrwolfe.com', 1188: 'https://adage.com', 1189: 'http://jayshah.me/', 1190: 'http://dev-human.com/', 1191: 'http://malisper.me/', 1192: 'https://blogs.dropbox.com/', 1193: 'https://blog.sentry.io', 1194: 'https://www.smashingmagazine.com/', 1195: 'http://wp.sigmod.org/', 1196: 'https://web.archive.org', 1197: 'https://www.reddit.com/', 1198: 'https://fi.co/', 1199: 'https://www.quantcast.com/', 1200: 'https://float-middle.com/', 1201: 'https://greenteapress.com', 1202: 'http://www.newsweek.com/', 1203: 'http://erikrood.com/', 1204: 'https://www.hodinkee.com/', 1205: 'https://thinkpiece.club/', 1206: 'http://blog.docker.com/', 1207: 'http://hbswk.hbs.edu/', 1208: 'https://engineering.videoblocks.com/', 1209: 'https://www.vanityfair.com/', 1210: 'https://www.yegor256.com', 1211: 'http://buytaert.net/', 1212: 'http://debarghyadas.com/', 1213: 'https://www.enterprisetech.com', 1214: 'https://www.nickkolenda.com/', 1215: 'http://blog.louisgray.com/', 1216: 'http://enterprisecraftsmanship.com/', 1217: 'http://www.makeuseof.com/', 1218: 'http://blog.edtechie.net/', 1219: 'https://dzone.com', 1220: 'http://www.rancher.io/', 1221: 'https://algeri-wong.com', 1222: 'https://grasshopper.com/', 1223: 'http://blog.spearhead.co/', 1224: 'https://www.usnews.com/', 1225: 'https://news.realm.io', 1226: 'https://pasztor.at/', 1227: 'https://www.wired.com', 1228: 'http://drillin.gs/', 1229: 'https://ny.eater.com/', 1230: 'https://mcfunley.com', 1231: 'https://paulgraham.com', 1232: 'https://bitquabit.com', 1233: 'http://www.rockpapershotgun.com/', 1234: 'https://blog.codinghorror.com/', 1235: 'https://ma.ttias.be', 1236: 'https://www.sec.gov', 1237: 'https://blog.louisgray.com', 1238: 'http://www.gamesindustry.biz/', 1239: 'http://www.stackbuilders.com/', 1240: 'http://www.referralsaasquatch.com/', 1241: 'http://www.sandimetz.com/', 1242: 'https://deardesignstudent.com/', 1243: 'https://www.fast.ai', 1244: 'http://blog.bodellconsulting.com/', 1245: 'https://www.raptitude.com/', 1246: 'http://www.zdnet.com/', 1247: 'https://www.justin.tv', 1248: 'http://ardalis.com/', 1249: 'https://www.thoughtworks.com', 1250: 'https://mattermark.com', 1251: 'https://blog.fugue.co/', 1252: 'https://www.intelligentchange.com/', 1253: 'https://react-etc.net', 1254: 'https://cmd-t.webydo.com/', 1255: 'https://www.raywenderlich.com/', 1256: 'https://phrack.org', 1257: 'https://www.craigslist.org', 1258: 'https://chrisreining.com/', 1259: 'https://daringfireball.net/', 1260: 'http://blog.restcase.com/', 1261: 'http://www.sellbrite.com/', 1262: 'http://www.phillymag.com/', 1263: 'http://nautil.us/', 1264: 'https://craigmod.com/', 1265: 'https://blog.drift.com', 1266: 'https://www.momenteo.com/', 1267: 'http://mir.aculo.us/', 1268: 'https://www.saastr.com', 1269: 'https://sizovs.net', 1270: 'https://blog.benjamin-encz.de', 1271: 'https://leanstack.com/', 1272: 'http://www.jasonshen.com/', 1273: 'https://sizovs.net/', 1274: 'http://www.chris-granger.com/', 1275: 'https://myers.io/', 1276: 'https://engineering.khanacademy.org', 1277: 'https://www.linux.com', 1278: 'http://www.aberdeeninvestment.com/', 1279: 'https://howmuch.net/', 1280: 'https://ashfurrow.com/', 1281: 'http://danshipper.com/', 1282: 'https://www.techinasia.com', 1283: 'http://thedailywtf.com/', 1284: 'http://blog.alinelerner.com/', 1285: 'http://www.jointventure.org/', 1286: 'http://engineering.khanacademy.org/', 1287: 'https://brucefwebster.com', 1288: 'https://www.poynter.org', 1289: 'http://blog.eladgil.com/', 1290: 'http://dgovil.com/', 1291: 'http://www.mckinsey.com/', 1292: 'http://reallifemag.com/', 1293: 'https://www.racked.com', 1294: 'https://www.nfx.com/', 1295: 'https://chiefexecutive.net', 1296: 'https://www.l2inc.com', 1297: 'https://sixteenventures.com', 1298: 'https://www.joyent.com', 1299: 'https://boagworld.com', 1300: 'https://blog.creandum.com/', 1301: 'https://www.coelevate.com', 1302: 'https://textslashplain.com/', 1303: 'https://hbr.org', 1304: 'https://zachholman.com', 1305: 'https://bradfrost.com', 1306: 'https://blog.wix.engineering', 1307: 'https://quip.com', 1308: 'https://www.silvestarbistrovic.from.hr/', 1309: 'https://www.linfo.org', 1310: 'https://www.theatlantic.com/', 1311: 'http://quoteinvestigator.com/', 1312: 'https://www.theringer.com/', 1313: 'https://www.oreilly.com', 1314: 'https://www.uxpin.com', 1315: 'http://www.b-list.org/', 1316: 'http://alexandros.resin.io/', 1317: 'https://500ish.com', 1318: 'https://segment.com', 1319: 'https://www.engadget.com/', 1320: 'http://www.shubhro.com/', 1321: 'https://sendgrid.com', 1322: 'https://www.multicians.org', 1323: 'https://blog.stephenwolfram.com/', 1324: 'http://foundation.bz/', 1325: 'https://ashfurrow.com', 1326: 'https://www.skilled.io', 1327: 'https://visible.vc/', 1328: 'https://www.cracked.com', 1329: 'https://zhuanlan.zhihu.com', 1330: 'https://www.cjr.org/', 1331: 'https://blog.pinboard.in/', 1332: 'https://8thlight.com/', 1333: 'https://ponyfoo.com/', 1334: 'https://blog.openstreetmap.org/', 1335: 'https://blog.invisionapp.com', 1336: 'https://tech.polyconseil.fr/', 1337: 'http://jwegan.com/', 1338: 'https://digiday.com', 1339: 'http://blog.lmorchard.com/', 1340: 'https://craigmod.com', 1341: 'https://ux.useronboard.com/', 1342: 'https://blog.wikimedia.org/', 1343: 'https://www.deconstructconf.com/', 1344: 'http://minimaxir.com/', 1345: 'https://crate.io', 1346: 'https://foliovision.com/', 1347: 'https://reidhoffman.org', 1348: 'http://www.cracked.com/', 1349: 'https://intoli.com', 1350: 'https://www.techrepublic.com', 1351: 'https://www.nytimes.com', 1352: 'https://jezebel.com', 1353: 'http://www.natesullivan.com/', 1354: 'https://www.figma.com/', 1355: 'https://www.innoq.com', 1356: 'https://design.google/', 1357: 'http://nymag.com/', 1358: 'https://www.comscore.com', 1359: 'https://caseyaccidental.com', 1360: 'http://www.espn.com/', 1361: 'https://jamesclear.com', 1362: 'https://www.plagiarismtoday.com/', 1363: 'https://blog.discordapp.com/', 1364: 'http://www.opsschool.org/', 1365: 'https://engineering.shopify.com/', 1366: 'https://josephwalla.com', 1367: 'http://ben.akrin.com/', 1368: 'http://blog.professorbeekums.com/', 1369: 'https://www.julian.com/', 1370: 'http://observer.com/', 1371: 'http://tylertringas.com/', 1372: 'https://techcrunch.com', 1373: 'https://thecodist.com', 1374: 'https://www.aboveavalon.com', 1375: 'https://www.telegraph.co.uk', 1376: 'https://blog.catchpoint.com', 1377: 'https://www.forbes.com', 1378: 'https://www.mindtheproduct.com', 1379: 'https://blog.ltse.com', 1380: 'http://patrickwoods.com/', 1381: 'https://news.harvard.edu', 1382: 'https://www.inc.com', 1383: 'https://om.co/', 1384: 'https://www.tbray.org/', 1385: 'https://blog.httpwatch.com/', 1386: 'https://getlighthouse.com', 1387: 'https://www.lucidchart.com', 1388: 'http://chadfowler.com/', 1389: 'https://blog.idonethis.com', 1390: 'https://inconshreveable.com/', 1391: 'https://www.figma.com', 1392: 'https://www.w3.org', 1393: 'https://www.chris-granger.com', 1394: 'https://crisp.im', 1395: 'https://nedbatchelder.com', 1396: 'https://developers.google.com', 1397: 'https://skift.com', 1398: 'https://www.catb.org', 1399: 'https://aphyr.com', 1400: 'https://angel.co', 1401: 'https://itsyourturnblog.com', 1402: 'https://fs.blog', 1403: 'https://searchengineland.com', 1404: 'https://matt.might.net', 1405: 'https://stackshare.io', 1406: 'https://tom.preston-werner.com', 1407: 'https://www.virtuouscode.com', 1408: 'https://www.eofire.com', 1409: 'https://lethain.com', 1410: 'https://okdork.com', 1411: 'https://robertheaton.com', 1412: 'https://paulhammant.com', 1413: 'https://backchannel.com', 1414: 'https://time.com', 1415: 'https://ahrefs.com', 1416: 'https://mondaynote.com', 1417: 'https://www.weforum.org', 1418: 'https://cdixon.org', 1419: 'https://smerity.com', 1420: 'https://www.somethingsimilar.com', 1421: 'https://waitbutwhy.com', 1422: 'https://www.joelonsoftware.com', 1423: 'https://www.haneycodes.net', 1424: 'https://www.usatoday.com', 1425: 'https://variety.com', 1426: 'https://www.inverse.com', 1427: 'https://khanlou.com', 1428: 'https://pmarchive.com', 1429: 'https://blogs.dropbox.com', 1430: 'https://twobithistory.org', 1431: 'https://www.jwz.org', 1432: 'https://avichal.com', 1433: 'https://www.bnnbloomberg.ca', 1434: 'https://pasztor.at', 1435: 'https://crew.co', 1436: 'https://www.applift.com', 1437: 'https://thehustle.co', 1438: 'https://buzzsumo.com', 1439: 'https://reactionwheel.net', 1440: 'https://www.ctrl.blog', 1441: 'https://www.rainforestqa.com', 1442: 'https://www.holovaty.com', 1443: 'https://www.economist.com', 1444: 'https://www.speedshop.co', 1445: 'https://www.cockroachlabs.com', 1446: 'https://story.californiasunday.com', 1447: 'https://www.newsweek.com', 1448: 'https://www.instigatorblog.com', 1449: 'https://rauchg.com', 1450: 'https://blog.jaredsinclair.com', 1451: 'https://blog.hootsuite.com', 1452: 'https://dangrover.com', 1453: 'https://initialized.com', 1454: 'https://www.sellbrite.com', 1455: 'https://www.nirandfar.com', 1456: 'https://webaim.org', 1457: 'https://daringfireball.net', 1458: 'https://www.theplayerstribune.com', 1459: 'https://www.jotform.com', 1460: 'https://baremetrics.com', 1461: 'https://blog.asmartbear.com', 1462: 'https://mtlynch.io', 1463: 'https://www.k9ventures.com', 1464: 'https://blog.doordash.com', 1465: 'https://www.aaronsw.com', 1466: 'https://www.flurry.com', 1467: 'https://open.buffer.com', 1468: 'https://www.filfre.net', 1469: 'https://svpg.com', 1470: 'https://pando.com', 1471: 'https://blog.takipi.com', 1472: 'https://www.macobserver.com', 1473: 'https://www.smashingmagazine.com', 1474: 'https://www.agilevc.com', 1475: 'https://www.asahi.com', 1476: 'https://www.gamesradar.com', 1477: 'https://mattturck.com', 1478: 'https://changelog.com', 1479: 'https://signal.org', 1480: 'https://blogs.msdn.microsoft.com', 1481: 'https://www.strategy-business.com', 1482: 'https://www.propublica.org', 1483: 'https://www.gq.com', 1484: 'https://blog.prototypr.io', 1485: 'https://www.theplatform.net', 1486: 'https://scottberkun.com', 1487: 'https://www.shirky.com', 1488: 'https://paulromer.net', 1489: 'https://codewithoutrules.com', 1490: 'https://warpspire.com', 1491: 'https://widgetsandshit.com', 1492: 'https://blog.mergelane.stfi.re', 1493: 'https://engineering.shopify.com', 1494: 'https://www.wbur.org', 1495: 'https://beero.ps', 1496: 'https://exponents.co', 1497: 'https://leanstack.com', 1498: 'https://daniel.haxx.se', 1499: 'https://www.sachinrekhi.com', 1500: 'https://stackstatus.net', 1501: 'https://www.backblaze.com', 1502: 'https://jacobian.org', 1503: 'https://customer.io', 1504: 'https://lwn.net', 1505: 'https://blogs.scientificamerican.com', 1506: 'https://inessential.com', 1507: 'https://www.boredpanda.com', 1508: 'https://www.vanityfair.com', 1509: 'https://dave.cheney.net', 1510: 'https://jvns.ca', 1511: 'https://waxy.org', 1512: 'https://gizmodo.com', 1513: 'https://www.lukew.com', 1514: 'https://david-smith.org', 1515: 'https://alistapart.com', 1516: 'https://www.mattcutts.com', 1517: 'https://wayswework.io', 1518: 'https://thenewstack.io', 1519: 'https://wistia.com', 1520: 'https://blogs.tedneward.com', 1521: 'https://rework.withgoogle.com', 1522: 'https://codingvc.com', 1523: 'https://www.reddit.com', 1524: 'https://grasshopper.com', 1525: 'https://redditblog.com', 1526: 'https://www.osnews.com', 1527: 'https://www.pocketgamer.biz', 1528: 'https://shift.newco.co', 1529: 'https://fundersclub.com', 1530: 'https://inside.com', 1531: 'https://engineeringblog.yelp.com', 1532: 'https://www.csoonline.com', 1533: 'https://adam.herokuapp.com', 1534: 'https://practicoanalytics.com', 1535: 'https://slack.engineering', 1536: 'https://blog.ycombinator.com', 1537: 'https://news.crunchbase.com', 1538: 'https://www.elasticsearch.org', 1539: 'https://blog.codinghorror.com', 1540: 'https://www.hollywoodreporter.com', 1541: 'https://airbnb.design', 1542: 'https://blog.nullspace.io', 1543: 'https://kylerush.net', 1544: 'https://www.groovehq.com', 1545: 'https://stratechery.com', 1546: 'https://hacks.mozilla.org', 1547: 'https://slackhq.com', 1548: 'https://gigaom.com', 1549: 'https://hbswk.hbs.edu', 1550: 'https://qz.com', 1551: 'https://lithub.com', 1552: 'https://tmux.sourceforge.net', 1553: 'https://www.bvp.com', 1554: 'https://ponyfoo.com', 1555: 'https://newrepublic.com', 1556: 'https://continuations.com', 1557: 'https://whoo.ps', 1558: 'https://fortune.com', 1559: 'https://dtrace.org', 1560: 'https://freddestin.com', 1561: 'https://www.brendangregg.com', 1562: 'https://www.thriveglobal.com', 1563: 'https://www.mercatus.org', 1564: 'https://abovethecrowd.com', 1565: 'https://okigiveup.net', 1566: 'https://www.jessyoko.com', 1567: 'https://www.vulture.com', 1568: 'https://zurb.com', 1569: 'https://www.reuters.com', 1570: 'https://www.dailymail.co.uk', 1571: 'https://howmuch.net', 1572: 'https://sumo.com', 1573: 'https://pingdom.com', 1574: 'https://appleinsider.com', 1575: 'https://danshipper.com', 1576: 'https://www.salon.com', 1577: 'https://www.toptal.com', 1578: 'https://blog.discordapp.com', 1579: 'https://david.heinemeierhansson.com', 1580: 'https://blogs.oracle.com', 1581: 'https://www.maxcdn.com', 1582: 'https://mailchimp.com', 1583: 'https://bothsidesofthetable.com', 1584: 'https://evhead.com', 1585: 'https://library.gv.com', 1586: 'https://www.fullcontact.com', 1587: 'https://nvie.com', 1588: 'https://www.livechatinc.com', 1589: 'https://casnocha.com', 1590: 'https://www.politico.com', 1591: 'https://lemire.me', 1592: 'https://lob.com', 1593: 'https://www.collaborativefund.com', 1594: 'https://builttoadapt.io', 1595: 'https://www.susanjfowler.com', 1596: 'https://www.si.com', 1597: 'https://randsinrepose.com', 1598: 'https://calnewport.com', 1599: 'https://www.cnbc.com', 1600: 'https://blog.statuspage.io', 1601: 'https://www.jimcollins.com', 1602: 'https://www.animalz.co', 1603: 'https://www.journalism.org', 1604: 'https://www.artsy.net', 1605: 'https://fi.co', 1606: 'https://9to5mac.com', 1607: 'https://blog.d3in.org', 1608: 'https://www.nerdwallet.com', 1609: 'https://medium.com', 1610: 'https://arxiv.org', 1611: 'https://www.fastcodesign.com', 1612: 'https://allthingsd.com', 1613: 'https://char.gd', 1614: 'https://pointsandfigures.com', 1615: 'https://www.techinsider.io', 1616: 'https://chris.beams.io', 1617: 'https://ardalis.com', 1618: 'https://bitsplitting.org', 1619: 'https://www.jacobinmag.com', 1620: 'https://www.alternet.org', 1621: 'https://anildash.com', 1622: 'https://www.newyorker.com', 1623: 'https://engineering.gusto.com', 1624: 'https://searchenginewatch.com', 1625: 'https://factoryjoe.com', 1626: 'https://overreacted.io', 1627: 'https://nolanlawson.com', 1628: 'https://www.theguardian.com', 1629: 'https://blog.twitch.tv', 1630: 'https://dev.to', 1631: 'https://www.buzzfeed.com', 1632: 'https://www.eugenewei.com', 1633: 'https://journal.stuffwithstuff.com', 1634: 'https://medium.freecodecamp.org', 1635: 'https://blog.algolia.com', 1636: 'https://www.asianefficiency.com', 1637: 'https://blog.skyliner.io', 1638: 'https://storify.com', 1639: 'https://www.bleepingcomputer.com', 1640: 'https://thesocietypages.org', 1641: 'https://www.salesforce.com', 1642: 'https://www.internethistorypodcast.com', 1643: 'https://www.disruptingjapan.com', 1644: 'https://99designs.com', 1645: 'https://blog.docker.com', 1646: 'https://artplusmarketing.com', 1647: 'https://sivers.org', 1648: 'https://paulstamatiou.com', 1649: 'https://blog.ndepend.com', 1650: 'https://www.nngroup.com', 1651: 'https://blogs.nvidia.com', 1652: 'https://www.macrumors.com', 1653: 'https://www.theinformation.com', 1654: 'https://enterprisecraftsmanship.com', 1655: 'https://www.davefarley.net', 1656: 'https://thinkgrowth.org', 1657: 'https://www.geekwire.com', 1658: 'https://www.daemonology.net', 1659: 'https://kinsta.com', 1660: 'https://prog21.dadgum.com', 1661: 'https://where.coraline.codes', 1662: 'https://www.linuxvoice.com', 1663: 'https://lowercasecapital.com', 1664: 'https://blog.travis-ci.com', 1665: 'https://mike-bland.com', 1666: 'https://www.techstars.com', 1667: 'https://www.afr.com', 1668: 'https://25iq.com', 1669: 'https://www.slate.com', 1670: 'https://www.gsb.stanford.edu', 1671: 'https://iansommerville.com', 1672: 'https://www.thedrum.com', 1673: 'https://blog.turbinelabs.io', 1674: 'https://hintjens.com', 1675: 'https://nathanmarz.com', 1676: 'https://hackerlife.co', 1677: 'https://gist.github.com', 1678: 'https://www.raptitude.com', 1679: 'https://blog.cloudflare.com', 1680: 'https://nautil.us', 1681: 'https://triplebyte.com', 1682: 'https://thinkpiece.club', 1683: 'https://www.geckoboard.com', 1684: 'https://www.sitepoint.com', 1685: 'https://betterhumans.coach.me', 1686: 'https://paulbuchheit.blogspot.com', 1687: 'https://www.aaronkharris.com', 1688: 'https://www.dailydot.com', 1689: 'https://www.theawl.com', 1690: 'https://eev.ee', 1691: 'https://www.aerofs.com', 1692: 'https://www.youtube.com', 1693: 'https://mixergy.com', 1694: 'https://andrewchen.co', 1695: 'https://www.ben-evans.com', 1696: 'https://www.macworld.com', 1697: 'https://www.cbinsights.com', 1698: 'https://www.complex.com', 1699: 'https://www.visualcapitalist.com', 1700: 'https://calendar.perfplanet.com', 1701: 'https://www.hodinkee.com', 1702: 'https://www.ebayinc.com', 1703: 'https://boingboing.net', 1704: 'https://guykawasaki.com', 1705: 'https://avc.com', 1706: 'https://jessicaabel.com', 1707: 'https://www.aarp.org', 1708: 'https://tech.gilt.com', 1709: 'https://c2.com', 1710: 'https://lattice.com', 1711: 'https://www.ybrikman.com', 1712: 'https://meyerweb.com', 1713: 'https://developer.olery.com', 1714: 'https://kottke.org', 1715: 'https://deardesignstudent.com', 1716: 'https://blog.frontapp.com', 1717: 'https://blog.gruntwork.io', 1718: 'https://www.ibtimes.co.uk', 1719: 'https://www.marketingsherpa.com', 1720: 'https://m.signalvnoise.com', 1721: 'https://justinkan.com', 1722: 'https://www.pagerduty.com', 1723: 'https://hitenism.com', 1724: 'https://a16z.com', 1725: 'https://blog.coinbase.com', 1726: 'https://uxplanet.org', 1727: 'https://meltingasphalt.com', 1728: 'https://programmers.stackexchange.com', 1729: 'https://www.folklore.org', 1730: 'https://www.farnamstreetblog.com', 1731: 'https://www.themacro.com', 1732: 'https://jasonevanish.com', 1733: 'https://blog.producthunt.com', 1734: 'https://www.prisonpolicy.org', 1735: 'https://simpleprogrammer.com', 1736: 'https://wp.sigmod.org', 1737: 'https://www.johndcook.com', 1738: 'https://blog.disqus.com', 1739: 'https://engineering.riotgames.com', 1740: 'https://www.braintreepayments.com', 1741: 'https://80000hours.org', 1742: 'https://code.likeagirl.io', 1743: 'https://www.apple.com', 1744: 'https://www.analyticsvidhya.com', 1745: 'https://www.dailyfinance.com', 1746: 'https://developer.telerik.com', 1747: 'https://en.wikipedia.org', 1748: 'https://sanctum.geek.nz'}




def graph_embedding_algorithm_result_converter(filepath, num_to_url_dict):
    with open (filepath) as jsonfile:
        result_dict = json.load(jsonfile)
    dict_of_cluster = {}
    for key, value in result_dict.items():
        if value in dict_of_cluster:
            dict_of_cluster[value].append(num_to_url_dict[int(key)])
        else:
            dict_of_cluster[value] = [num_to_url_dict[int(key)]]
    cluster_file = open('./data/graph/graph_community_file.txt', 'w+', encoding='utf-8')
    cluster_file.write(json.dumps(dict_of_cluster) + '\n')
    return dict_of_cluster

def edge_list_file_to_graph(file_path, graph_init):
    edge_list = []
    with open(file_path) as f:
        while True:
            line = f.readline()
            if line:
                edge_list.append(line.strip('\n'))
            else:
                break
    edge_list_no_string = [literal_eval(lst) for lst in edge_list]
    real_edge_list = []
    for lst in edge_list_no_string:
        for lst_of_lst in lst:
            real_edge_list.append((lst_of_lst[0], lst_of_lst[1], lst_of_lst[2]))
    graph_init.add_weighted_edges_from(real_edge_list)



def dfs_get_internal_href_tuple_from_domain(visited_urls, domain, url, max_degree=3):  #for wikipedia
    if url:
        visited_urls.add(url)   #May need to change
        soup=get_page_soup(url)
        soup = soup.find("div", {"id": "bodyContent"})       #only look at body content
        internal_hrefs = get_all_hrefs_from_soup(soup, domain)
        time.sleep(constants.sleep_time)
        result = {(url, internal_href) for internal_href in internal_hrefs}
        if max_degree == 0:
            return result
        else:
            if not internal_hrefs:         #if get no internal_hrefs, return None
                return None
            else:
                for internal_href in internal_hrefs:
                    if internal_href in visited_urls:
                        continue
                    else:
                        visited_urls.add(internal_href)
                        sub_page_result = dfs_get_internal_href_tuple_from_domain(visited_urls, domain, internal_href,
                                                                               max_degree=max_degree - 1)
                        if sub_page_result:
                            result = result.union(sub_page_result)
                        else:
                            pass
                return result
    else:
        return None


#new dfs ##################
def dfs_get_vocab_edge_from_domain(visited_urls, domain, url, current_vocab, max_degree=3):  #for wikipedia
    if url:
        visited_urls.add(url)   #May need to change
        soup=get_page_soup(url)
        soup = soup.find("div", {"id": "bodyContent"})       #only look at body content
        hrefs_voacbs_dict = get_all_hrefs_and_vocab_from_soup(soup, domain)       #{href:vocab}
        if hrefs_voacbs_dict:
            internal_hrefs = hrefs_voacbs_dict.keys()
            time.sleep(constants.sleep_time)
            result = {(current_vocab, hrefs_voacbs_dict[href]) for href in internal_hrefs}          #{(source_vocab, dest_vocab)}
            if max_degree == 0:
                return result
            else:
                if not internal_hrefs:         #if get no internal_hrefs, return None
                    return None
                else:
                    for internal_href in internal_hrefs:
                        if internal_href in visited_urls:
                            continue
                        else:
                            visited_urls.add(internal_href)
                            sub_page_result = dfs_get_vocab_edge_from_domain(visited_urls, domain, internal_href,
                                                                                   hrefs_voacbs_dict[internal_href], max_degree=max_degree - 1)
                            if sub_page_result:
                                result = result.union(sub_page_result)
                            else:
                                pass
                    return result
        else:
            return None
    else:
        return None

def get_wiki_edge_list_from_hrefs_tuples(hrefs_tuples_list):  #input {(source_url, dest_url)}
    wiki_edges_list = [(get_wiki_vocab_from_url(href_tuple[0]), get_wiki_vocab_from_url(href_tuple[1])) for href_tuple in hrefs_tuples_list]
    return set(wiki_edges_list)

def get_wiki_vocab_from_url(url):       #get it from url or extract from soup?
    url_elements = url.split('/')
    if url_elements[-1]:
        vocab = url_elements[-1].replace('_',' ')
        return vocab
    else:
        vocab = url_elements[-2].replace('_', ' ')
        return vocab

# def wiki_api_get_edges(topic):
#     wiki_en_version = wikipediaapi.Wikipedia('en')
#     current_topic_page = wiki_en_version.page(topic)
#     dict_of_pages = current_topic_page.links
#     print(dict_of_pages.keys())
#     print(current_topic_page.categories)
#     return dict_of_pages
#
#     #访问受限
#     #祛除乱码，改成set
#     #改dfs，每次取<a 里面的title =


def get_all_hrefs_and_vocab_from_soup(soup, domain):  #get all internal hrefs and vocab   output = (internal_hrefs_set, vocab_set)

    def get_title_from_a_tag(ele):
        if ele.has_attr('title'):
            single_vocab = ele['title']
            return single_vocab
        else:
            return None
    def get_href(ele):
        if ele.has_attr('href'):
            if ele['href'] not in ["", '/']:

                if '#' in ele['href']:
                    core_link = ele['href'].split('#')[0]
                    if core_link == '':
                        return None
                else:
                    core_link = ele['href']

                if bool(re.match(re.compile('^https?://'), core_link)):
                    if url_fine_grinding(domain) == url_fine_grinding(core_link):
                        return core_link
                    else:
                        return None

                elif bool(re.match(re.compile('^www'), core_link)):
                    if url_fine_grinding('http://' + core_link) == url_fine_grinding(domain):
                        return 'http://' + core_link
                    else:
                        return None

                elif bool(re.match(re.compile('^/[a-zA-Z0-9]'), core_link)):
                    return domain + core_link

                elif bool(re.match(re.compile('^//[a-zA-Z0-9]'), core_link)):
                    possible_full_url = core_link[2:]

                    if bool(re.match(re.compile('^https?://'), possible_full_url)):
                        if url_fine_grinding(possible_full_url) == url_fine_grinding(domain):
                            return possible_full_url
                        else:
                            return None

                    elif bool(re.match(re.compile('^www'), possible_full_url)):
                        if url_fine_grinding('http://' + possible_full_url) == url_fine_grinding(domain):
                            return 'http://' + possible_full_url
                        else:
                            return None

                    else:
                        if url_fine_grinding('http://' + possible_full_url) == url_fine_grinding(domain):
                            return 'http://' + possible_full_url
                        else:
                            return None    # a dangerous assumption
                else:
                    return None
        else:
            return None
    try:
        a_elements = soup.find_all(re.compile('a'))
        hrefs_vocab_dict = {}
        result_hrefs = set()
        result_vocab = set()
        for e in a_elements:
            get_href_result = get_href(e)
            title = get_title_from_a_tag(e)
            if get_href_result and title and not url_contains_unwanted_elements(get_href_result):      #filterred videos
                hrefs_vocab_dict[get_href_result] = title
                result_hrefs.add(get_href_result)
                result_vocab.add(title)
            else:
                pass
        return hrefs_vocab_dict

    except Exception as e:
        print(e)
        logging.exception(e)
        return None

#
if __name__ ==  '__main__':
    print(get_page_soup('https://en.wiktionary.org/wiki/Wiktionary:Requested_entries'))
#
#     fp = './data/graph/updated_edge_list_file.txt'
#     graph_of_url = nx.DiGraph()
#     edge_list_file_to_graph(fp, graph_of_url)
#     num_to_url_dict = graph_to_int_node_edges_file(graph_of_url)
#     dict_cluster = graph_embedding_algorithm_result_converter('graph_of_url.json', num_to_url_dict)
#     source_urls = set()
#     root_source_urls = set()
#     source_urls_file = 'source_sites.tsv'
#     with open(source_urls_file) as f:
#         while True:
#             line = f.readline()
#             if line:
#                 current_url = line.strip('\n') + '/'
#                 root_url = url_fine_grinding(current_url).split('.')[0]  # make sure one domain only appear once
#                 if root_url not in root_source_urls:  # eliminate cases like bbc.com and bbc.co.uk
#                     root_source_urls.add(root_url)  # {bbc, cnn, foxnews, etc}
#                     source_urls.add(current_url)
#             else:
#                 break
#     dict_trimed = {}
#     for key in dict_cluster:
#         dict_trimed[key] = [href for href in dict_cluster[key] if destination_site_is_part_of_source_site(href, source_urls)]