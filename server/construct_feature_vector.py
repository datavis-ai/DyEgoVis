# coding:utf-8
import pandas as pd
import json
import numpy as np
import pymongo
from entropy import app_entropy
import os.path
import time
import os


# fixme: 为一个egonet序列(dyegonet)构建有一个特征向量(由均值等5个指标拼接而成.)
def construction_egonet_feature_vec(ego_features=None, ego_feature_names=None, time_steps_list=None, time_interval=None):
    """
    ego_features: a object, e.g., {_id:x, ego:x, features:{f1:[x,...], ...,fn:[x,...]}}
    ego_feature_names: ['num_alters', ...], 用于固定均值方差等5个指标值的拼接顺序.按照该列表中的特征顺序拼接,即num_alters的5个指标值+...
    time_steps_list: a time step list, e.g., [x, ..., x]. note that len(time_steps_list)==len(feature_sequence),
               and its indexes correspond to feature_sequence's time steps.
    time_interval: the specified time interval, a list, e.g., ['2000-03', '2001-04']
    :return: [ego_name, feature_vec], e.g, ['mao', [x, x, ...]]
    """
    ego_name = ego_features["ego"]
    ego_features_obj = ego_features["features"]  # {f1:[x, ...], ..., fn:[x, ...]}
    ego_feature_vec_list = []  # [mean, ...]
    for each_feature in ego_feature_names:  # each feature
        feature_sequence = ego_features_obj[each_feature]  # [x, ...]
        # fixme: 某个时间区间
        if time_interval is not None:  # time_interval=[from, to]
            if time_interval[0] != time_interval[1]:  # # fixme:区间 ['2000-03', '2001-04']
                t_from_index = time_steps_list.index(time_interval[0])
                t_to_index = time_steps_list.index(time_interval[1])
                feature_seq_slice = feature_sequence[t_from_index:t_to_index + 1]  # feature_seq_slice=[x, ...,x]
                # fixme: 均值
                seq_mean = np.mean(feature_seq_slice)
                # fixme: 方差
                seq_var = np.var(feature_seq_slice)
                # fixme: 偏度
                pd_s = pd.Series(feature_seq_slice)
                seq_skew = pd_s.skew()
                # fixme: 峰度
                seq_kurt = pd_s.kurt()
                # fixme: 近似熵
                seq_app_entropy = app_entropy(feature_seq_slice)
                # fixme: 将5个指标装到列表中
                ego_feature_vec_list.append(seq_mean)
                ego_feature_vec_list.append(seq_var)
                ego_feature_vec_list.append(seq_skew)
                ego_feature_vec_list.append(seq_kurt)
                ego_feature_vec_list.append(seq_app_entropy)

            else:  # fixme: 某个时间点, e.g.,['2000-03', '2000-03']
                t_index = time_steps_list.index(time_interval[0])
                feature_val = feature_sequence[t_index]
                ego_feature_vec_list.append(feature_val)

        # fixme:整个时间轴
        else:  # the whole time series
            # fixme: 均值
            seq_mean = np.mean(feature_sequence)
            # fixme: 方差
            seq_var = np.var(feature_sequence)
            # fixme: 偏度
            pd_s = pd.Series(feature_sequence)
            seq_skew = pd_s.skew()
            # fixme: 峰度
            seq_kurt = pd_s.kurt()
            # fixme: 近似熵
            seq_app_entropy = app_entropy(feature_sequence)
            # fixme: 将5个指标装到列表中
            ego_feature_vec_list.append(seq_mean)
            ego_feature_vec_list.append(seq_var)
            ego_feature_vec_list.append(seq_skew)
            ego_feature_vec_list.append(seq_kurt)
            ego_feature_vec_list.append(seq_app_entropy)

    return [ego_name, ego_feature_vec_list]


# fixme: 获得符合过滤条件的ego列表
def get_filter_ego_list(db_client, db_name, filter_cond):
    db = db_client[db_name]
    query = {}
    project = {"_id": 0, "ego": 1}
    """
     $gte: >=   
     $lte: <=  
     e.g., {attr1 : {$gte : 100}}
    """
    if db_name.lower() == "enron":
        for each_key in filter_cond:
            if each_key != "total_p_num":
                query[each_key] = {"$gte": filter_cond[each_key][0], "$lte": filter_cond[each_key][1]}
    if db_name.lower() == "tvcg":
        for each_key in filter_cond:
            query[each_key] = {"$gte": filter_cond[each_key][0], "$lte": filter_cond[each_key][1]}
    filter_egos = db["ego_features"].find(query, project)  # [{ego: x}, ...]
    filter_ego_list = []  # 筛选出来的egos, [ego1, ...]
    for ego in filter_egos:
        filter_ego_list.append(ego["ego"])
    return filter_ego_list

