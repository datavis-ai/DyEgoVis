# coding:utf-8
import numpy as np
from sklearn.manifold import MDS, TSNE
from sklearn.metrics import pairwise_distances
from collections import defaultdict
from sklearn import preprocessing
from sklearn.decomposition import PCA
"""
说明: dynetx中动态图的存储格式:
json文件中的动态图表示形式: {2000-03: [{source: 'A', target: 'B', weight: 2}], 2000-04: [{source: 'A', target: 'B', weight: 3}, {source: 'A', target: 'C', weight: 5}]}

dynetx根据以上json数据建立的动态图在内存中的格式:
    adj = {A: {B: {'t': [[0,1]], 'weight': {0: 2, 1: 3}}, C: {'t': [[1, 1]], 'weight': {1: 5}}}}
以字典的形式存储,遵循networkx的存储格式.下面看networkx静态图的存储格式:
    import networkx as nx
        G = nx.Graph()
        G.add_weighted_edges_from([("A", "B", 2), ("A", "C", 5)])
        r = G.adj
        print(r)
    格式为: adj = {'C': {'A': {'weight': 5}}, 'B': {'A': {'weight': 2}}, 'A': {'C': {'weight': 5}, 'B': {'weight': 2}}}
"""


# fixme: 更换数据库时,重新加载对应的动态网络.
def load_global_dyngraph(global_dyngraph=None, db_client=None, db_name=None):
    """
    :param global_dyngraph: global dynamic graph.
    :param db_client: mongodb client
    :param db_name: name of current database
    :return: nodes_time_step = {2000-03: [ego1, ego2, ..., egom], ...}, i.e., a node set per year.
    """
    global_dyngraph.clear()  # 清除原来的动态图
    db = db_client[db_name]  # mongodb数据库
    db_collction = db["dynamic_graph"]  # 对应的表, {2000: [{source: x, target: x, frequency: x}, ...], ...}
    all_items = db_collction.find()  # 取出集合"dynamic_graph"中所有的文档(格式: [{time_step: x, edges: [{}, ...]}, ...])
    time_line = db["timeline"].find_one()  # 取出时间线{id_: x, time_steps: [2000-03, ...]}
    time_steps_list = time_line["time_steps"]  # time_steps_list= ["2000-03", ...]
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
        # fixme: 创建动态图.
        global_dyngraph.add_interactions_from(ebunch=links_list, t=step_index)  # [G0, G1, ...]
    return nodes_time_step


# fixme: 为 actors (ego + alters)计算位置
def compute_pos_alters(actors_s_l_list, cur_total_steps, from_index):
    """
    :param actors_s_l_list: e.g., [(id, start_time, length), ...], (id, start_time, length): 节点id, 首次出现的时间, 长度; 长度 = 最后时间 - 初始时间 + 1
    :param cur_total_steps: total time steps
    :param from_index: 时间区间的起始位置.
    :return: actor_pos = {node1: [起始位置, ..., 结尾位置], node2: [], ...}
    注意: 如果一个alter在t=1首次出现, 在t=5最后出现, 无论中间是否出现, 长度都是5-1+1=5
    """
    actors_s_l_list = sorted(actors_s_l_list, key=lambda s: s[2], reverse=True)  # 按照长度进行排序
    actors_s_l_list = sorted(actors_s_l_list, key=lambda s: s[1], reverse=False)  # 按照起始时间进行排序
    s_up = 0
    s_down = 0
    L_up = [0] * cur_total_steps  # 用于记录下方alters
    L_down = [0] * cur_total_steps  # 用于记录上方alters
    actor_pos = defaultdict(list)  # fixme: actor_pos = {node1: [起始位置, ..., 结尾位置], node2: [0, -1, -1, ..., 0], ...}
    size_set = set()  # fixme: 用于找出当前dyegonet在整个时间轴上的偏离ego的最大位置.
    for actor in actors_s_l_list:  # actor = (alterId, start_time, len_t)
        # if s_up < s_down:  # 此时不一定上下对称
        if s_up <= s_down:  # 现在改成上下对称
            # s_up = s_up + actor[2]  # 此时不一定上下对称
            s_up = s_up + 1
            for j in range(actor[1] - from_index, actor[1] - from_index + actor[2]):  # fixme: j是时间步的索引.
                L_up[j] = L_up[j] + 1
                actor_pos[actor[0]].append(-L_up[j])
        else:
            # s_down = s_down + actor[2]  # 此时不一定上下对称
            s_down = s_down + 1
            for j in range(actor[1] - from_index, actor[1] - from_index + actor[2]):
                L_down[j] = L_down[j] + 1
                actor_pos[actor[0]].append(L_down[j])

        # fixme: 因为对应的列表中的位置可负或可正
        size_set.add(abs(max(actor_pos[actor[0]], key=abs)))
    if len(size_set) == 0:
        maxs_ = 0
    else:
        maxs_ = max(size_set)
    snapshot_pos_num = []
    for idx, val in enumerate(L_up):
        num_pos = max(L_down[idx], val) * 2  # 两者中选择最大的, 然后乘以2.
        snapshot_pos_num.append(num_pos)


    return actor_pos, maxs_, snapshot_pos_num


