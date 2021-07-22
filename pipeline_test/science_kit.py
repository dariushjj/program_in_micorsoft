from scipy import stats
import queue
import numpy as np
import sys
import functools

def float_range(x, lower, upper):
    if x >= lower and x < upper:
        return True
    else:
        return False

def data_to_bucket_map(data, bucket_boundaries):
    for i in range(len(bucket_boundaries)-2, -1, -1):
        if float_range(data, bucket_boundaries[i], bucket_boundaries[i+1]):
            return i

def bucket_data(raw_data, std_num = 3):               
    is_normal = False
    if len(raw_data) > 7:
        alpha = 1e-2    
        _, p = stats.normaltest(list(raw_data))
        if p > alpha: 
            is_normal = True
            
    std = np.std(raw_data)
    mean = np.mean(raw_data)
    bucketized_data = []
    if is_normal:        
        bucket_boundaries = list(filter(lambda x: x > 0, [mean + i* std for i in range(-std_num, std_num + 1)]))
        bucket_boundaries.insert(0, 0)
        bucket_boundaries.append(sys.maxsize)
        for ele in raw_data:
            for i in range(len(bucket_boundaries)-2, -1, -1):
                if float_range(ele, bucket_boundaries[i], bucket_boundaries[i+1]):
                    bucketized_data.append(i)
        return bucketized_data, bucket_boundaries
    else:
        step = std/2
        bucket_boundaries = list(filter(lambda x: x > 0, [mean + i* step for i in range(-std_num*2, std_num*2 + 1)]))
        bucket_boundaries.insert(0, 0)
        bucket_boundaries.append(sys.maxsize)
        for ele in raw_data:
            for i in range(len(bucket_boundaries)-2, -1, -1):
                if float_range(ele, bucket_boundaries[i], bucket_boundaries[i+1]):
                    bucketized_data.append(i+1)
        return bucketized_data, bucket_boundaries


def fetch_extreme_ele(input_list, fetch_ratio, high=True):       
    if input_list:
        buf = []
        buf.append(input_list[0])
        buf_len = int(len(input_list) * fetch_ratio )
        if high:            
            for ele in input_list:
                if len(buf) <= buf_len:
                    buf.append(ele)
                else:
                    min_value = min(buf)
                    if ele > min_value:          
                        buf.append(ele)                                          
                        buf.remove(min_value)
                        min_value = min(buf)                                 
        else:
            for ele in input_list:
                if len(buf) <= buf_len:
                    buf.append(ele)
                else:
                    max_value = max(buf)
                    if ele < max_value:          
                        buf.append(ele)                                          
                        buf.remove(max_value)
                        max_value = max(buf) 
        return buf
    else:
        return


def mean(input_list):
    if input_list:
        return sum(input_list)/len(input_list)
    else:
        return None

def l2_distance(x,y):
    return np.sqrt(sum([(float(xi) - float(yi))**2 for xi,yi in zip(x,y)]))

