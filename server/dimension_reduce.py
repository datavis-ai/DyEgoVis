# coding:utf-8
# from sklearn.datasets import load_digits
from sklearn.manifold import MDS, TSNE
from scipy.spatial.distance import canberra
from sklearn.metrics import pairwise_distances
import time
from sklearn.decomposition import PCA, IncrementalPCA
from sklearn import preprocessing
import numpy as np
import os
import json

# classical MDS
def cmdscale(D, m=2):
    """
    Classical multidimensional scaling (MDS)

    Parameters
    ----------
    D : (n, n) array
        Symmetric distance matrix.
    m: desired dimension
    Returns
    -------
    Y : (n, p) array
        Configuration matrix. Each column represents a dimension. Only the
        p dimensions corresponding to positive eigenvalues of B are returned.
        Note that each dimension is only determined up to an overall sign,
        corresponding to a reflection.

    evals : (n,) array
        Eigenvalues of B. 降序排列的特征值列表.

    """
    # Number of points
    n = len(D)

    # Centering matrix
    H = np.eye(n) - np.ones((n, n)) / n

    # YY^T
    B = -H.dot(D ** 2).dot(H) / 2

    # Diagonalize
    evals, evecs = np.linalg.eigh(B)  # 求解: 特征值 + 特征向量
    # Sort by eigenvalue in descending order
    idx = np.argsort(evals)[::-1]  # 从小到大排列并取出索引.
    evals = evals[idx]  # 特征值降序排列
    evecs = evecs[:, idx]  # 特征向量按照特征值一一对应重排.
    # Compute the coordinates using positive-eigenvalued components only
    # 注意: 即使使用了欧式距离矩阵, 算出的特征值仍然有负的.
    w, = np.where(evals > 0)  # 返回正的特征值对应的索引.
    L = np.diag(np.sqrt(evals[w]))  # 特征值构成的对角矩阵
    V = evecs[:, w]
    Y = V.dot(L)
    cord_2d_cmds = []  # [[x, y], ..]
    for each_one in Y:
        cord_2d_cmds.append(list(each_one[:m]))

    return cord_2d_cmds


# fixme: 使用canberra距离作为距离矩阵.
def canberra_dissimilarity(data_list):
    """
    :param data_list: [[x, x, ...], [x, x, ...], ....], shape=(n_samples, dims)
    :return: distance_list = [[x, x, x, ...], [x, x, x, ...], ...], shape=(n_samples, n_samples)
    """
    distance_list = []
    for each_row in data_list:
        temp_list = []
        for each_col in data_list:
            r = canberra(u=each_row, v=each_col)
            temp_list.append(r)
        distance_list.append(temp_list)
    return distance_list