# fixme: 根据过滤条件过滤egos.
def filter_egos(db_client, db_name, filter_cond, all_egos_feature=None):
    """
    :param db_client:
    :param db_name: enron or tvcg
    :param filter_cond: e.g., {"avg_density": 0.5, "avg_tie": 0.4, ...}
    :param all_egos_feature: 符合条件的ego-feature对, {ego: [x, ...], ...}
    :return: {ego: [x, ...], ...}
    """
    db = db_client[db_name]
    query = {}
    project = {"_id": 0, "ego": 1}
    """
     $gte: >=   
     $lte: <=  
     e.g., {attr1 : {$gte : 100}}
    """
    if db_name.lower() == "enron":
        for each_key in filter_cond:
            if each_key != "total_p_num":
                query[each_key] = {"$gte": filter_cond[each_key][0], "$lte": filter_cond[each_key][1]}
    if db_name.lower() == "tvcg":
        for each_key in filter_cond:
            query[each_key] = {"$gte": filter_cond[each_key][0], "$lte": filter_cond[each_key][1]}
    filter_egos = db["ego_features"].find(query, project)  # [{ego: x}, ...]
    filter_ego_list = []  # 筛选出来的egos, [ego1, ...]
    for ego in filter_egos:
        filter_ego_list.append(ego["ego"])
    filter_egos_feature = {}
    for ego in all_egos_feature:  # {ego: [x, ...], ...}
        if ego in filter_ego_list:
            filter_egos_feature[ego] = all_egos_feature[ego]
    return filter_egos_feature, filter_ego_list


# fixme:用于响应前端发送过来的请求,动态地支持时间片. 该函数的作用: 算出选定时间片内的dynegonet的每个特征的均值,方差,峰度,偏度,近似熵这5个统计指标,然后构成一个5*5=25个元素的向量,并用于降维.
def construction_egonet_feature_vec_for_dynet(db_client=None, db_name=None, time_interval=None, path_data=None, filter_cond=None, is_filter=False):
    """
    :param db_client: e.g., pymongo.MongoClient("mongodb://localhost:27017/")
    :param db_name: the name of the specified database.
    :param time_interval: None indicates the entire sequence; ['2000-01', '2001-10'] indicates from 2000-01 to 2001-10.
    :param path_data: e.g., "data/enron_email_undirected_graph"
    :param filter_cond: 过滤条件, e.g., {"avg_density": 0.5, "avg_tie": 0.4, ...}
    :return: {ego1:[x, ...], ego2:[x, ...], ...}, i.e., a feature vector object
       t1    t2    t3    t4    t5
       ego1 ego1  ego1  ego1  ego1
    f1  x    x     x     x     x =>  均值 方差 峰度 偏度 近似熵  }=> [均值 方差 峰度 偏度 近似熵...均值 方差 峰度 偏度 近似熵] 25个值
    f2  x    x     x     x     x =>  均值 方差 峰度 偏度 近似熵
    ...
    f6  x    x     x     x     x =>  均值 方差 峰度 偏度 近似熵
    """
    # is_exist_time_s = time.time()
    if time_interval is None:  # 整个时间区间
        path_file = path_data + "/ego_vec_none.json"
    else:  # 选择了某个时间区间
        path_file = path_data + "/ego_vec_" + str(time_interval[0]) + "_" + str(time_interval[1]) + ".json"
    f_is_exist = os.path.exists(path_file)
    if f_is_exist:  # if the file exists, load data from the file.
        with open(path_file, 'r') as load_f:
            load_obj = json.load(load_f)  # {"mao": [x, ...], ...}
            print("load ego_vec_xxx from the local file")
            # todo: 将过滤操作添加在这里. 从所有egos中过滤出符合条件的egos.
            # if is_filter:
            #     load_obj, filter_ego_list = filter_egos(db_client=db_client, db_name=db_name, filter_cond=filter_cond, all_egos_feature=load_obj)
            #     return load_obj, filter_ego_list
            # else:
            return load_obj  # {'mao': [x, x, ...], ...}
    else:
        print("online generate data")
        s_time = time.time()
        db = db_client[db_name]
        ego_feature_names_r = db["ego_feature_names"].find_one()  # {__id: x, features_list: [x, ...]}
        ego_feature_names = ego_feature_names_r["features_list"]  # fixme: [f1_name, f2_name, ...]
        if time_interval is not None:
            timeline_r = db["timeline"].find_one()
            time_steps_list = timeline_r["time_steps"]  # ['2000-01', '2000-02', ...]
            f_ego_vec = path_data + "/ego_vec_" + str(time_interval[0]) + "_" + str(time_interval[1]) + ".json"
        else:
            time_steps_list = None
            f_ego_vec = path_data + "/ego_vec_none.json"
        # fixme: 一个dynnet的6种特征序列已经提前算好并存放在数据库中了.
        # todo: 可以在这里添加过滤条件直接让数据库执行过滤操作, 但是生成的文件将作废.
        all_ego_features = db["ego_features"].find()
        # fixme: 如果没有对应的文件则生成并存放在本地文件中.文件命名规则如: ego_vec_2001-03_2002-01.json
        f_json = open(f_ego_vec, "w")
        json_obj = {}  # {"ego1": [f1的均值,f1的方差, f1的峰度,f1偏度,f1的近似熵, f2...]}
        print("construct ego_vec object....")
        # todo: 可以在这里添加过滤条件, 这样就能加速特征构建过程, 但是生成的文件将作废.
        for ego_features in all_ego_features:  # ego_features: {_id:x, ego:x, features:{f1:[x,...], ...,fn:[x,...]}}
            ego_vec = construction_egonet_feature_vec(ego_features=ego_features, ego_feature_names=ego_feature_names, time_steps_list=time_steps_list, time_interval=time_interval)
            json_obj[ego_vec[0]] = ego_vec[1]
        print("writing ego_vec_xxx.json file.....")
        json.dump(json_obj, f_json)
        f_json.close()
        e_time = time.time()
        print("run time:")
        print(e_time - s_time)
        # todo: 将过滤操作添加在这里. 从所有egos中过滤出符合条件的egos.
        # if is_filter:
        #     json_obj, filter_ego_list = filter_egos(db_client=db_client, db_name=db_name, filter_cond=filter_cond, all_egos_feature=json_obj)
        #     return json_obj, filter_ego_list
        # else:
        return json_obj

