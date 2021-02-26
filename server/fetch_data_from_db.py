# coding:utf-8
import pymongo
import re
import numpy as np

# fixme: 获得字段的所有的值
def fetch_all_val(db_client=None, db_name=None, field=None):
    db = db_client[db_name]
    db_collction = db["ego_features"]
    temp_obj = {}
    temp_obj[field] = 1
    temp_obj["_id"] = 0  # _id是默认显示的, 想要不显示, 则设置为0
    r = db_collction.find({}, temp_obj)
    field_val_list = set()  # [x, x, x, ...]
    for each_one in r:
        field_val = each_one[field]
        str_list = str(field_val).strip().split(";")
        for each_one in str_list:
            field_val_list.add(each_one)
    return list(field_val_list)


# fixme: 根据输入的关键词,查询出对应的ego节点.
def query_match_nodes(db_client=None, db_name=None, field=None, query_item=None):
    """
    :param db_name: 数据库名称
    :param field: 前端选中的字段条件
    :param query_item: 前端输入的查询词
    :return: e.g., [{ego: x, name: x, position: x}, ...]
    """
    db = db_client[db_name]
    db_collction = db["ego_features"]
    temp_obj = {}
    temp_obj["_id"] = 0
    temp_obj["features"] = 0
    if db_name.lower() == "tvcg":
        temp_obj["p_num_year"] = 0
    query_condition = {}
    # fixme: 支持模糊查询,e.g., query_item="smith"
    query_condition[field] = re.compile(query_item)  # 查询包含query_item的节点.
    query_r = db_collction.find(query_condition, temp_obj)
    return list(query_r)


# fixme: 获得egoId对应的egonet的信息.
def get_dyegonet_detail(db_client=None, db_name=None, egoId=None):
    db = db_client[db_name]
    db_collction = db["ego_features"]
    result = db_collction.find({"ego": egoId}, {"_id": 0, "avg_alter_num": 0, "avg_density": 0, "avg_tie": 0, "avg_alterE_num": 0, "avg_alter2_num": 0, "avg_alter_alters": 0})
    db_collction = db["ego_feature_names"]
    features_list = db_collction.find({}, {"_id": 0})
    infoObj = {}
    infoObj["info"] = list(result)[0]
    adpt_features_list = ["num_alters", "num_edges_alters", "density", "avg_tie", "num_2_alters", "avg_alters_alters"]
    # infoObj["ftList"] = list(features_list)[0]["features_list"]
    infoObj["ftList"] = adpt_features_list
    return infoObj


# fixme: 获得node_id的信息.
def get_node_info(dyegonet=None, db_client=None, db_name=None, ego_id=None, node_id=None, tslice=None):
    """
    :param dyegonet:
    :param db_client:
    :param db_name:
    :param ego_id: 当前egonet的ego的id.
    :param node_id: 点击的节点的id
    :param tslice: 选中的时间区间, e.g., [4, 8]
    :return: rest = {tsliceW: {0: 12, 1: 0, 2: 1, ...}, lifespan: [min_t, max_t], occurfreq: 10, nattr: {name: x, position: x}}
    """
    db = db_client[db_name]
    db_collction = db["ego_features"]
    result = db_collction.find({"ego": node_id}, {"_id": 0, "ego": 0, "features": 0, "avg_alter_num": 0, "avg_density": 0, "avg_tie": 0, "avg_alterE_num": 0, "avg_alter2_num": 0, "avg_alter_alters": 0})
    attr_obj = dyegonet.get_edge_data(u=ego_id, v=node_id)  # {'weight': {0: 100, 1: 100}, 't': [[0, 1]]}
    min_t = attr_obj["t"][0][0]  # [[0, 1], [3, 5], ..., [7, 9]]
    max_t = attr_obj["t"][-1][1]  # [[0, 1], [3, 5], ..., [7, 9]]
    w_obj = attr_obj['weight']  # {0: 100, 1: 100}
    weight_obj = {}
    for idx in range(tslice[0], tslice[1] + 1):
        if idx in w_obj:
            weight_obj[str(idx)] = w_obj[idx]
        else:
            weight_obj[str(idx)] = 0
    node_attr = list(result)[0]  # {node: x, }
    rest = {}
    rest["tsliceW"] = weight_obj  # {0: 1, 1: 100, ...} 时间区间内的边权重对象
    rest["lifespan"] = [min_t, max_t]  # [3, 6], 在整个时间轴上的寿命
    rest["occurfreq"] = len(w_obj)  # 在整个时间轴上的出现次数.
    rest["nattr"] = node_attr  # 节点属性对象.
    return rest


