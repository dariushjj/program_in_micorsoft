import os
import re
import utils
import constants
import logging
import concurrent.futures
import json
import info_extractor
import datetime
import logging
# logging.basicConfig(level=logging.INFO)

# use redis to store last time get_all_href result in a set,
# to store unsuccessful ping in blacklist(zset with score), and to store value of updated gain.
class Monitor(object):
	def __init__(self, url, vocab):
		self.vocab = vocab
		self.url = url
		self.title = None
		self.jsonlist = []

	def run(self):
		logging.info('monitoring '+self.url)
		r = constants.redis_server
		url = self.url
		soup = utils.get_fresh_page_soup(url)
		domain = utils.get_base_site_url(url)
		# new_all_hrefs = utils.get_all_hrefs_from_soup(soup, domain)
		new_all_hrefs_ele_dict = utils.get_all_href_ele_from_soup(soup, domain)  # bofei updated 7.19
		new_all_hrefs = set(new_all_hrefs_ele_dict.keys())
		try:
			origin_urls = set(r.lrange("origin_urls_of_" + url, 0, -1))
			updated_urls = set(r.lrange("updated_urls_of_" + url, 0, -1))
		except Exception as e:
			logging.exception(e)
			return

		if origin_urls:
			try:
				if len(new_all_hrefs) > 0.7 * len(origin_urls) and len(new_all_hrefs) > constants.min_valid_update_num:
					logging.info("Valid Update")
					updated_hrefs = list((new_all_hrefs - origin_urls)-updated_urls)
					# print(updated_hrefs)#this is a test,empty list
					if updated_hrefs:
						for updated_href in updated_hrefs:
							if new_all_hrefs_ele_dict[updated_href].find_parent(['h1', 'h2', 'h3', 'h4', 'h5', 'h6']) or new_all_hrefs_ele_dict[updated_href].find_all(['h1', 'h2', 'h3', 'h4', 'h5', 'h6']):
								title = new_all_hrefs_ele_dict[updated_href].text
							else:
								title = info_extractor.article_title_extractor(updated_href)

							if utils.is_english_paragraph(title, self.vocab):
								passagetime = info_extractor.article_timestamp_extractor(self.url, soup)
								urljson = json.dumps({'title': title, 'timestamp': passagetime, 'url': updated_href, 'gettime':datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")})
								self.jsonlist.append(urljson)
							else:
								continue
						r.lpush("updated_urls_of_" + url, *updated_hrefs)
						r.lpush("updated_hrefs_details_" + url, *self.jsonlist)

					while r.llen("updated_urls_of_" + url) > constants.max_kept_recent_update_gain:
						r.rpop("updated_urls_of_" + url)
				# there ought to be a blacklist, however it doesn't work well
				else:
					if len(new_all_hrefs) == 0:
						r.zincrby("blacklist", url, 5)
					else:
						r.zincrby("blacklist", url, 1)
			except Exception as e:
				logging.exception(e)
				return

		else:  # if doesnt have hrefs last time
			if len(new_all_hrefs) > constants.min_valid_update_num:
				try:
					new_all_hrefs_list = list(new_all_hrefs)
					# for new_href in new_all_hrefs_list:
					# 	self.title = info_extractor.article_title_extractor(new_href)
					# 	if self.title:
					# 		r.set("updated_hrefs_title"+url,self.title)
					r.lpush("origin_urls_of_" + url, *new_all_hrefs_list)
				except Exception as e:
					logging.exception(e)
					return
			# same problem happens again
			else:
				try:
					if len(new_all_hrefs) == 0:
						r.zincrby("blacklist", url, 5)
					else:
						r.zincrby("blacklist", url, 1)
				except Exception as e:
					logging.exception(e)
					return

		# print(r.keys())#this is a test to get redis keys
		print(r.lrange('updated_hrefs_details_'+url,0,-1))#this is a test to get titles
		print(r.lrange('updated_urls_of_'+url,0,-1))#this is a test to get last_all_herfs_urls

	def flushlist(self):
		r = constants.redis_server
		r.flushall()
		print(r.keys('*'))#this is a test

	def get_url(self):
		return self.url


def multi_thread_test(threads=os.cpu_count()+1):
	monitor_list = []
	vocab = utils.build_english_vocab()
	file_name_list = constants.HDFS_client.list(constants.list_of_view_file_dir)
	for filename in file_name_list:
		with constants.HDFS_client.read(constants.kmeans_result_dir + filename, encoding="utf-8") as reader:
			list_of_view_urls = json.load(reader)
			for list_of_view_url in list_of_view_urls:
				monitor_list.append(Monitor(list_of_view_url, vocab))

	with concurrent.futures.ThreadPoolExecutor(max_workers=threads) as executor:
		future_dict = {}
		for monitor in monitor_list:
			future_dict.update({executor.submit(monitor.run()): monitor})

		for future in future_dict.keys():
			finished_monitor = future_dict[future]
			try:
				_ = future.result()
			except Exception as e:
				logging.info(e)
				logging.info('monitor error on '+finished_monitor.get_url())


if __name__ == '__main__':
	# source_sites = set()
	# source_sites_file = './data/unique_source_sites.csv'
	# with open(source_sites_file) as f:
	# 	while True:
	# 		line = f.readline()
	# 		if line:
	# 			source_sites.add(line.strip('\n') + '/')
	# 		else:
	# 			break
	# source_sites_list = list(source_sites)
	# while True:
	# 	for site in source_sites_list:
	# 		monitor = Monitor(site,domain)
	# 		monitor.run()
	# monitor = Monitor('https://www.theverge.com/')

	# for i in range(10000):
	# 	monitor.run()

	# vocab = utils.build_english_vocab()
	# file_name_list = constants.HDFS_client.list(constants.list_of_view_file_dir)
	# for file_name in file_name_list:
	# 	with constants.HDFS_client.read(constants.kmeans_result_dir + file_name, encoding="utf-8") as reader:
	# 		list_of_views = json.load(reader)
	# 		for list_of_view in list_of_views:
	# 			monitor = Monitor(list_of_view, vocab)
	# 			monitor.run()

	# monitor = Monitor('https://www.theverge.com/',vocab)
	# monitor.flushlist()

	for index in range(1000):
		multi_thread_test()