# fixme: 使用MDS降维.
def dimension_reduce_MDS(db_client=None, db_name=None, ego_vec_obj=None, dissimilarity="canberra", max_iter=350, method_rd="PCA", normalization="min-max", time_interval=None, path_data=None):
    """
    db_client: mongodb
    db_name: database name
    dissimilarity: e.g., "canberra", "euclidean", "cosine"...
    ego_vec_obj: {ego1: [x, x, ...], ego2: [x, x, ...], ...}, 每个向量由每个指定特征(6个指定特征)的[均值,方差,偏度,峰度,近似熵]5个指标拼接而成.
    :return: all_points_list, a list, e.g., [{ego: 'mao', point: [x, y], egoattrs: {attr1: x, attr2: x, ...}}, ...]
    """
    s_time = time.time()
    # path_file = ""
    if time_interval:
        path_file = path_data + "/egoPoints_" + time_interval[0] + "_" + time_interval[1] + "_" + method_rd + ".json"
    else:
        path_file = path_data + "/egoPoints_none_" + method_rd + ".json"
    f_is_exist = os.path.exists(path_file)
    if f_is_exist:  # if the file exists, load data from the file.
        with open(path_file, 'r') as load_f:
            ego_points_obj = json.load(load_f)  # {"mao": [x, ...], ...}
            print("load egoPoints_xxx.json from the local file")
            return ego_points_obj  # {'mao': [x, x, ...], ...}
    ego_vec_list = []  # [[], ...]
    ego_name_list = []  # [x, x, x, ...]
    collection_name = "ego_features"
    db = db_client[db_name]
    db_collction = db[collection_name]
    for each_ego in ego_vec_obj:
        ego_name_list.append(each_ego)
        ego_vec_list.append(ego_vec_obj[each_ego])  # ego_vec_list=[[], [], ...]
    print(normalization.lower() + " normalization ......")
    ##################### Normalization ############################
    if normalization.lower() == "min-max":
        # fixme: min-max Normalization
        min_max_scaler = preprocessing.MinMaxScaler()
        ego_vec_list = min_max_scaler.fit_transform(ego_vec_list)  # min-max normalization
    if normalization.lower() == "z-score":
        standar_scaler = preprocessing.StandardScaler()
        ego_vec_list = standar_scaler.fit_transform(ego_vec_list)
    ####################### End Normalization ##########################
    no_need_ft = {"_id": 0, "ego": 0, "features": 0, "avg_density": 0, "avg_alterE_num": 0, "avg_alter2_num": 0, "avg_alter_alters": 0}
    if db_name.lower() == "tvcg":
        no_need_ft["r_interests"] = 0
        no_need_ft["p_num_year"] = 0
        no_need_ft["org"] = 0
    all_points_list = []
    if method_rd == "PCA":
        print("Using PCA...")
        pca = PCA(n_components=2)
        points_list = pca.fit_transform(ego_vec_list)
        # all_points_list = []
        index_point = -1
        for each_point in points_list:
            index_point += 1
            temp_obj = {}
            ego_name = ego_name_list[index_point]
            temp_obj["ego"] = ego_name
            temp_obj["point"] = list(each_point)
            # temp_obj["fvec"] = list(ego_vec_list[index_point])
            ego_doc = db_collction.find_one({"ego": ego_name}, no_need_ft)
            temp_obj["egoattrs"] = ego_doc
            all_points_list.append(temp_obj)  # [{ego: 'mao', point: [x, y], egoattrs: {attr1: x, attr2: x, ...}}, ...]
        e_time = time.time()
        print("dimension reduce time:")
        print(e_time - s_time)
        # return all_points_list

    if method_rd == "MDS":
        print("Using MDS...")
        if dissimilarity == "euclidean":
            embedding = MDS(n_components=2, max_iter=max_iter, n_init=1)
            points_list = embedding.fit_transform(ego_vec_list)
        else:
            embedding = MDS(n_components=2, max_iter=max_iter, n_init=1, dissimilarity="precomputed")
            # canberra_dist_list = canberra_dissimilarity(data_list=ego_vec_list)
            canberra_dist_list = pairwise_distances(X=ego_vec_list, metric=dissimilarity)
            points_list = embedding.fit_transform(canberra_dist_list)

        # all_points_list = []
        index_point = -1
        for each_point in points_list:
            index_point += 1
            temp_obj = {}
            ego_name = ego_name_list[index_point]
            temp_obj["ego"] = ego_name
            temp_obj["point"] = list(each_point)
            # temp_obj["fvec"] = list(ego_vec_list[index_point])
            ego_doc = db_collction.find_one({"ego": ego_name}, no_need_ft)
            temp_obj["egoattrs"] = ego_doc
            all_points_list.append(temp_obj)  # [{ego: 'mao', point: [x, y], egoattrs: {attr1: x, attr2: x, ...}}, ...]
        e_time = time.time()
        print("dimension reduce time:")
        print(e_time - s_time)
        # return all_points_list

    if method_rd == "t-SNE":
        print("Using t-SNE...")
        if dissimilarity == "euclidean":
            points_list = TSNE(n_components=2).fit_transform(ego_vec_list)
        else:
            canberra_dist_list = pairwise_distances(X=ego_vec_list, metric=dissimilarity)
            points_list = TSNE(n_components=2, metric="precomputed").fit_transform(canberra_dist_list)

        # all_points_list = []
        index_point = -1
        for each_point in points_list:
            index_point += 1
            temp_obj = {}
            ego_name = ego_name_list[index_point]
            temp_obj["ego"] = ego_name
            temp_obj["point"] = list(map(float, each_point))  # fixme: 原来的np.float32无法序列化, 强制转换成float型.
            # temp_obj["fvec"] = list(ego_vec_list[index_point])
            ego_doc = db_collction.find_one({"ego": ego_name}, no_need_ft)
            temp_obj["egoattrs"] = ego_doc
            all_points_list.append(temp_obj)  # [{ego: 'mao', point: [x, y], egoattrs: {attr1: x, attr2: x, ...}}, ...]
        e_time = time.time()
        print("dimension reduce time:")
        print(e_time - s_time)
        # return all_points_list
    if method_rd == "CMDS":
        print("Using CMDS...")
        D = pairwise_distances(X=ego_vec_list, metric=dissimilarity)
        points_list = cmdscale(D=D, m=2)
        # all_points_list = []
        index_point = -1
        for each_point in points_list:
            index_point += 1
            temp_obj = {}
            ego_name = ego_name_list[index_point]
            temp_obj["ego"] = ego_name
            temp_obj["point"] = list(map(float, each_point))  # fixme: 原来的np.float32无法序列化, 强制转换成float型.
            # temp_obj["fvec"] = list(ego_vec_list[index_point])
            ego_doc = db_collction.find_one({"ego": ego_name}, no_need_ft)
            temp_obj["egoattrs"] = ego_doc
            all_points_list.append(temp_obj)  # [{ego: 'mao', point: [x, y], egoattrs: {attr1: x, attr2: x, ...}}, ...]
        e_time = time.time()
        print("dimension reduce time:")
        print(e_time - s_time)
    f_json = open(path_file, "w")
    json.dump(all_points_list, f_json)
    f_json.close()
    return all_points_list