# fixme: 根据选中的ego抽取出其对应的dyegonet.
def get_dyegonet(db_client=None, db_name=None, global_dyngraph=None, time_steps_list=None, ego=None, time_interval=None, n_level=2):
    """
    :param dynet: 全局动态网络.
    :param ego: 指定的ego(即节点id或唯一性标识)
    :param time_interval: 选中的时间区间, [2000-03, 2000-08]
    :param n_level: 1-level: egonet由ego的1跳邻居构成, 2-level: egonet由2跳内邻居构成.
    :return:
     dynegog =
     {dyegonet: {2000-03: {nodes: {ego: {id:x, name:x, ...}, nbrs1: [{}, ...], nbrs2: [{}, ...]}, links: {nbrs1: [{source: x, target: x, weight: x}, ...], nbrs2: [{}, ...]}}, ...},
      nbrs1t: {pos: {a1: [-1, -2, -1], ...}, tslice: {a1: [4, 6], ...}}, // 1-level邻居的布局位置(pos), 以及起始和终止时间(tslice).
      nbrs2t: {pos: {b1: [-1, -2, -1], ...}, tslice: {b1: [4, 6], ...}} // 2-level邻居的布局位置(pos), 以及起始和终止时间(tslice).
      maxs1: x, // alter1偏离ego的最大位置
      maxs2: x, // alter2偏离ego的最大位置
      egots: [x, x] // dyegonet的时间切片, i.e., [start_time, end_time],
      pos_num_alter1: [x, x, x, ...], // 每个snapshot下alter1位置的数量, 用于调整每个时间步下邻居的数量.
      pos_num_alter2: [x, x, x, ...]  // 每个snapshot下alter2位置的数量, 用于调整每个时间步下邻居的数量.
     }
    """

    if time_interval is not None:  # e.g., time_interval=[2000-03, 2000-04]
        from_index = time_steps_list.index(time_interval[0])
        to_index = time_steps_list.index(time_interval[1])
    else:
        from_index = 0
        to_index = len(time_steps_list) - 1
    cur_total_steps = to_index - from_index + 1  # 当前的总时间步 = 时间切片的长度.
    # fixme: 每个时间步下的 egonet = 节点 + 边, {2000-03: {nodes: {"ego": {}, "nbrs1": [], "nbrs2": []}, links: {"nbrs1": [], "nbrs2": []}}}
    dyegonet_obj = {}
    nbrs1_id_set = set()
    nbrs1_t_attr = {}  # {nodeId: [[0, 3], [4, 4], [6, 9]]}, 表示 0-3 / 6-9 之间持续出现, 而4时刻出现1次
    nbrs2_t_attr = defaultdict(set)  # {"a": set(), ...}
    # size_nbrs1_set = set()  # 用于求出最大1-level alters大小
    ego_timestep_set = set()  # fixme: 用于找出ego出现的时间段. {2000-03, 2000-05, ...}
    # fixme: 指定不需要的属性. {"features": 0, "_id": 0}
    no_need_ft = {"_id": 0, "ego": 0, "features": 0, "avg_density": 0, "avg_alterE_num": 0, "avg_alter2_num": 0, "avg_alter_alters": 0}
    if db_name.lower() == "tvcg":
        no_need_ft["r_interests"] = 0
        no_need_ft["p_num_year"] = 0
        no_need_ft["org"] = 0
    # fixme: 被选中的时间跨度内, 每个时间步骤下的egonet.
    for each_step in range(from_index, to_index + 1):
        if n_level == 1:  # fixme: 只取1跳以内的邻居
            nbrs_list = global_dyngraph.neighbors(n=ego, t=each_step)  # 获得在指定时间步下, 指定点的所有邻居(in/out)
            len_nbr = len(nbrs_list)
            # fixme: {"nbrs1": [ego-alter1边 + alter1-alter1边], "nbrs2": []}, 边格式: {source: x, target: x, weight: x}
            nbrs_edges_obj = {"nbrs1": [], "nbrs2": []}
            ego_nbrs_obj = {"ego": {}, "nbrs1": [], "nbrs2": []}  # {ego: {id:x, name:x, position:x}, nbrs1: [{}, ...], nbrs2: [{}, ...]}
            if len_nbr > 0:
                ego_timestep_set.add(each_step)
                # fixme: 获得ego的信息{id: ego, name: x, attr1: x, ...}, 将其放入 ego_nbrs_obj 中.
                node_obj = {}  # {id: x, name: x, position: x}
                node_obj["id"] = ego
                doc_obj = db_client[db_name]["ego_features"].find({"ego": ego}, no_need_ft)  # 从数据库中读取ego对应的name
                doc_obj = list(doc_obj)[0]  # doc_obj=[{}] -> {f1: x, f2: x, ...}
                for each_i in doc_obj:
                    node_obj[each_i] = doc_obj[each_i]
                ego_nbrs_obj["ego"] = node_obj

                for nbr_i in range(len_nbr - 1):  # 这里要找出邻居之间的边,所以先减去1.
                    # fixme: 先构建 ego-alter1边.
                    u = nbrs_list[nbr_i]
                    edge_obj = {}
                    edge_obj["source"] = ego
                    edge_obj["target"] = u
                    node_obj = {}
                    node_obj["id"] = u
                    nbrs1_id_set.add(u)
                    doc_obj = db_client[db_name]["ego_features"].find({"ego": u}, no_need_ft)  # 从数据库中读取ego对应的name
                    doc_obj = list(doc_obj)[0]  # doc_obj=[{}] -> {f1: x, f2: x, ...}
                    for each_i in doc_obj:
                        node_obj[each_i] = doc_obj[each_i]
                    ego_nbrs_obj["nbrs1"].append(node_obj)
                    attr_obj = global_dyngraph.get_edge_data(u=ego, v=u)  # {'weight': {0: 100, 1: 100}, 't': [[0, 1]]}
                    if u not in nbrs1_t_attr:
                        nbrs1_t_attr[u] = attr_obj["t"]
                    edge_weight = attr_obj['weight'][each_step]
                    edge_obj["weight"] = edge_weight
                    nbrs_edges_obj["nbrs1"].append(edge_obj)  # {nbrs1: [{source: x, target: x, weight: x}, ...]}
                    # fixme: 构建 alter1-alter1 边.
                    for nbr_j in range(nbr_i + 1, len_nbr):
                        v = nbrs_list[nbr_j]
                        if global_dyngraph.has_interaction(u=u, v=v, t=each_step):
                            edge_obj = {}
                            edge_obj["source"] = u
                            edge_obj["target"] = v
                            attr_obj = global_dyngraph.get_edge_data(u=u, v=v)  # {'weight': {0: 100, 1: 100}, 't': [[0, 1]]}
                            edge_weight = attr_obj['weight'][each_step]
                            edge_obj["weight"] = edge_weight
                            nbrs_edges_obj["nbrs1"].append(edge_obj)
                # fixme: 最后一条 ego-alter1 边.
                edge_obj = {}
                edge_obj["source"] = ego
                uu = nbrs_list[-1]
                edge_obj["target"] = uu
                attr_obj = global_dyngraph.get_edge_data(u=ego, v=uu)  # {'weight': {0: 100, 1: 100}, 't': [[0, 1]]}
                if uu not in nbrs1_t_attr:
                    nbrs1_t_attr[uu] = attr_obj["t"]
                edge_weight = attr_obj['weight'][each_step]
                edge_obj["weight"] = edge_weight
                nbrs_edges_obj["nbrs1"].append(edge_obj)  # {nbrs1: [{source: x, target: x, weight: x}, ...]}
                node_obj = {}
                node_obj["id"] = uu
                nbrs1_id_set.add(uu)
                doc_obj = db_client[db_name]["ego_features"].find({"ego": uu}, no_need_ft)  # 从数据库中读取ego对应的name
                doc_obj = list(doc_obj)[0]  # doc_obj=[{}] -> {f1: x, f2: x, ...}
                for each_i in doc_obj:
                    node_obj[each_i] = doc_obj[each_i]
                ego_nbrs_obj["nbrs1"].append(node_obj)
            # fixme: {2000-03: {nodes: {"ego": {}, "nbrs1": [], "nbrs2": []}, links: {"nbrs1": [], "nbrs2": []}}}
            # size_nbrs1_set.add((time_steps_list[each_step], len(ego_nbrs_obj["nbrs1"])))  # fixme: 目前只考虑1-level alters.
            dyegonet_obj[time_steps_list[each_step]] = {"nodes": ego_nbrs_obj, "links": nbrs_edges_obj}

        if n_level == 2:  # fixme: 取2跳以内的邻居, alter1 + alter2
            # fixme: {"nbrs1": [ego-alter1边 + alter1-alter1边], "nbrs2": [alter1-alter2边 + alter2-alter2边]}, 边格式: {source: x, target: x, weight: x}
            nbrs_edges_obj = {"nbrs1": [], "nbrs2": []}
            ego_nbrs_obj = {"ego": {}, "nbrs1": [], "nbrs2": []}  # {ego: {id:x, name:x, position:x}, nbrs1: [{}, ...], nbrs2: [{}, ...]}
            nbrs_level1 = global_dyngraph.neighbors(n=ego, t=each_step)
            if len(nbrs_level1) > 0:
                ego_timestep_set.add(each_step)
                nbrs_set2 = []  # 2-level alters.
                # fixme: 先获得ego信息.
                node_obj = {}
                node_obj["id"] = ego
                doc_obj = db_client[db_name]["ego_features"].find({"ego": ego}, no_need_ft)  # 从数据库中读取ego对应的name
                doc_obj = list(doc_obj)[0]  # doc_obj=[{}] -> {f1: x, f2: x, ...}
                for each_i in doc_obj:
                    node_obj[each_i] = doc_obj[each_i]
                ego_nbrs_obj["ego"] = node_obj
                for nbr in nbrs_level1:
                    # fixme: 获得 alter1 信息
                    node_obj = {}
                    node_obj["id"] = nbr
                    doc_obj = db_client[db_name]["ego_features"].find({"ego": nbr}, no_need_ft)  # 从数据库中读取ego对应的name
                    doc_obj = list(doc_obj)[0]  # doc_obj=[{}] -> {f1: x, f2: x, ...}
                    for each_i in doc_obj:
                        node_obj[each_i] = doc_obj[each_i]
                    ego_nbrs_obj["nbrs1"].append(node_obj)
                    # fixme: 构建 ego-alter 边.
                    edge_obj = {}
                    edge_obj["source"] = ego
                    edge_obj["target"] = nbr
                    attr_obj = global_dyngraph.get_edge_data(u=ego, v=nbr)  # {'weight': {0: 100, 1: 100}, 't': [[0, 1]]}
                    if nbr not in nbrs1_t_attr:  # fixme: 一阶邻居存在的时间.
                        nbrs1_t_attr[nbr] = attr_obj["t"]
                    edge_weight = attr_obj['weight'][each_step]
                    edge_obj["weight"] = edge_weight
                    nbrs_edges_obj["nbrs1"].append(edge_obj)
                for each_nbr in nbrs_level1:
                    for nbr2 in global_dyngraph.neighbors(n=each_nbr, t=each_step):
                        # fixme: alters2.
                        if nbr2 != ego and nbr2 not in nbrs_level1:
                            if nbr2 not in nbrs_set2:
                                # fixme: 获得 alters2 节点信息.
                                nbrs_set2.append(nbr2)
                                node_obj = {}
                                node_obj["id"] = nbr2
                                doc_obj = db_client[db_name]["ego_features"].find({"ego": nbr2}, no_need_ft)  # 从数据库中读取ego对应的name
                                # for each_i in doc_obj:
                                #     node_obj["name"] = each_i["name"]
                                #     if db_name == "enron":
                                #         node_obj["position"] = each_i["position"]  # fixme: 中期时加的
                                doc_obj = list(doc_obj)[0]  # doc_obj=[{}] -> {f1: x, f2: x, ...}
                                for each_i in doc_obj:
                                    node_obj[each_i] = doc_obj[each_i]
                                ego_nbrs_obj["nbrs2"].append(node_obj)
                            # fixme: 构造 alter1-alter2 边
                            edge_obj = {}
                            edge_obj["source"] = each_nbr
                            edge_obj["target"] = nbr2
                            attr_obj = global_dyngraph.get_edge_data(u=each_nbr, v=nbr2)  # {'weight': {0: 100, 1: 100}, 't': [[0, 1]]}
                            for t in attr_obj["t"]:  # [[], [], ...]
                                nbrs2_t_attr[nbr2].add(tuple(t))
                            edge_weight = attr_obj['weight'][each_step]
                            edge_obj["weight"] = edge_weight
                            nbrs_edges_obj["nbrs2"].append(edge_obj)
                len_1 = len(nbrs_level1)
                len_2 = len(nbrs_set2)
                # fixme: 构造 alter1-alter1 边
                for nbr_i in range(len_1 - 1):
                    u = nbrs_level1[nbr_i]
                    for nbr_j in range(nbr_i + 1, len_1):
                        v = nbrs_level1[nbr_j]
                        if global_dyngraph.has_interaction(u=u, v=v, t=each_step):
                            edge_obj = {}
                            edge_obj["source"] = u
                            edge_obj["target"] = v
                            attr_obj = global_dyngraph.get_edge_data(u=u, v=v)  # {'weight': {0: 100, 1: 100}, 't': [[0, 1]]}
                            edge_weight = attr_obj['weight'][each_step]
                            edge_obj["weight"] = edge_weight
                            nbrs_edges_obj["nbrs1"].append(edge_obj)
                # fixme: 构造 alter2-alter2 边
                for nbr_i in range(len_2 - 1):
                    u = nbrs_set2[nbr_i]
                    for nbr_j in range(nbr_i + 1, len_2):
                        v = nbrs_set2[nbr_i]
                        if global_dyngraph.has_interaction(u=u, v=v, t=each_step):
                            edge_obj = {}
                            edge_obj["source"] = u
                            edge_obj["target"] = v
                            attr_obj = global_dyngraph.get_edge_data(u=u, v=v)  # {'weight': {0: 100, 1: 100}, 't': [[0, 1]]}
                            edge_weight = attr_obj['weight'][each_step]
                            edge_obj["weight"] = edge_weight
                            nbrs_edges_obj["nbrs2"].append(edge_obj)
            dyegonet_obj[time_steps_list[each_step]] = {"nodes": ego_nbrs_obj, "links": nbrs_edges_obj}
    # fixme: 以下是计算 egonet 中alter1节点的位置的算法, 参考论文: egoline.
    dynegog = {"nbrs1t": {}, "nbrs2t": {}}
    dynegog["dyegonet"] = dyegonet_obj  # 每个时间步下的egonet的节点和边信息.
    nbrs1_s_l_list = []  # [(nodeId, 2, 4), ...]
    for nbr1 in nbrs1_t_attr:  # {nodeId: [[0, 3], [5, 5], [7, 9]]}
        min_t = nbrs1_t_attr[nbr1][0][0]  # [[], [], ...]
        max_t = nbrs1_t_attr[nbr1][-1][1]  # [[], [], ...]
        # fixme: 加上时间区间限制后
        if min_t < from_index and from_index <= max_t <= to_index:  # 右半部分有效
            nbrs1_t_attr[nbr1] = [from_index, max_t]
            nbrs1_s_l_list.append((nbr1, from_index, max_t - from_index + 1))
        if from_index <= min_t and max_t <= to_index:  # 整个区间有效
            nbrs1_t_attr[nbr1] = [min_t, max_t]
            nbrs1_s_l_list.append((nbr1, min_t, max_t - min_t + 1))
        if from_index <= min_t <= to_index and to_index < max_t:  # 左半部分有效.
            nbrs1_t_attr[nbr1] = [min_t, to_index]
            nbrs1_s_l_list.append((nbr1, min_t, to_index - min_t + 1))
        if min_t < from_index and to_index < max_t:
            nbrs1_t_attr[nbr1] = [from_index, to_index]
            nbrs1_s_l_list.append((nbr1, from_index, to_index - from_index + 1))

    # fixme: 为每个alter1计算位置
    nbrs1_actor_pos, maxs1, snapshot_pos_num = compute_pos_alters(actors_s_l_list=nbrs1_s_l_list, cur_total_steps=cur_total_steps, from_index=from_index)  # 原来的.
    dynegog["nbrs1t"]["tslice"] = nbrs1_t_attr  # 起点是整个时间轴的起点, 每个alter1的时间切片, {alter1: [min_t, max_t], ...}
    dynegog["nbrs1t"]["pos"] = nbrs1_actor_pos  # 每个alter1在每个时间步下的位置.
    dynegog["maxs1"] = 2 * maxs1
    dynegog["pos_num_alter1"] = snapshot_pos_num
    # fixme: 为每个alter2计算位置.
    nbrs2_s_l_list = []  # [("alter2", 2, 4), ...]
    for nbr2 in nbrs2_t_attr:
        node_set = set()
        for tt in nbrs2_t_attr[nbr2]:
            for t in range(tt[0], tt[1] + 1):
                node_set.add(t)
        min_t = min(node_set)
        max_t = max(node_set)
        # fixme: 限制在时间区间内: 分为节点的区间与时间轴区间的对比, 小于, 等于, 大于.
        if min_t < from_index and from_index <= max_t <= to_index:  # 右半部分有效
            nbrs2_t_attr[nbr2] = [from_index, max_t]
            nbrs2_s_l_list.append((nbr2, from_index, max_t - from_index + 1))
        if from_index <= min_t and max_t <= to_index:  # 整个区间有效
            nbrs2_t_attr[nbr2] = [min_t, max_t]
            nbrs2_s_l_list.append((nbr2, min_t, max_t - min_t + 1))
        if from_index <= min_t <= to_index and to_index < max_t:  # 左半部分有效.
            nbrs2_t_attr[nbr2] = [min_t, to_index]
            nbrs2_s_l_list.append((nbr2, min_t, to_index - min_t + 1))
        if min_t < from_index and to_index < max_t:
            nbrs2_t_attr[nbr2] = [from_index, to_index]
            nbrs2_s_l_list.append((nbr2, from_index, to_index - from_index + 1))
    nbrs2_actor_pos, maxs2, snapshot_pos_num = compute_pos_alters(actors_s_l_list=nbrs2_s_l_list, cur_total_steps=cur_total_steps, from_index=from_index)  # 原来的
    dynegog["nbrs2t"]["tslice"] = nbrs2_t_attr  # 每个alter2的时间切片, {alter2: [min_t, max_t], ...}
    dynegog["nbrs2t"]["pos"] = nbrs2_actor_pos  # 每个alter2在每个时间步的位置.
    dynegog["maxs2"] = 2 * maxs2
    dynegog["pos_num_alter2"] = snapshot_pos_num
    min_t, max_t = min(ego_timestep_set), max(ego_timestep_set)
    if min_t < from_index and from_index <= max_t <= to_index:
        dynegog["egots"] = [from_index, max_t]
    if from_index <= min_t and max_t <= to_index:
        dynegog["egots"] = [min_t, max_t]
    if from_index <= min_t <= to_index and to_index < max_t:
        dynegog["egots"] = [min_t, to_index]
    return dynegog


