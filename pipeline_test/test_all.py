import kmeans_only
import DFS_integration
import feature_extractor
import logging
import update_monitor

logging.basicConfig(filename='pipeline.log', filemode='w', format='%(asctime)s,%(msecs)d %(name)s %(levelname)s %(message)s',
                    datefmt='%H:%M:%S', level=logging.INFO)
DFS_integration.start_multi_thread_dfs_search()
feature_extractor.multi_thread_test_handle()
kmeans_only.multi_thread_test_handle()
