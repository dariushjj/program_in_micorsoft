import certifi
# import redis
import requests
from bs4 import BeautifulSoup
from hdfs import InsecureClient
from rediscluster import StrictRedisCluster

source_site_upper_bound = 724
source_site_lower_bound = 714
partition_index = 1
partition_size = 3

headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/75.0.3770.100 Safari/537.36', 'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3', 'Accept-Language': 'en-US,en;q=0.9,zh-CN;q=0.8,zh;q=0.7,zh-TW;q=0.6'} 
headers1 = {'User-Agent': 'Mozilla/4.0 (compatible; MSIE 7.0; Windows NT 6.1; WOW64; Trident/5.0; SLCC2; .NET CLR 2.0.50727; .NET CLR 3.5.30729; .NET CLR 3.0.30729; Media Center PC 6.0; InfoPath.3; .NET4.0C; .NET4.0E; SE 2.X MetaSr 1.0)'}
cafile = certifi.where()
proxy = requests.get('http://list.didsoft.com/get?email=likailunzj@126.com&pass=36xsqw&pid=http1000&https=yes&showcountry=no')
proxy.encoding = 'utf-8'
soup = BeautifulSoup(proxy.text, 'html.parser')
proxies = soup.text.split('\n')
# redis_server = redis.Redis(host='localhost', port=6379, db=0)
sleep_time = 3
HDFS_client = InsecureClient("http://172.31.43.44:9870")

dfs_file_dir = '/user/ubuntu/dfs_data/'
feature_file_dir = '/user/ubuntu/features/'
kmeans_result_dir = "/user/ubuntu/kmeans_result/"
list_of_view_file_dir = '/user/ubuntu/kmeans_result/list_of_view/'
article_page_dir = '/user/ubuntu/kmeans_result/article_page/'

startup_nodes = [{"host": "localhost", "port": "6379"}]
redis_server = StrictRedisCluster(startup_nodes=startup_nodes, decode_responses=True)
max_kept_recent_update_gain = 5000
min_valid_update_num = 5
dfs_degree = 2