# fixme: 根据前端选中的egos,获得其egonet序列的"time curve"
def get_time_curves(db_client=None, db_name=None, ego_list=None, time_interval=None, dissimilarity="canberra", normalization="min-max", method_rd="MDS"):
    """
    :param db_client: mongodb client
    :param db_name: database name
    :param ego_list: a ego list, i.e., [ego1, ego2, ..., egom]
    :param time_interval: None or e.g., [2000-03, 2000-08]
    :param dissimilarity: canberra or euclidean
    :param method_rd: PCA/MDS/t-SNE
    :return: ego_time_curves_obj={ego1: {"2000-08": {"xy": [x, y], "feature_vec": [x, ...]}, "2000-09": {}, ...}, ...}
    """
    method_rd = "MDS"  # 始终使用MDS, 这个效果最好.
    db = db_client[db_name]
    ego_feature_names = db["ego_feature_names"].find_one()
    features_list = ego_feature_names["features_list"]  # [f1, f2, ...]
    time_line = db["timeline"].find_one()
    time_steps_list = time_line["time_steps"]  # time_steps_list= ["2000-03", ...]
    if time_interval is not None:
        start_index = time_steps_list.index(time_interval[0])
        end_index = time_steps_list.index(time_interval[1])
    else:
        start_index = 0
        end_index = len(time_steps_list) - 1
    ego_time_curves_obj = {}  # fixme: {ego1: {"2000-08": {"xy": [x, y], "feature_vec": [x, ...]}, "2000-09": {}, ...}, ...}
    ego_time_curves_f_list = []  # fixme: 特征矩阵, 所有ego的所有时间步骤下的特征, [[f1, ..., f6], ...].
    for each_ego in ego_list:
        doc_obj = db_client[db_name]["ego_features"].find_one({"ego": each_ego})  # fixme: 使用find_one({条件})找出一个符合条件的字典(对象), find({条件})找出所有符合条件的文档所在位置(需要使用for迭代)
        features = doc_obj["features"]  # {f1: [], f2: [], ...}
        ego_name = doc_obj["name"]
        feature_value_list = []
        for each_f in features_list:  # [f1, f2, ...]
            f_v_list = features[each_f]  # fixme:
            f_v_list = f_v_list[start_index:(end_index + 1)]
            feature_value_list.append(f_v_list)
        time_step_f_list = np.mat(feature_value_list).transpose().tolist()  # fixme: [[f1, f2, f3, ...,f6], [f1, f2, f3, ...,f6], ...]
        counter_index = -1
        ego_each_time_step_obj = {}  # {2000-08: {feature_vec: [f1, ...,f6]}, ...}
        for each_index in range(start_index, end_index + 1):
            counter_index += 1
            current_time_step = time_steps_list[each_index]  # 2000-08
            each_time_step_f = time_step_f_list[counter_index]  # [f1, f2, f3, ...,f6]
            ego_each_time_step_obj[current_time_step] = {"feature_vec": each_time_step_f}
            ego_time_curves_f_list.append(each_time_step_f + [])  # + []: 拷贝, 避免污染原来的数据.
        ego_time_curves_obj[each_ego] = ego_each_time_step_obj
    ##################### Normalization ############################
    if normalization.lower() == "min-max":
        # fixme: min-max Normalization
        min_max_scaler = preprocessing.MinMaxScaler()
        ego_time_curves_f_list = min_max_scaler.fit_transform(ego_time_curves_f_list)  # min-max normalization
    if normalization.lower() == "z-score":
        standar_scaler = preprocessing.StandardScaler()
        ego_time_curves_f_list = standar_scaler.fit_transform(ego_time_curves_f_list)
    ####################### End Normalization ######################
    points_list = None
    if method_rd.lower() == "mds":
        if dissimilarity == "euclidean":
            embedding = MDS(n_components=2, max_iter=300, n_init=1)
            points_list = embedding.fit_transform(ego_time_curves_f_list).tolist()
        else:
            embedding = MDS(n_components=2, max_iter=300, n_init=1, dissimilarity="precomputed")
            canberra_dist_list = pairwise_distances(X=ego_time_curves_f_list, metric=dissimilarity)
            points_list = embedding.fit_transform(canberra_dist_list).tolist()
    if method_rd.lower() == "t-sne":
        if dissimilarity == "euclidean":
            points_list = TSNE(n_components=2).fit_transform(ego_time_curves_f_list)
        else:
            canberra_dist_list = pairwise_distances(X=ego_time_curves_f_list, metric=dissimilarity)
            points_list = TSNE(n_components=2, metric="precomputed").fit_transform(canberra_dist_list)
        temp = []  # [[], ...]
        for each_one in points_list:
            each_one = list(map(float, each_one))
            temp.append(each_one)
        points_list = temp
    if method_rd.lower() == "pca":
        pca = PCA(n_components=2)
        points_list = pca.fit_transform(ego_time_curves_f_list)

    counter_ego_index = -1
    time_steps_slice = time_steps_list[start_index:(end_index + 1)]  # ["2000-03", "2000-04", ...]
    for each_ego in ego_list:
        counter_ego_index += 1
        index_ = counter_ego_index * len(time_steps_slice)
        points_list_slice = points_list[index_:(index_ + len(time_steps_slice))]  # [[x, y], [x, y]]
        counter_time_step_index = -1
        for each_time_step in time_steps_slice:  # ["2000", "2001"]
            counter_time_step_index += 1
            x_y_point = points_list_slice[counter_time_step_index]
            ego_time_curves_obj[each_ego][each_time_step]["point"] = x_y_point
    return ego_time_curves_obj


