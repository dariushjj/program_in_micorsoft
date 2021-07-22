import logging
import utils
import re
import copy
import constants
import json
from dateparser.search import search_dates
import datetime


class PageInfoExtractor(object):
    def __init__(self, url, vocab):
        self.title = None
        self.url = url
        soup = utils.get_page_soup(url)
        self.soup = soup
        self.vocab = vocab

    def dfs_get_all_ele_and_content(self):
        def dfs_search(ele_list, content_set, root_soup):
            if str(type(root_soup)) == '<class \'bs4.element.Tag\'>':
                ele_list.append(root_soup)
                if utils.is_english_paragraph(root_soup.text, self.vocab):
                    content_set.add(root_soup.text)
                if len(list(root_soup.children)) == 0:
                    return
                else:
                    for child in root_soup.children:
                        dfs_search(ele_list, content_set, child)
            else:
                pass

        ele_list = []
        content_set = set()
        root_soup = self.soup.find('html')
        dfs_search(ele_list, content_set, root_soup)
        return ele_list, content_set

    def get_all_text_region(self):
        try:
            soup = self.soup
            [s.extract() for s in soup(['script', 'span'])]
            contents = dict()
            for ele in soup.findAll(re.compile('')):
                if ele.text in contents:
                    pass
                else:
                    if utils.is_english_paragraph(ele.text, self.vocab):
                        contents.update({ele.text: len(ele.text.split())})
                    else:
                        pass
            return contents
        except Exception as e:
            logging.exception(e)
            print(e)
            return None

    def get_article_text_regions(self):
        try:
            soup = self.soup
            [s.extract() for s in soup(['script', 'span'])]
            props = ['name', 'class', 'id']
            contents = dict()
            for prop in props:
                for ele in soup.findAll(re.compile('section|div'), {prop: re.compile('content|body|text|article')}):
                    if ele.text in contents:
                        pass
                    else:
                        if utils.is_english_paragraph(ele.text, self.vocab):
                            contents.update({ele.text: len(ele.text.split())})
                        else:
                            pass
            return contents
        except Exception as e:
            logging.exception(e)
            print(e)
            return None


# granted inputs are article pages
class ArticlePageInfoExractor(PageInfoExtractor):
    def __init__(self, url, vocab):
        super.__init__(url, vocab)

    def article_body_extractor(self):
        try:
            soup = self.soup
            [s.extract() for s in soup(['script', 'span'])]
            props = ['name', 'class', 'id']
            contents = []
            for prop in props:
                contents += soup.findAll(re.compile('section|div'), {prop: re.compile('content|body|text|article')})

            target_idx = 0
            max_text_len = 0
            for idx, text_region in enumerate(contents):
                cur_text_len = len(text_region.text.split())
                if cur_text_len > max_text_len:
                    target_idx = idx
                    max_text_len = cur_text_len
            return contents[target_idx].text
        except Exception as e:
            logging.exception(e)
            return None

            # def article_title_extractor(self):

    #     try:
    #         soup = self.soup
    #         tags = ['h'+str(i+1) for i in range(5)]
    #         for idx, tag in enumerate(tags):
    #             title_candidates = soup.findAll(tag)
    #             if len(title_candidates) == 1:
    #                 return title_candidates[0].text
    #     except Exception as e:
    #         logging.exception(e)
    #     return

    def article_img_extractor(self):
        try:
            soup = self.soup
            imgs = [ele['src'] for ele in soup.findAll('img')]
        except Exception as e:
            logging.exception(e)
        return imgs

    def article_video_extractor(self):
        try:
            soup = self.soup
            videos = [ele['src'] for ele in soup.findAll('video')]
        except Exception as e:
            logging.exception(e)
        return videos

    #########3