# # 使用公式计算均值方差偏度峰度
# def calc(data):
#     n = len(data)  # 10000个数
#     niu = 0.0  # niu表示平均值,即期望.
#     niu2 = 0.0  # niu2表示平方的平均值
#     niu3 = 0.0  # niu3表示三次方的平均值
#     for a in data:
#         niu += a
#         niu2 += a**2
#         niu3 += a**3
#     niu /= n
#     niu2 /= n
#     niu3 /= n
#     sigma = math.sqrt(niu2 - niu*niu)
#     return [niu, sigma, niu3]
#
#
# def calc_stat(data):
#     [niu, sigma, niu3] = calc(data)
#     n = len(data)
#     niu4 = 0.0  # niu4计算峰度计算公式的分子
#     for a in data:
#         a -= niu
#         niu4 += a ** 4
#     niu4 /= n
#
#     skew = (niu3 - 3 * niu * sigma ** 2 - niu ** 3) / (sigma ** 3)  # 偏度计算公式
#     kurt = niu4 / (sigma ** 4)  # 峰度计算公式:下方为方差的平方即为标准差的四次方
#     return [niu, sigma, skew, kurt]


if __name__ == "__main__":
    import pymongo
    # db_client = pymongo.MongoClient("mongodb://localhost:27017/")
    # db = db_client["enron"]
    # all_ego_features = db["ego_features"].find()
    # print(list(all_ego_features))

    """
    import time
    data = list(np.random.randn(10000))  # 满足高斯分布的10000个数
    # data2 = list(2 * np.random.randn(10000))  # 将满足好高斯分布的10000个数乘以两倍,方差变成四倍
    start = time.time()
    [niu, sigma, skew, kurt] = calc_stat(data)
    end = time.time()
    print("time_1:")
    print(end - start)
    print(niu, sigma, skew, kurt)

    start_1 = time.time()
    # fixme: 均值
    seq_mean = np.mean(data)
    # print("seq_mean")
    # print(seq_mean)
    # fixme: 方差
    seq_var = np.var(data)
    # fixme: 偏度
    pd_s = pd.Series(data)
    seq_skew = pd_s.skew()
    # fixme: 峰度
    seq_kurt = pd_s.kurt()
    end_1 = time.time()

    print("time_2:")
    print(end_1 - start_1)
    print(seq_mean, seq_var, seq_skew, seq_kurt)
    """
    # query = {}
    # db_name = "enron"
    # if db_name.lower() == "enron":
    #     for each_key in filter_cond:
    #         if each_key != "total_p_num":
    #             query[each_key] = {"$gte": filter_cond[each_key]}
    # if db_name.lower() == "tvcg":
    #     for each_key in filter_cond:
    #         query[each_key] = {"$gte": filter_cond[each_key]}
    # print(query)
    db_client = pymongo.MongoClient("mongodb://localhost:27017/")
    db_name = "enron"
    filter_cond = {"avg_tie": 0.3, "avg_density": 0.2, "avg_alterE_num": 12.2, "avg_alter_alters": 2.1, "avg_alter2_num": 6.1, "avg_alter_num": 5.1, "total_p_num": 24}
    all_egos_feature = load_obj = json.load(open("data/enron/ego_vec_none.json", "r"))
    r = filter_egos(db_client=db_client, db_name=db_name, filter_cond=filter_cond, all_egos_feature=all_egos_feature)
    print(r)
    """
    ['louise.kitchen', 'john.lavorato']
    """