# fixme: 获得堆叠图的数据
def get_stacked_graph_data(db_client=None, db_name=None, time_interval=None, ego_list=None, feature=None):
    """
    :param db_client:
    :param db_name: enron / tvcg
    :param time_interval: e.g., ["2000-03", "2000-09"]
    :param ego_list: [ego1, ego2, ...]
    :param feature: the selected feature in the frontend
    :return: {"dataList": dataList, "columns": columns}
    """
    db = db_client[db_name]
    db_collction = db["ego_features"]
    timeline_r = db["timeline"].find_one()
    time_steps_list = timeline_r["time_steps"]  # ["2000-03", ..., "2002-02"]
    columns = ["date"]
    t_from_index = 0
    t_to_index = len(time_steps_list) - 1
    if time_interval is not None:  # time_interval=[from, to]
        if time_interval[0] != time_interval[1]:  # # fixme:区间 ['2000-03', '2001-04']
            t_from_index = time_steps_list.index(time_interval[0])
            t_to_index = time_steps_list.index(time_interval[1])
    feature_slices_list = []  # [[], ...]
    for each_ego in ego_list:
        columns.append(each_ego)
        result = db_collction.find({"ego": each_ego},  {"_id": 0, "ego": 0, "avg_alter_num": 0, "avg_density": 0, "avg_tie": 0, "avg_alterE_num": 0, "avg_alter2_num": 0, "avg_alter_alters": 0})
        if feature == "p_num_year":
            feature_seq = list(result)[0][feature]
        else:
            feature_seq = list(result)[0]["features"][feature]  # {feature: {}}
        feature_slice = feature_seq[t_from_index:t_to_index + 1]
        feature_slices_list.append(feature_slice)
    # print("feature_slices_list")
    # print(feature_slices_list)
    feature_slices_list = np.array(feature_slices_list)
    feature_slices_list = feature_slices_list.transpose()
    dataList = []
    time_steps_slice = time_steps_list[t_from_index:t_to_index + 1]  # [2000-02, 2000-03, 2000-04]
    for row, ft_slice in enumerate(feature_slices_list):
        date = time_steps_slice[row]
        tempObj = {}
        tempObj["date"] = date
        for col, ft in enumerate(ft_slice):
            ego = ego_list[col]
            tempObj[ego] = float(ft)
        dataList.append(tempObj)
    # print("dataList")
    # print(dataList)
    # print("columns")
    # print(columns)
    stacked_graph_obj = {"dataList": dataList, "columns": columns}
    return stacked_graph_obj


if __name__ == "__main__":
    db_client = pymongo.MongoClient("mongodb://localhost:27017/")
    # db_name = "enron"
    # egoId = "fletcher.sturm"
    # r = get_dyegonet_detail(db_client=db_client, db_name=db_name, egoId=egoId)
    # print(r)
    '''
    [{'total_p_num': 1, 
    'ego': '2128276236', 
    'features': {f1: [x,x,x,...], f2: [], ...}, // 原始特征而非统计特征. 
    'name': 'Ping Guo', 
    'p_num_year': [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0], 
    'r_interests': 'Parallel coordinates;Data visualization', 
    'org': 'IEEE'}]

    '''
    # db_name = "enron"
    # time_interval = ["2000-03", "2000-05"]
    # ego_list = ["fletcher.sturm", "brad.mckay"]
    # feature = "avg_tie"
    # r = get_stacked_graph_data(db_client=db_client, db_name=db_name, time_interval=time_interval, ego_list=ego_list, feature=feature)
    # print(r)
    # time_steps_list = ["1990", "1991", "1992", "1993", "1994"]
    # time_interval = ["1990", "1992"]
    # t_from_index = 0
    # t_to_index = 0
    # if time_interval is not None:  # time_interval=[from, to]
    #     if time_interval[0] != time_interval[1]:  # # fixme:区间 ['2000-03', '2001-04']
    #         t_from_index = time_steps_list.index(time_interval[0])
    #         t_to_index = time_steps_list.index(time_interval[1])
    # time_steps_slice = time_steps_list[t_from_index:t_to_index + 1]
    # print("time_steps_slice")
    # print(time_steps_slice)  # ["1990", "1991", "1992"]
    # ego_list = ["A", "B"]
    # feature_slices_list = [[1, 2, 3], [11, 22, 33]]
    # feature_slices_list = np.array(feature_slices_list)
    # feature_slices_list = feature_slices_list.transpose()
    # print(feature_slices_list)
    # dataList = []
    # for row, ft_slice in enumerate(feature_slices_list):
    #     date = time_steps_slice[row]
    #     tempObj = {}
    #     tempObj["date"] = date
    #     for col, ft in enumerate(ft_slice):
    #         ego = ego_list[col]
    #         tempObj[ego] = ft
    #     dataList.append(tempObj)
    # print("dataList")
    # print(dataList)
    # feature_name_ls = list(db_client[db_name]["ego_feature_names"].find({}, {"_id": 0}))[0]["features_list"]  # [0]["features_list"]
    # print(feature_name_ls)
    db_name = "tvcg"
    db = db_client[db_name]
    db_collction = db["dynamic_graph"]
    result = db_collction.find({}, {"_id": 0})
    total_edges_len = 0
    for each_one in result:
        time_step = each_one["time_step"]
        edges_len = len(each_one["edges"])
        # print("time_step")
        # print(time_step)
        # print("edges_len")
        # print(edges_len)
        total_edges_len += edges_len
    print("total_edges_len")
    print(total_edges_len)