# fixme:为每个时间步绘制MDS图.
def MDS_all_time_step(db_client=None, db_name=None, nodes_time_step=None, method_rd="MDS", dissimilarity="canberra", max_iter=300, path_data=None, normalization="min-max"):
    """
    :param db_client: 数据库
    :param db_name: 数据库名称
    :param nodes_time_step: {2000-02: [ego1, ego2, ego3, ...], ...}
    path_data: data/enron
    :return: timestep_mds_obj = {2000-03: [{ego:x, point:[x,x], egoattrs:{x:xx, ...}}, ...]}
    """
    s_time = time.time()
    path_file = path_data + "/all_timesteps_" + normalization.lower() + "_" + method_rd + "_" + dissimilarity + ".json"
    no_need_ft = {"_id": 0, "ego": 0, "features": 0, "avg_density": 0, "avg_alterE_num": 0, "avg_alter2_num": 0, "avg_alter_alters": 0}
    if db_name.lower() == "tvcg":
        no_need_ft["r_interests"] = 0
        no_need_ft["p_num_year"] = 0
        no_need_ft["org"] = 0
    f_is_exist = os.path.exists(path_file)
    if f_is_exist:  # if the file exists, load data from the file.
        with open(path_file, 'r') as load_f:
            timestep_mds_obj = json.load(load_f)  # {"mao": [x, ...], ...}
            print("load all_timesteps_xxx.json from the local file")
            return timestep_mds_obj  # {'mao': [x, x, ...], ...}
    else:
        db = db_client[db_name]
        timeline = db["timeline"].find_one()
        all_ego_features = {}  # {ego: [], ...}
        for each_doc in db["ego_features"].find():
            ego = each_doc["ego"]
            features = each_doc["features"]
            all_ego_features[ego] = features
        """
        all_ego_features: {ego1: {f1: [x,x,x...], f2: [x,x,x,...], ...}, ...}
        """
        time_steps_list = timeline["time_steps"]  # ['2000-01', '2000-02', ...]

        ego_feature_names = db["ego_feature_names"].find_one()
        feature_name_list = ego_feature_names["features_list"]  # [f1, f2, f3, ...]
        timestep_mds_obj = {}
        index_time = -1
        for time_step in time_steps_list:  # fixme: 为每个时间步生成空间布局.
            index_time += 1
            ego_name_list = nodes_time_step[time_step]  # [ego0, ego1, ego2, ...]
            ego_vec_list = []  # fixme: [[f1,f2,...f6], ...], egonet snapshot embedding matrix.
            for ego in ego_name_list:  # all nodes at current time step.
                feature_obj = all_ego_features[ego]  # {f1: [x,x,x,...], f2: [x,x,x,...], ...}
                ego_fvect_list = []  # fixme: ego-network snapshot embedding, [f1,f2,..., f6], 以后可以在这里加上节点属性.
                for each_feature in feature_name_list:
                    ego_fvect_list.append(feature_obj[each_feature][index_time])
                ego_vec_list.append(ego_fvect_list)
            # todo: 在这里加上归一化处理,因为涉及到计算向量间的距离.
            ##################### Normalization ############################
            if normalization.lower() == "min-max":
                # fixme: min-max Normalization
                min_max_scaler = preprocessing.MinMaxScaler()
                ego_vec_list = min_max_scaler.fit_transform(ego_vec_list)  # min-max normalization
            if normalization.lower() == "z-score":
                standar_scaler = preprocessing.StandardScaler()
                ego_vec_list = standar_scaler.fit_transform(ego_vec_list)
            ####################### End Normalization ##########################
            if method_rd.lower() == "mds":
                if dissimilarity == "euclidean":
                    embedding = MDS(n_components=2, max_iter=max_iter, n_init=1)
                    points_list = embedding.fit_transform(ego_vec_list)
                else:
                    embedding = MDS(n_components=2, max_iter=max_iter, n_init=1, dissimilarity="precomputed")
                    # canberra_dist_list = canberra_dissimilarity(data_list=ego_vec_list)
                    canberra_dist_list = pairwise_distances(X=ego_vec_list, metric=dissimilarity)
                    points_list = embedding.fit_transform(canberra_dist_list)

                all_points_list = []  # [{ego: x, point: [x,x], fvec: [x,x,x,...], egoattrs: {name: x, position:x, ...}}, ...]
                index_point = -1
                for each_point in points_list:
                    index_point += 1
                    temp_obj = {}
                    ego_name = ego_name_list[index_point]
                    temp_obj["ego"] = ego_name
                    temp_obj["point"] = list(each_point)
                    # temp_obj["fvec"] = list(ego_vec_list[index_point])
                    ego_doc = db["ego_features"].find_one({"ego": ego_name}, no_need_ft)
                    temp_obj["egoattrs"] = ego_doc
                    all_points_list.append(temp_obj)  # [{ego: 'mao', point: [x, y], egoattrs: {attr1: x, attr2: x, ...}}, ...]
                timestep_mds_obj[time_step] = all_points_list
            if method_rd.lower() == "pca":
                print("Using PCA...")
                pca = PCA(n_components=2)
                points_list = pca.fit_transform(ego_vec_list)
                all_points_list = []  # [{ego: x, point: [x,x], fvec: [x,x,x,...], egoattrs: {name: x, position:x, ...}}, ...]
                index_point = -1
                for each_point in points_list:
                    index_point += 1
                    temp_obj = {}
                    ego_name = ego_name_list[index_point]
                    temp_obj["ego"] = ego_name
                    temp_obj["point"] = list(each_point)
                    # temp_obj["fvec"] = list(ego_vec_list[index_point])
                    ego_doc = db["ego_features"].find_one({"ego": ego_name}, no_need_ft)
                    temp_obj["egoattrs"] = ego_doc
                    all_points_list.append(
                        temp_obj)  # [{ego: 'mao', point: [x, y], egoattrs: {attr1: x, attr2: x, ...}}, ...]
                timestep_mds_obj[time_step] = all_points_list
            if method_rd.lower() == "t-sne":
                print("Using t-SNE...")
                if dissimilarity == "euclidean":
                    points_list = TSNE(n_components=2).fit_transform(ego_vec_list)
                else:
                    canberra_dist_list = pairwise_distances(X=ego_vec_list, metric=dissimilarity)
                    points_list = TSNE(n_components=2, metric="precomputed").fit_transform(canberra_dist_list)

                all_points_list = []  # [{ego: x, point: [x,x], fvec: [x,x,x,...], egoattrs: {name: x, position:x, ...}}, ...]
                index_point = -1
                for each_point in points_list:
                    index_point += 1
                    temp_obj = {}
                    ego_name = ego_name_list[index_point]
                    temp_obj["ego"] = ego_name
                    temp_obj["point"] = list(map(float, each_point))  # fixme: 原来的np.float32无法序列化, 强制转换成float型.
                    # temp_obj["fvec"] = list(ego_vec_list[index_point])
                    ego_doc = db["ego_features"].find_one({"ego": ego_name}, no_need_ft)
                    temp_obj["egoattrs"] = ego_doc
                    all_points_list.append(
                        temp_obj)  # [{ego: 'mao', point: [x, y], egoattrs: {attr1: x, attr2: x, ...}}, ...]
                timestep_mds_obj[time_step] = all_points_list

        f_json = open(path_file, "w")
        json.dump(timestep_mds_obj, f_json)
        f_json.close()
        e_time = time.time()
        print("time of generating " + path_file + ":")
        print(e_time - s_time)
        return timestep_mds_obj