# fixme: 修正版本, 根据选中的ego抽取出其对应的dyegonet.
def get_dyegonet_info(db_client=None, db_name=None, global_dyngraph=None, time_steps_list=None, ego=None, time_interval=None, n_level=2):
    """
    :param dynet: 全局动态网络.
    :param ego: 指定的ego(即节点id或唯一性标识)
    :param time_interval: 选中的时间区间, [2000-03, 2000-08]
    :param n_level: 1-level: egonet由ego的1跳邻居构成, 2-level: egonet由2跳内邻居构成.
    :return:
     dynegog =
     {dyegonet: {2000-03: {nodes: {ego: {id:x, name:x, ...}, nbrs1: [{}, ...], nbrs2: [{}, ...]}, links: {nbrs1: [{source: x, target: x, weight: x}, ...], nbrs2: [{}, ...]}}, ...},
      nbrs1t: {pos: {a1: [-1, -2, -1], ...}, tslice: {a1: [4, 6], ...}}, // 1-level邻居的布局位置(pos), 以及起始和终止时间(tslice).
      maxs1: x, // alter1偏离ego的最大位置
      egots: [x, x] // dyegonet的时间切片, i.e., [start_time, end_time],
      pos_num_alter1: [x, x, x, ...], // 每个snapshot下alter1位置的数量, 用于调整每个时间步下邻居的数量.
      nbrs12: [id1, id2, ...] // 属于1-degree和2-degree的alter1.
     }
    """

    if time_interval is not None:  # e.g., time_interval=[2000-03, 2000-04]
        from_index = time_steps_list.index(time_interval[0])
        to_index = time_steps_list.index(time_interval[1])
    else:
        from_index = 0
        to_index = len(time_steps_list) - 1
    cur_total_steps = to_index - from_index + 1  # 当前的总时间步 = 时间切片的长度.
    # fixme: 每个时间步下的 egonet = 节点 + 边, {2000-03: {nodes: {"ego": {}, "nbrs1": [], "nbrs2": []}, links: {"nbrs1": [], "nbrs2": []}}}
    dyegonet_obj = {}
    nbrs1_id_set = set()
    nbrs1_t_attr = {}  # {nodeId: [[0, 3], [4, 4], [6, 9]]}, 表示 0-3 / 6-9 之间持续出现, 而4时刻出现1次
    nbrs2_t_attr = defaultdict(set)  # {"a": set(), ...} 之前的
    # nbrs2_t_attr = {}  # {"a": set(), ...} 修改后
    ego_timestep_set = set()  # fixme: 用于找出ego出现的时间段. {2000-03, 2000-05, ...}
    # fixme: 指定不需要的属性. {"features": 0, "_id": 0}
    no_need_ft = {"_id": 0, "ego": 0, "features": 0, "avg_density": 0, "avg_alterE_num": 0, "avg_alter2_num": 0, "avg_alter_alters": 0}
    if db_name.lower() == "tvcg":
        no_need_ft["r_interests"] = 0
        no_need_ft["p_num_year"] = 0
        no_need_ft["org"] = 0
    # fixme: 被选中的时间跨度内, 每个时间步骤下的egonet.
    for each_step in range(from_index, to_index + 1):
        if n_level == 1:  # fixme: 只取1跳以内的邻居
            nbrs_list = global_dyngraph.neighbors(n=ego, t=each_step)  # 获得在指定时间步下, 指定点的所有邻居(in/out)
            len_nbr = len(nbrs_list)
            # fixme: {"nbrs1": [ego-alter1边 + alter1-alter1边], "nbrs2": []}, 边格式: {source: x, target: x, weight: x}
            nbrs_edges_obj = {"nbrs1": [], "nbrs2": []}
            ego_nbrs_obj = {"ego": {}, "nbrs1": [], "nbrs2": []}  # {ego: {id:x, name:x, position:x}, nbrs1: [{}, ...], nbrs2: [{}, ...]}
            if len_nbr > 0:
                ego_timestep_set.add(each_step)
                # fixme: 获得ego的信息{id: ego, name: x, attr1: x, ...}, 将其放入 ego_nbrs_obj 中.
                node_obj = {}  # {id: x, name: x, position: x}
                node_obj["id"] = ego
                doc_obj = db_client[db_name]["ego_features"].find({"ego": ego}, no_need_ft)  # 从数据库中读取ego对应的name
                doc_obj = list(doc_obj)[0]  # doc_obj=[{}] -> {f1: x, f2: x, ...}
                for each_i in doc_obj:
                    node_obj[each_i] = doc_obj[each_i]
                ego_nbrs_obj["ego"] = node_obj

                for nbr_i in range(len_nbr - 1):  # 这里要找出邻居之间的边,所以先减去1.
                    # fixme: 先构建 ego-alter1边.
                    u = nbrs_list[nbr_i]
                    edge_obj = {}
                    edge_obj["source"] = ego
                    edge_obj["target"] = u
                    node_obj = {}
                    node_obj["id"] = u
                    nbrs1_id_set.add(u)
                    doc_obj = db_client[db_name]["ego_features"].find({"ego": u}, no_need_ft)  # 从数据库中读取ego对应的name
                    doc_obj = list(doc_obj)[0]  # doc_obj=[{}] -> {f1: x, f2: x, ...}
                    for each_i in doc_obj:
                        node_obj[each_i] = doc_obj[each_i]
                    ego_nbrs_obj["nbrs1"].append(node_obj)
                    attr_obj = global_dyngraph.get_edge_data(u=ego, v=u)  # {'weight': {0: 100, 1: 100}, 't': [[0, 1]]}
                    if u not in nbrs1_t_attr:
                        nbrs1_t_attr[u] = attr_obj["t"]
                    edge_weight = attr_obj['weight'][each_step]
                    edge_obj["weight"] = edge_weight
                    nbrs_edges_obj["nbrs1"].append(edge_obj)  # {nbrs1: [{source: x, target: x, weight: x}, ...]}
                    # fixme: 构建 alter1-alter1 边.
                    for nbr_j in range(nbr_i + 1, len_nbr):
                        v = nbrs_list[nbr_j]
                        if global_dyngraph.has_interaction(u=u, v=v, t=each_step):
                            edge_obj = {}
                            edge_obj["source"] = u
                            edge_obj["target"] = v
                            attr_obj = global_dyngraph.get_edge_data(u=u, v=v)  # {'weight': {0: 100, 1: 100}, 't': [[0, 1]]}
                            edge_weight = attr_obj['weight'][each_step]
                            edge_obj["weight"] = edge_weight
                            nbrs_edges_obj["nbrs1"].append(edge_obj)
                # fixme: 最后一条 ego-alter1 边.
                edge_obj = {}
                edge_obj["source"] = ego
                uu = nbrs_list[-1]
                edge_obj["target"] = uu
                attr_obj = global_dyngraph.get_edge_data(u=ego, v=uu)  # {'weight': {0: 100, 1: 100}, 't': [[0, 1]]}
                if uu not in nbrs1_t_attr:
                    nbrs1_t_attr[uu] = attr_obj["t"]
                edge_weight = attr_obj['weight'][each_step]
                edge_obj["weight"] = edge_weight
                nbrs_edges_obj["nbrs1"].append(edge_obj)  # {nbrs1: [{source: x, target: x, weight: x}, ...]}
                node_obj = {}
                node_obj["id"] = uu
                nbrs1_id_set.add(uu)
                doc_obj = db_client[db_name]["ego_features"].find({"ego": uu}, no_need_ft)  # 从数据库中读取ego对应的name
                doc_obj = list(doc_obj)[0]  # doc_obj=[{}] -> {f1: x, f2: x, ...}
                for each_i in doc_obj:
                    node_obj[each_i] = doc_obj[each_i]
                ego_nbrs_obj["nbrs1"].append(node_obj)
            # fixme: {2000-03: {nodes: {"ego": {}, "nbrs1": [], "nbrs2": []}, links: {"nbrs1": [], "nbrs2": []}}}
            # size_nbrs1_set.add((time_steps_list[each_step], len(ego_nbrs_obj["nbrs1"])))  # fixme: 目前只考虑1-level alters.
            dyegonet_obj[time_steps_list[each_step]] = {"nodes": ego_nbrs_obj, "links": nbrs_edges_obj}

        if n_level == 2:  # fixme: 取2跳以内的邻居, alter1 + alter2
            # fixme: {"nbrs1": [ego-alter1边 + alter1-alter1边], "nbrs2": [alter1-alter2边 + alter2-alter2边]}, 边格式: {source: x, target: x, weight: x}
            nbrs_edges_obj = {"nbrs1": [], "nbrs2": []}
            ego_nbrs_obj = {"ego": {}, "nbrs1": [], "nbrs2": []}  # {ego: {id:x, name:x, position:x}, nbrs1: [{}, ...], nbrs2: [{}, ...]}
            nbrs_level1 = global_dyngraph.neighbors(n=ego, t=each_step)
            if len(nbrs_level1) > 0:
                ego_timestep_set.add(each_step)
                nbrs_set2 = []  # 2-level alters.
                # fixme: 先获得ego信息.
                node_obj = {}
                node_obj["id"] = ego
                doc_obj = db_client[db_name]["ego_features"].find({"ego": ego}, no_need_ft)  # 从数据库中读取ego对应的name
                doc_obj = list(doc_obj)[0]  # doc_obj=[{}] -> {f1: x, f2: x, ...}
                for each_i in doc_obj:
                    node_obj[each_i] = doc_obj[each_i]
                ego_nbrs_obj["ego"] = node_obj
                for nbr in nbrs_level1:
                    # fixme: 获得 alter1 信息
                    node_obj = {}
                    node_obj["id"] = nbr
                    doc_obj = db_client[db_name]["ego_features"].find({"ego": nbr}, no_need_ft)  # 从数据库中读取ego对应的name
                    doc_obj = list(doc_obj)[0]  # doc_obj=[{}] -> {f1: x, f2: x, ...}
                    for each_i in doc_obj:
                        node_obj[each_i] = doc_obj[each_i]
                    ego_nbrs_obj["nbrs1"].append(node_obj)
                    # fixme: 构建 ego-alter 边.
                    edge_obj = {}
                    edge_obj["source"] = ego
                    edge_obj["target"] = nbr
                    attr_obj = global_dyngraph.get_edge_data(u=ego, v=nbr)  # {'weight': {0: 100, 1: 100}, 't': [[0, 1]]}
                    if nbr not in nbrs1_t_attr:  # fixme: 一阶邻居存在的时间.
                        nbrs1_t_attr[nbr] = attr_obj["t"]  # {id1: [[], ...]}
                    edge_weight = attr_obj['weight'][each_step]
                    edge_obj["weight"] = edge_weight
                    nbrs_edges_obj["nbrs1"].append(edge_obj)
                for each_nbr in nbrs_level1:
                    for nbr2 in global_dyngraph.neighbors(n=each_nbr, t=each_step):
                        # fixme: alters2.
                        if nbr2 != ego and nbr2 not in nbrs_level1:
                            if nbr2 not in nbrs_set2:
                                # fixme: 获得 alters2 节点信息.
                                nbrs_set2.append(nbr2)
                                node_obj = {}
                                node_obj["id"] = nbr2
                                doc_obj = db_client[db_name]["ego_features"].find({"ego": nbr2}, no_need_ft)  # 从数据库中读取ego对应的name
                                # for each_i in doc_obj:
                                #     node_obj["name"] = each_i["name"]
                                #     if db_name == "enron":
                                #         node_obj["position"] = each_i["position"]  # fixme: 中期时加的
                                doc_obj = list(doc_obj)[0]  # doc_obj=[{}] -> {f1: x, f2: x, ...}
                                for each_i in doc_obj:
                                    node_obj[each_i] = doc_obj[each_i]
                                ego_nbrs_obj["nbrs2"].append(node_obj)
                            # fixme: 构造 alter1-alter2 边
                            edge_obj = {}
                            edge_obj["source"] = each_nbr
                            edge_obj["target"] = nbr2
                            attr_obj = global_dyngraph.get_edge_data(u=each_nbr, v=nbr2)  # {'weight': {0: 100, 1: 100}, 't': [[0, 1]]}
                            # fixme: 获得仅仅是alter12的时间步 Start
                            ego_n1_list = []  # 23 24
                            for each_ts in nbrs1_t_attr[each_nbr]:  # [[4, 5], ...]
                                for t in range(each_ts[0], each_ts[1] + 1):
                                    ego_n1_list.append(t)
                            n1_n2_list = []  # 23 24
                            for each_ts in attr_obj["t"]:  # [[3, 6], ...]
                                for t in range(each_ts[0], each_ts[1] + 1):
                                    n1_n2_list.append(t)
                            # 23 24
                            ego_n1_n2_list = list(set(ego_n1_list).intersection(n1_n2_list))

                            ego_n2_list = []
                            ego_nbr2 = global_dyngraph.get_edge_data(u=ego, v=nbr2)
                            if ego_nbr2:
                                for each_ts in ego_nbr2["t"]:  # [[4, 5], ...]
                                    for t in range(each_ts[0], each_ts[1] + 1):
                                        ego_n2_list.append(t)
                                tri_t_list = list(set(ego_n1_n2_list).intersection(ego_n2_list))
                                as_alter2_t_list = list(set(ego_n1_n2_list) - set(tri_t_list))  # 取补集, 这样就将作为alter1的时间去掉.
                            else:
                                as_alter2_t_list = ego_n1_n2_list
                            # fixme: 获得仅仅是alter12的时间步 END
                            for t in as_alter2_t_list:  # [x, ...]  # 之前的
                                nbrs2_t_attr[nbr2].add(t)
                            # if nbr2 == "2177988531":
                            #     print("2177988531")
                            #     print("ego_n1_list")
                            #     print(ego_n1_list)
                            #     print("n1_n2_list")
                            #     print(n1_n2_list)
                            #     print("ego_n1_n2_list")
                            #     print(ego_n1_n2_list)
                            #     print("ego_n2_list")
                            #     print(ego_n2_list)
                            #     # print("ego_n2_list")
                            #     # print(ego_n2_list)
                            #     print("tri_t_list")
                            #     print(tri_t_list)
                            #     print("as_alter2_t_list")
                            #     print(as_alter2_t_list)
                            edge_weight = attr_obj['weight'][each_step]
                            edge_obj["weight"] = edge_weight
                            nbrs_edges_obj["nbrs2"].append(edge_obj)
                len_1 = len(nbrs_level1)
                len_2 = len(nbrs_set2)
                # fixme: 构造 alter1-alter1 边
                for nbr_i in range(len_1 - 1):
                    u = nbrs_level1[nbr_i]
                    for nbr_j in range(nbr_i + 1, len_1):
                        v = nbrs_level1[nbr_j]
                        if global_dyngraph.has_interaction(u=u, v=v, t=each_step):
                            edge_obj = {}
                            edge_obj["source"] = u
                            edge_obj["target"] = v
                            attr_obj = global_dyngraph.get_edge_data(u=u, v=v)  # {'weight': {0: 100, 1: 100}, 't': [[0, 1]]}
                            edge_weight = attr_obj['weight'][each_step]
                            edge_obj["weight"] = edge_weight
                            nbrs_edges_obj["nbrs1"].append(edge_obj)
                # fixme: 构造 alter2-alter2 边
                for nbr_i in range(len_2 - 1):
                    u = nbrs_set2[nbr_i]
                    for nbr_j in range(nbr_i + 1, len_2):
                        v = nbrs_set2[nbr_i]
                        if global_dyngraph.has_interaction(u=u, v=v, t=each_step):
                            edge_obj = {}
                            edge_obj["source"] = u
                            edge_obj["target"] = v
                            attr_obj = global_dyngraph.get_edge_data(u=u, v=v)  # {'weight': {0: 100, 1: 100}, 't': [[0, 1]]}
                            edge_weight = attr_obj['weight'][each_step]
                            edge_obj["weight"] = edge_weight
                            nbrs_edges_obj["nbrs2"].append(edge_obj)
            dyegonet_obj[time_steps_list[each_step]] = {"nodes": ego_nbrs_obj, "links": nbrs_edges_obj}
    # fixme: 首先, 找出既是1-degree又是2-degree的alter1
    nbrs2_list = list(nbrs2_t_attr.keys())  # [id1, id2, ...]
    nbrs1_list = list(nbrs1_t_attr.keys())  # [id1, id2, ...]
    alter12_lsit = list(set(nbrs1_list).intersection(nbrs2_list))  # 交集, 既是1-degree alter 也是 2-degree alter
    # fixme: 获得 alter12_lsit 中属于2-degree alter的时间区间
    nbrs12_t_arr = {}  # 同时属于1-degree和2-degree的alter, {id: [min_t, max_t], ...}
    nbrs12_occur_time = {}
    for nbr2 in alter12_lsit:
        # node_set = set()
        node_set = nbrs2_t_attr[nbr2]  # set({x, ...})
        # for tt in nbrs2_t_attr[nbr2]:  # nbrs2_t_attr = {id: set(), ...}
        #     for t in range(tt[0], tt[1] + 1):
        #         node_set.add(t)
            # node_set.add(tt[0])
            # node_set.add(tt[1])
        nbrs12_occur_time[nbr2] = list(node_set)  # fixme: {id: [1, 2, 3, 4], ...}, 代表alter12出现的时间步.
        min_t = min(node_set)
        max_t = max(node_set)
        # fixme: 限制在时间区间内: 分为节点的区间与时间轴区间的对比, 小于, 等于, 大于.
        if min_t < from_index and from_index <= max_t <= to_index:  # 右半部分有效
            nbrs12_t_arr[nbr2] = [from_index, max_t]
        if from_index <= min_t and max_t <= to_index:  # 整个区间有效
            nbrs12_t_arr[nbr2] = [min_t, max_t]
        if from_index <= min_t <= to_index and to_index < max_t:  # 左半部分有效.
            nbrs12_t_arr[nbr2] = [min_t, to_index]
        if min_t < from_index and to_index < max_t:
            nbrs12_t_arr[nbr2] = [from_index, to_index]

    # fixme: 以下是计算 egonet 中alter1节点的位置的算法, 参考论文: egoline.
    dynegog = {"nbrs1t": {}, "nbrs2t": {}, "nbrs12t": {}}
    dynegog["dyegonet"] = dyegonet_obj  # 每个时间步下的egonet的节点和边信息.
    nbrs1_s_l_list = []  # [(nodeId, 2, 4), ...]
    nbrs1_s_l_obj = {}  # {id: (nodeId, 2, 4), ...}
    for nbr1 in nbrs1_t_attr:  # {nodeId: [[0, 3], [5, 5], [7, 9]]}
        min_t = nbrs1_t_attr[nbr1][0][0]  # [[], [], ...]
        max_t = nbrs1_t_attr[nbr1][-1][1]  # [[], [], ...]
        # fixme: 加上时间区间限制后
        if min_t < from_index and from_index <= max_t <= to_index:  # 右半部分有效
            nbrs1_t_attr[nbr1] = [from_index, max_t]
            # nbrs1_s_l_list.append((nbr1, from_index, max_t - from_index + 1))
            nbrs1_s_l_obj[nbr1] = (nbr1, from_index, max_t - from_index + 1)
        if from_index <= min_t and max_t <= to_index:  # 整个区间有效
            nbrs1_t_attr[nbr1] = [min_t, max_t]
            # nbrs1_s_l_list.append((nbr1, min_t, max_t - min_t + 1))
            nbrs1_s_l_obj[nbr1] = (nbr1, min_t, max_t - min_t + 1)
        if from_index <= min_t <= to_index and to_index < max_t:  # 左半部分有效.
            nbrs1_t_attr[nbr1] = [min_t, to_index]
            # nbrs1_s_l_list.append((nbr1, min_t, to_index - min_t + 1))
            nbrs1_s_l_obj[nbr1] = (nbr1, min_t, to_index - min_t + 1)
        if min_t < from_index and to_index < max_t:
            nbrs1_t_attr[nbr1] = [from_index, to_index]
            # nbrs1_s_l_list.append((nbr1, from_index, to_index - from_index + 1))
            nbrs1_s_l_obj[nbr1] = (nbr1, from_index, to_index - from_index + 1)
    # fixme: 调整既是1-degree又是2-degree的alter1的时间区间.
    for nbr12 in nbrs12_t_arr:
        t_set = set()
        nbr12_min_t, nbr12_max_t = nbrs12_t_arr[nbr12]
        t_set.add(nbr12_min_t)
        t_set.add(nbr12_max_t)
        nbr1_min_t, nbr1_max_t = nbrs1_t_attr[nbr12]
        t_set.add(nbr1_min_t)
        t_set.add(nbr1_max_t)
        min_t = min(t_set)
        max_t = max(t_set)
        nbrs1_t_attr[nbr12] = [min_t, max_t]
        nbrs1_s_l_obj[nbr12] = (nbr12, min_t, max_t - min_t + 1)
    for alter in nbrs1_s_l_obj:
        nbrs1_s_l_list.append(nbrs1_s_l_obj[alter])
    # fixme: 为每个alter1计算位置
    nbrs1_actor_pos, maxs1, snapshot_pos_num = compute_pos_alters(actors_s_l_list=nbrs1_s_l_list, cur_total_steps=cur_total_steps, from_index=from_index)  # 原来的.
    dynegog["nbrs1t"]["tslice"] = nbrs1_t_attr  # 起点是整个时间轴的起点, 每个alter1的时间切片, {alter1: [min_t, max_t], ...}
    dynegog["nbrs1t"]["pos"] = nbrs1_actor_pos  # 每个alter1在每个时间步下的位置.
    dynegog["maxs1"] = 2 * maxs1
    dynegog["pos_num_alter1"] = snapshot_pos_num
    dynegog["nbrs12"] = alter12_lsit  # fixme: 属于1-degree和2-degree的alter1.
    dynegog["nbrs12t"] = nbrs12_occur_time  # 每个alter2的时间切片, {alter12: [1, 2, 5, 7], ...}
    """    
    # fixme: 为每个alter2计算位置.
    nbrs2_s_l_list = []  # [("alter2", 2, 4), ...]
    for nbr2 in nbrs2_t_attr:
        node_set = set()
        for tt in nbrs2_t_attr[nbr2]:
            for t in range(tt[0], tt[1] + 1):
                node_set.add(t)
        min_t = min(node_set)
        max_t = max(node_set)
        # fixme: 限制在时间区间内: 分为节点的区间与时间轴区间的对比, 小于, 等于, 大于.
        if min_t < from_index and from_index <= max_t <= to_index:  # 右半部分有效
            nbrs2_t_attr[nbr2] = [from_index, max_t]
            nbrs2_s_l_list.append((nbr2, from_index, max_t - from_index + 1))
        if from_index <= min_t and max_t <= to_index:  # 整个区间有效
            nbrs2_t_attr[nbr2] = [min_t, max_t]
            nbrs2_s_l_list.append((nbr2, min_t, max_t - min_t + 1))
        if from_index <= min_t <= to_index and to_index < max_t:  # 左半部分有效.
            nbrs2_t_attr[nbr2] = [min_t, to_index]
            nbrs2_s_l_list.append((nbr2, min_t, to_index - min_t + 1))
        if min_t < from_index and to_index < max_t:
            nbrs2_t_attr[nbr2] = [from_index, to_index]
            nbrs2_s_l_list.append((nbr2, from_index, to_index - from_index + 1))
    nbrs2_actor_pos, maxs2, snapshot_pos_num = compute_pos_alters(actors_s_l_list=nbrs2_s_l_list, cur_total_steps=cur_total_steps, from_index=from_index)  # 原来的
    dynegog["nbrs2t"]["tslice"] = nbrs2_t_attr  # 每个alter2的时间切片, {alter2: [min_t, max_t], ...}
    dynegog["nbrs2t"]["pos"] = nbrs2_actor_pos  # 每个alter2在每个时间步的位置.
    dynegog["maxs2"] = 2 * maxs2
    dynegog["pos_num_alter2"] = snapshot_pos_num
    """
    dynegog["nbrs2t"]["tslice"] = {}  # 每个alter2的时间切片, {alter2: [min_t, max_t], ...}
    dynegog["nbrs2t"]["pos"] = {}  # 每个alter2在每个时间步的位置.
    dynegog["maxs2"] = 0
    dynegog["pos_num_alter2"] = [0] * cur_total_steps

    min_t, max_t = min(ego_timestep_set), max(ego_timestep_set)
    if min_t < from_index and from_index <= max_t <= to_index:
        dynegog["egots"] = [from_index, max_t]
    if from_index <= min_t and max_t <= to_index:
        dynegog["egots"] = [min_t, max_t]
    if from_index <= min_t <= to_index and to_index < max_t:
        dynegog["egots"] = [min_t, to_index]
    return dynegog


if __name__ == "__main__":
    # import pymongo
    # db_client = pymongo.MongoClient("mongodb://localhost:27017/")
    # db_name = "enron"
    #
    # time_interval = ["2000-04", "2000-05"]
    # ego_list = ["jason.williams", "danny.mccarty"]
    # get_time_curves(db_client=db_client, db_name=db_name, ego_list=ego_list, time_interval=time_interval)

    def func(a, b):
        intersection = list(set(a).intersection(b))
        return intersection
    # a = [1, 2, 34, 5]
    # b = [11, 2, 34, 15]
    # r = func(a, b)
    # print(r)
    # obj = {"a": 10, "b": 20}
    # r = list(obj.keys())
    # print(r)
    # a = {}
    # a["A"] = (1, 2, 3)
    # a["B"] = (1, 2, 3)
    # a["C"] = (1, 2, 3)
    # print(a)
    # b = []
    # for each_one in a:
    #     b.append(a[each_one])
    # print(b)
    # ego_n1_n2_list = [24, 23]
    # tri_t_list = [24]
    # as_alter2_t_list = list(set(ego_n1_n2_list) - set(tri_t_list))
    # print(as_alter2_t_list)
    a = {"mao": 100, "jj": 50}
    if "mao" in a:
        print("uu")



