from bs4 import BeautifulSoup
import requests
import re
import certifi
import logging
import random


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

def get_fresh_page_soup(url, timeout=3):
    try:
        cafile = certifi.where()
        headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/75.0.3770.100 Safari/537.36', 'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3', 'Accept-Language': 'en-US,en;q=0.9,zh-CN;q=0.8,zh;q=0.7,zh-TW;q=0.6'}
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
    try:
        proxy = requests.get(
            'http://list.didsoft.com/get?email=likailunzj@126.com&pass=36xsqw&pid=http1000&https=yes&showcountry=no')
        proxy.encoding = 'utf-8'
        soup = BeautifulSoup(proxy.text, 'html.parser')
        proxies = soup.text.split('\n')
        cafile = certifi.where()
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/75.0.3770.100 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3',
            'Accept-Language': 'en-US,en;q=0.9,zh-CN;q=0.8,zh;q=0.7,zh-TW;q=0.6'}
        proxy = random.choice(proxies)
        proxies = {'https':'https://' + proxy}
        html = requests.get(url, verify=cafile, headers=headers, proxies=proxies, timeout=3)
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

def list_of_article_url_filter(soup):
    soup.find_all(['article', 'div'], class_=re.compile('post'))
    return

if __name__ == '__main__':
    list_of_article = ['https://venturehacks.com/',
            #            'https://stratechery.com/',
            #            'https://geshan.com.np/',
            #            'https://thehftguy.com/',
            # 'https://summation.net/',
            # 'https://joel.is/',
            # 'https://avc.com/',
            # 'https://hunterwalk.com/',
            # 'https://www.eugenewei.com/',
            # 'https://blog.stephenwolfram.com/'
                       ]
    list_of_view=[
        'http://www.betaboston.com',
                  'https://www.star-telegram.com/',
                  'http://engineering.linkedin.com',
                  'http://www.foodtechconnect.com',
                  'http://www.takram.com',
                  'http://blog.linkedin.com',
                  'http://fivethirtyeight.com',
    ]
    article_list_item_pattern = re.compile('post|entry')

    length_of_posts = []
    list_of_all_siblings=[]
for list_name in list_of_article:
    soup = get_fresh_page_soup(list_name)
    print(soup)
    items = soup.find_all(['article', 'div'], class_=article_list_item_pattern)
    minimum_items = []
    article_list_item = 0
    for item in items:
        # if get_max_consecutive_siblings_count(item, 'p') > 4:
        #     article_list_item += 1
        # print(get_max_consecutive_siblings_count(item, 'p'))
        if not len(item.find_all(['article', 'div'], class_=article_list_item_pattern)):
            minimum_items.append(item)
    list_of_each_sibling = []
    for item in minimum_items:
        list_of_each_sibling.append(get_max_consecutive_siblings_count(item, 'p'))
    list_of_all_siblings.append(list_of_each_sibling)
    length_of_posts.append(len(minimum_items))
print('max_consecutive_siblings_count:', list_of_all_siblings)
print('sum: ', length_of_posts)