# fixme: 时间片内的概览图.
def MDS_timeslice(db_client=None, db_name=None, time_interval=None, path_data=None, normalization="min-max", method_rd="MDS", dissimilarity="canberra", max_iter=300, filter_ego_list=None):
    """
    :param db_client: mongodb client
    :param db_name: selected database
    :param time_interval: e.g., [2000-09, 20001-01]
    :param path_data: e.g., data/enron
    :param normalization: min-max, z-score, none.
    :param filter_ego_list: [ego1, ego2, ...], 按照当前过滤条件筛选出来的egos.
    :return: filter_obj, e.g., {2000-03: [{ego:x, point:[x,x], egoattrs:{x:xx, ...}}, ...]}
    """
    db = db_client[db_name]
    timeline_r = db["timeline"].find_one()
    time_steps_list = timeline_r["time_steps"]  # ['2000-01', '2000-02', ...]
    no_need_ft = {"_id": 0, "ego": 0, "features": 0, "avg_density": 0, "avg_alterE_num": 0, "avg_alter2_num": 0, "avg_alter_alters": 0}
    if db_name.lower() == "tvcg":
        no_need_ft["r_interests"] = 0
        no_need_ft["p_num_year"] = 0
        no_need_ft["org"] = 0
    if time_interval == None:  # 整个时间轴
        t_from_index = 0
        t_to_index = len(time_steps_list) - 1
    else:  # 一个时间片
        t_from_index = time_steps_list.index(time_interval[0])
        t_to_index = time_steps_list.index(time_interval[1])
    # path_file = path_data + "/timeSlice_" + normalization.lower() + ".json"
    path_file = path_data + "/all_timesteps_" + normalization.lower() + "_" + method_rd + "_" + dissimilarity + ".json"
    # if time_interval == None:
    #     path_file = path_data + "/all_timesteps_" + normalization.lower() + "_" + method_rd + "_" + dissimilarity + ".json"
    # else:
    #     path_file = path_data + "/timeslice_" + normalization.lower() + "_" + method_rd + "_" + dissimilarity + "_" + str(time_interval[0]) + "_" + str(time_interval[1]) + ".json"
    f_is_exist = os.path.exists(path_file)
    if f_is_exist:  # if the file exists, load data from the file.
        with open(path_file, 'r') as load_f:
            timestep_mds_obj = json.load(load_f)  # {2000-03: [{ego: x, point: [x, y], fvec: [x, ...], egoattrs: {}, ...}, ...]}
            filter_obj = {}
            for date in time_steps_list[t_from_index:t_to_index + 1]:
                temp_ego_list = []
                for each_ego in timestep_mds_obj[date]:  # [{ego: x, ...}, ...]
                    if each_ego["ego"] in filter_ego_list:
                        temp_ego_list.append(each_ego)
                filter_obj[date] = temp_ego_list
            return filter_obj  # {'mao': [x, x, ...], ...}
    else:
        print("No the file " + path_file)
        print("Generating this file......")
        #################
        db_collction = db["dynamic_graph"]  # 对应的表, {2000: [{source: x, target: x, frequency: x}, ...], ...}
        all_items = db_collction.find()  # 取出集合"dynamic_graph"中所有的文档(格式: [{time_step: x, edges: [{}, ...]}, ...])
        dynamic_graph_obj = {}  # {"2000-01": [{source: x, target: x, frequency: x}, ...], ...}
        for each_doc in all_items:  # each_doc={_id:x, time_step:x, edges:[{source:x, target:x, frequency:x}, ...]}
            edges = each_doc["edges"]
            time_step = each_doc["time_step"]
            dynamic_graph_obj[time_step] = edges  # dynamic_graph_obj = {'2000-03': [{source:x, target:x, value:x}, ...], ...}
        nodes_time_step = {}  # {2000-01: [ego1, ego2, ...]}
        step_index = -1
        for each_step in time_steps_list:  # 按照时间顺序创建动态图
            step_index += 1
            edges = dynamic_graph_obj[each_step]  # [{source:x, target:x, frequency:x}, ...]
            links_list = []  # [(id1, id2, 10), ...]
            nodes_set = set()
            for each_link in edges:
                # print(each_link)
                source = each_link["source"]
                target = each_link["target"]
                weight_ = each_link["frequency"]
                nodes_set.add(source)
                nodes_set.add(target)
                links_list.append((source, target, int(weight_)))
            nodes_time_step[each_step] = list(nodes_set)
        #################
        all_ego_features = {}  # {ego: [], ...}
        for each_doc in db["ego_features"].find():
            ego = each_doc["ego"]
            features = each_doc["features"]
            all_ego_features[ego] = features
        """
        all_ego_features: {ego1: {f1: [x,x,x...], f2: [x,x,x,...], ...}, ...}
        """
        ego_feature_names = db["ego_feature_names"].find_one()
        feature_name_list = ego_feature_names["features_list"]  # [f1, f2, f3, ...]
        timestep_mds_obj = {}
        index_time = -1
        for time_step in time_steps_list:  # fixme: 为每个时间步生成空间布局.
            index_time += 1
            ego_name_list = nodes_time_step[time_step]  # [ego0, ego1, ego2, ...]
            ego_vec_list = []  # fixme: [[f1,f2,...f6], ...], egonet snapshot embedding matrix.
            for ego in ego_name_list:  # all nodes at current time step.
                feature_obj = all_ego_features[ego]  # {f1: [x,x,x,...], f2: [x,x,x,...], ...}
                ego_fvect_list = []  # fixme: ego-network snapshot embedding, [f1,f2,..., f6], 以后可以在这里加上节点属性.
                for each_feature in feature_name_list:
                    ego_fvect_list.append(feature_obj[each_feature][index_time])
                ego_vec_list.append(ego_fvect_list)
            # todo: 在这里加上归一化处理,因为涉及到计算向量间的距离.
            ##################### Normalization ############################
            if normalization.lower() == "min-max":
                # fixme: min-max Normalization
                min_max_scaler = preprocessing.MinMaxScaler()
                ego_vec_list = min_max_scaler.fit_transform(ego_vec_list)  # min-max normalization
            if normalization.lower() == "z-score":
                standar_scaler = preprocessing.StandardScaler()
                ego_vec_list = standar_scaler.fit_transform(ego_vec_list)
            ####################### End Normalization ##########################
            if method_rd.lower() == "mds":
                if dissimilarity == "euclidean":
                    embedding = MDS(n_components=2, max_iter=max_iter, n_init=1)
                    points_list = embedding.fit_transform(ego_vec_list)
                else:
                    embedding = MDS(n_components=2, max_iter=max_iter, n_init=1, dissimilarity="precomputed")
                    # canberra_dist_list = canberra_dissimilarity(data_list=ego_vec_list)
                    canberra_dist_list = pairwise_distances(X=ego_vec_list, metric=dissimilarity)
                    points_list = embedding.fit_transform(canberra_dist_list)

                all_points_list = []  # [{ego: x, point: [x,x], fvec: [x,x,x,...], egoattrs: {name: x, position:x, ...}}, ...]
                index_point = -1
                for each_point in points_list:
                    index_point += 1
                    temp_obj = {}
                    ego_name = ego_name_list[index_point]
                    temp_obj["ego"] = ego_name
                    temp_obj["point"] = list(each_point)
                    # temp_obj["fvec"] = list(ego_vec_list[index_point])
                    ego_doc = db["ego_features"].find_one({"ego": ego_name}, no_need_ft)
                    temp_obj["egoattrs"] = ego_doc
                    all_points_list.append(temp_obj)  # [{ego: 'mao', point: [x, y], egoattrs: {attr1: x, attr2: x, ...}}, ...]
                timestep_mds_obj[time_step] = all_points_list
            if method_rd.lower() == "pca":
                print("Using PCA...")
                pca = PCA(n_components=2)
                points_list = pca.fit_transform(ego_vec_list)
                all_points_list = []  # [{ego: x, point: [x,x], fvec: [x,x,x,...], egoattrs: {name: x, position:x, ...}}, ...]
                index_point = -1
                for each_point in points_list:
                    index_point += 1
                    temp_obj = {}
                    ego_name = ego_name_list[index_point]
                    temp_obj["ego"] = ego_name
                    temp_obj["point"] = list(each_point)
                    # temp_obj["fvec"] = list(ego_vec_list[index_point])
                    ego_doc = db["ego_features"].find_one({"ego": ego_name}, no_need_ft)
                    temp_obj["egoattrs"] = ego_doc
                    all_points_list.append(
                        temp_obj)  # [{ego: 'mao', point: [x, y], egoattrs: {attr1: x, attr2: x, ...}}, ...]
                timestep_mds_obj[time_step] = all_points_list
            if method_rd.lower() == "t-sne":
                print("Using t-SNE...")
                if dissimilarity == "euclidean":
                    points_list = TSNE(n_components=2).fit_transform(ego_vec_list)
                else:
                    canberra_dist_list = pairwise_distances(X=ego_vec_list, metric=dissimilarity)
                    points_list = TSNE(n_components=2, metric="precomputed").fit_transform(canberra_dist_list)

                all_points_list = []  # [{ego: x, point: [x,x], fvec: [x,x,x,...], egoattrs: {name: x, position:x, ...}}, ...]
                index_point = -1
                for each_point in points_list:
                    index_point += 1
                    temp_obj = {}
                    ego_name = ego_name_list[index_point]
                    temp_obj["ego"] = ego_name
                    temp_obj["point"] = list(map(float, each_point))  # fixme: 原来的np.float32无法序列化, 强制转换成float型.
                    # temp_obj["fvec"] = list(ego_vec_list[index_point])
                    ego_doc = db["ego_features"].find_one({"ego": ego_name}, no_need_ft)
                    temp_obj["egoattrs"] = ego_doc
                    all_points_list.append(temp_obj)  # [{ego: 'mao', point: [x, y], egoattrs: {attr1: x, attr2: x, ...}}, ...]
                timestep_mds_obj[time_step] = all_points_list
        f_json = open(path_file, "w")
        # print("timestep_mds_obj len")
        # print(len(timestep_mds_obj))
        json.dump(timestep_mds_obj, f_json)
        f_json.close()
        filter_obj = {}
        for date in time_steps_list[t_from_index:t_to_index + 1]:
            temp_ego_list = []
            for each_ego in timestep_mds_obj[date]:  # [{ego: x, ...}, ...]
                if each_ego["ego"] in filter_ego_list:
                    temp_ego_list.append(each_ego)
            filter_obj[date] = temp_ego_list
        return filter_obj  # {'1990': [x, x, ...], ...}