def article_title_extractor(url):
    title = ''
    title_list = []
    try:
        soup = utils.get_page_soup(url)
        if soup is None:
            raise NameError

        [s.extract() for s in soup(re.compile('div|section'), {"class": re.compile('bar|nav|banner|related|more')})]
        [s.extract() for s in soup('aside')]

        title_list.append(soup.find_all('h1',
                                        class_=re.compile('(article|entry|post|content|main|page).*?(title|header)',
                                                          re.IGNORECASE)))
        title_list.append(soup.find_all('h1', class_=re.compile('headline', re.I)))
        title_list.append(soup.find_all('h1', itemprop=re.compile('headline|name', re.IGNORECASE)))
        title_list.append(soup.find_all('span', itemprop=re.compile('headline', re.IGNORECASE)))
        title_list.append(soup.find_all(re.compile('h[2-4]'),
                                        class_=re.compile('(article|entry|post|content).*?(title|header)')))
        title_div = soup.find_all(re.compile('div|header|article|section|main', re.IGNORECASE),
                                  class_=re.compile(
                                      "(?!(site|nav).)*(entry|heading|title|content|headline|post|article)",
                                      re.IGNORECASE))
        if title_div:
            flag = False
            for tag in title_div:
                if tag.find_all('h1'):
                    if not re.match('(.\'.blog)|(org)', tag.find_all('h1')[0].get_text(), re.I):
                        if len((tag.find_all('h1')[0].get_text()).split()) > 3:
                            title_list.append(tag.find_all('h1'))
                            flag = True
                            break

            if flag is False:
                for tag in title_div:
                    if tag.find_all(re.compile('h[2-4]')):
                        if not re.match('(.\'.blog)|(site)', tag.find_all(re.compile('h[2-4]'))[0].get_text(),
                                        re.I):
                            if len((tag.find_all(re.compile('h[2-4]'))[0].get_text()).split()) > 3:
                                title_list.append(tag.find_all(re.compile('h[2-4]')))
                                break

        backup_titles = soup.find_all(re.compile('h[1-2]'))
        for backup_title in backup_titles:
            if len((backup_title.get_text()).split()) > 2:
                t = []
                t.append(backup_title)
                title_list.append(t)

        for name in title_list:
            if name:
                title = name[0].get_text()
                break

        # constants.redis_server.hset(name=url + '_info', key='title', value=title.__str__())
        # print(url)
        # print(title)
        return title

    except Exception as e:
        print(e.with_traceback())


def article_timestamp_extractor(url, soup):
    if soup is None:
        raise NameError

    timestamp = None
    while 1:
        # by ld_json
        ld_json = soup.find('script', type='application/ld+json')
        if ld_json is not None:
            ld_json = json.loads(ld_json.get_text())
            if 'datePublished' in ld_json.keys():
                timestamp = ld_json['datePublished']
                break
        [s.extract() for s in soup(['script', 'meta', 'footer'])]
        # by time tag
        time_eles = soup.find_all("time")
        if time_eles:
            # print('time')
            timestamp = time_eles[0].get_text()
            break
        # by meta tag
        props = ['itemprop', 'name', 'property']
        for prop in props:
            time_eles = soup.find_all('meta', {prop: re.compile("(?<!(up))date|published", re.I)})
            if time_eles:
                timestamp = time_eles[0].get('content')
                break
        if timestamp is not None:
            break
        # by url
        pattern = re.compile(r'(20[0-1][0-9]([-_/]?)[0-9]{1,2}(?:\2[0-9]{1,2})?)')
        if pattern.search(url):
            timestamp = pattern.search(url).group()
            break
        # by property
        time_eles = soup.find_all(
            class_=re.compile("(?<!(up))date((?!(outer)).)*$|timestamp|(post-(on|time)$)|publish", re.I))
        if time_eles:
            if search_dates(time_eles[0].get_text()):
                timestamp = time_eles[0].get_text()
                break
        # by dateparser
        time_keyword = re.compile(
            r'\d{2,4}[\s,-]\d{2,4}[\s,-]\d{2,4}$|Jan|Feb|Mar|April|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec|month|day|year',
            re.I)
        time_eles = soup.find_all(lambda tag: tag.string is not None and len(tag.string.split()) < 10 and len(
            tag.string.split()) > 2 and time_keyword.search(tag.string))
        if time_eles:
            for ele in time_eles:
                timestamp = search_dates(ele.get_text())
                if timestamp:
                    timestamp = timestamp[0][1].strftime("%Y-%m-%d %H:%M:%S")
                    break
            if timestamp:
                break
        break
    if timestamp is not None:
        timestamp = search_dates(timestamp)[0][1].strftime("%Y-%m-%d %H:%M:%S")
    else:
        timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    # print(self.url)
    # print(timestamp)
    return timestamp

# if __name__ == '__main__':
#     url = 'https://retropie.org.uk/2019/07/composite-out-broken-on-retropie-4-5/'
#     article_title_extractor(url)
# url = 'https://www.decibelinsight.com/blog'
# domain = utils.get_base_site_url(url)
# soup = utils.get_page_soup(url)
# vocab = utils.build_english_vocab()
# extr = PageInfoExtractor(url, vocab)
# text_region = extr.get_all_text_region()
# print(text_region)