if __name__ == "__main__":
    # with open("data/enron/ego_vec_none.json", 'r') as f_json:
    #     ego_vec_obj = json.load(f_json)
    #     # ego_vec_obj = {"a": [1, 2, 3, 4], "b": [22, 4, 20, 5], "c": [21, 3, 26, 12], "d": [11, 23, 45, 61]}
    #     dimensmutationion_reduce_MDS(ego_vec_obj=ego_vec_obj)
    # data_list = [[1, 0, 1], [0, 1, 0]]
    # r = canberra_dissimilarity(data_list)
    # print(r)
    import pymongo
    db_client = pymongo.MongoClient("mongodb://localhost:27017/")
    # nodes_time_step = {"1990": ["mao", "cher"], "1991": ["yun", "jingjing"]}
    # all_ego_features = {"mao": {"a": [10, 11], "b": [12, 13]},
    #                     "cher": {"a": [100, 111], "b": [112, 113]},
    #                     "yun": {"a": [210, 211], "b": [212, 213]},
    #                     "jingjing": {"a": [310, 311], "b": [312, 313]},
    #                     }
    # MDS_all_time_step(db_client=db_client, db_name="enron", nodes_time_step=nodes_time_step)
    # a = [11, 22, 33, 44, 55]
    # print(a[1:3 + 1])
    # db_name = "enron"
    # time_interval = ["2000-03", "2000-05"]
    # path_data = "data/" + db_name
    # r = MDS_timeslice(db_client=db_client, db_name=db_name, time_interval=time_interval, path_data=path_data)
    # print(r)
    # path_file = "data/enron/timeslice_min-max_MDS_canberra_2000-09_2001-09.json"
    # path_file = "data/enron/timeslice_min-max_t-SNE_canberra_2000-09_2001-09.json"
    # path_file = "data/enron/timeslice_z-score_PCA_canberra_2000-09_2001-09.json"
    path_file = "data/enron/timeslice_z-score_PCA_canberra_2000-10_2001-08.json"
    with open(path_file, 'r') as load_f:
        timestep_mds_obj = json.load(load_f)
        print(len(timestep_mds_obj))