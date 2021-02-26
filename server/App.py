# coding:utf-8
from flask import Flask, jsonify, request
from flask_cors import CORS
import os
import json

import global_init as gi
from construct_feature_vector import construction_egonet_feature_vec_for_dynet, get_filter_ego_list
from dimension_reduce import dimension_reduce_MDS, MDS_all_time_step, MDS_timeslice
from dyngraph_utility import load_global_dyngraph, get_dyegonet, get_time_curves, get_dyegonet_info
from fetch_data_from_db import fetch_all_val, query_match_nodes, get_dyegonet_detail, get_node_info, get_stacked_graph_data
# configuration
DEBUG = True

# 如下实现跨域请求.
app = Flask(__name__)
app.config.from_object(__name__)
CORS(app, resources={r"/*": {"origins": "*"}})


# fixme: responding to the request "get all dataset name" from the frontend.
@app.route('/selectdataset/dbnames', methods=['GET', 'POST'])
def select_dataset_db_names():
    db_client = gi.db_client
    all_db_names = db_client.list_database_names()  # [x, ...]
    all_db_names.remove("admin")
    all_db_names.remove("local")
    all_db_names.remove("dblp")  # fixme: 不探索dblp数据库
    db_name_obj = {"dbnamelist": all_db_names}
    return jsonify(db_name_obj)


# fixme: Responding to the request "select dataset" from the frontend.
@app.route('/selectdataset/whichdb', methods=['GET', 'POST'])
def select_dataset_which_db():
    param = json.loads(request.values.get('param'))
    db_name = param["dbname"]
    db_client = gi.db_client
    time_interval = None  # ["2001-01", "2001-01"]
    path_data = "data/" + db_name
    dissimilarity = param["whichDistance"]  # distance measure
    method_rd = param["whichMethodRD"]  # MDS, PCA or t-SNE
    normalization = param["whichMethodNorm"]  # none, min-max, z-score
    print("normalization " + normalization)
    print("method_rd " + method_rd)
    print("whichDistance " + dissimilarity)
    print("load dyngraph")
    # fixme: 装载整个时间轴上的动态图.
    nodes_time_step = load_global_dyngraph(global_dyngraph=gi.global_dyngraph, db_client=gi.db_client, db_name=db_name)  # fixme: 切换,加载对应的动态图数据.
    if time_interval:
        path_file = path_data + "/egoPoints_" + time_interval[0] + "_" + time_interval[1] + "_" + method_rd + ".json"
    else:
        path_file = path_data + "/egoPoints_none_" + method_rd + ".json"
    f_is_exist = os.path.exists(path_file)
    if f_is_exist:  # if the file exists, load data from the file.
        with open(path_file, 'r') as load_f:
            print("load egoPoints_xxx.json from the local file")
            ego_points_obj_list = json.load(load_f)  # {"mao": [x, ...], ...}
    else:
        # fixme: 根据选择的时间区间构造由(均值,方差,峰度,偏度,近似熵)拼接成的特征向量.
        print("construct the vector consisting of mean......")
        ego_vec_obj = construction_egonet_feature_vec_for_dynet(db_client=db_client,
                                                                db_name=db_name,
                                                                time_interval=time_interval,
                                                                path_data=path_data,
                                                                filter_cond=None,
                                                                is_filter=False)
        """
        ego_vec_obj: {ego1: [均值,方差,峰度,偏度,近似熵, ... 均值,方差,峰度,偏度,近似熵], ...}
        """
        print("Start dimension reduce......")
        ego_points_obj_list = dimension_reduce_MDS(db_client=db_client, db_name=db_name, ego_vec_obj=ego_vec_obj, dissimilarity=dissimilarity, method_rd=method_rd, normalization=normalization, time_interval=time_interval, path_data=path_data)
        print("End dimension reduce......")
    time_step_obj = db_client[db_name]["timeline"].find_one()
    time_step_list = time_step_obj["time_steps"]
    node_attr = None
    feature_name_ls = list(db_client[db_name]["ego_feature_names"].find({}, {"_id": 0}))[0]["features_list"]
    if db_name.lower() == "enron":
        node_attr = db_client[db_name]["ego_features"].find_one({}, {"features": 0, "_id": 0, "avg_alter_num": 0, "avg_density": 0, "avg_tie": 0, "avg_alterE_num": 0, "avg_alter2_num": 0, "avg_alter_alters": 0})
    if db_name.lower() == "tvcg":  # 只选择非数字属性.
        node_attr = db_client[db_name]["ego_features"].find_one({}, {"features": 0, "_id": 0, "p_num_year": 0, "total_p_num": 0, "avg_alter_num": 0, "avg_density": 0, "avg_tie": 0, "avg_alterE_num": 0, "avg_alter2_num": 0, "avg_alter_alters": 0})
        feature_name_ls.append("p_num_year")
    field_list = list(node_attr)
    # fixme: 生成每个时间步的概览, 现在添加过滤操作.
    timestep_mds_obj = MDS_all_time_step(db_client=db_client,
                                         db_name=db_name,
                                         nodes_time_step=nodes_time_step,
                                         method_rd=method_rd,
                                         dissimilarity=dissimilarity,
                                         max_iter=300,
                                         path_data=path_data,
                                         normalization=normalization)
    path = "data/" + db_name.lower() + "/" + db_name.lower() + "_filter_info.json"
    filter_info_obj = json.load(open(path, "r"))
    ego_points_obj = {"egoPointList": ego_points_obj_list, "timeStepList": time_step_list, "fieldList": field_list, "overviewTimeSteps": timestep_mds_obj, "obj4Filter": filter_info_obj, "ftNamels": feature_name_ls}
    return jsonify(ego_points_obj)


# fixme: Responding to the request "time slice refresh" from the frontend.
@app.route('/timeslice/refresh', methods=['GET', 'POST'])
def time_slice_refresh():
    param = json.loads(request.values.get('param'))
    db_name = param["dbname"]
    db_client = gi.db_client
    time_interval = param["timeInterval"]  # [] or ["2001-01", "2002-01"]
    dissimilarity = param["whichDistance"]
    method_rd = param["whichMethodRD"]
    normalization = param["whichMethodNorm"]
    filter_cond = param["filterCond"]
    print("whichDistance " + dissimilarity)
    print("normalization " + normalization)
    print("filter_cond")
    print(filter_cond)
    # data/enron/enron_filter_info.json
    if filter_cond == None:
        path = "data/" + db_name.lower() + "/" + db_name.lower() + "_filter_info.json"
        filter_cond = json.load(open(path, "r"))
    print("filter_cond")
    print(filter_cond)
    if len(time_interval) == 0:
        time_interval = None
    print("time_interval:")
    print(time_interval)
    path_data = "data/" + db_name
    filter_ego_list = get_filter_ego_list(db_client=db_client, db_name=db_name, filter_cond=filter_cond)
    if time_interval:
        path_file = path_data + "/egoPoints_" + time_interval[0] + "_" + time_interval[1] + "_" + method_rd + ".json"
    else:
        path_file = path_data + "/egoPoints_none_" + method_rd + ".json"
    f_is_exist = os.path.exists(path_file)
    if f_is_exist:  # if the file exists, load data from the file.
        with open(path_file, 'r') as load_f:
            print("load egoPoints_xxx.json from the local file")
            org_ego_point_list = json.load(load_f)  # [{ego: 'mao', point: [x, y], egoattrs: {attr1: x, attr2: x, ...}}, ...]
            ego_points_obj_list = []
            for ego in org_ego_point_list:  # [{ego: 'mao', ...}, ...]
                if ego["ego"] in filter_ego_list:
                    ego_points_obj_list.append(ego)
    else:
        ego_vec_obj = construction_egonet_feature_vec_for_dynet(db_client=db_client,
                                                                db_name=db_name,
                                                                time_interval=time_interval,
                                                                path_data=path_data,
                                                                filter_cond=filter_cond,
                                                                is_filter=True)
        ego_points_obj_list = dimension_reduce_MDS(db_client=db_client, db_name=db_name, ego_vec_obj=ego_vec_obj, dissimilarity=dissimilarity, method_rd=method_rd, normalization=normalization, time_interval=time_interval, path_data=path_data)
    overviews_timestep = MDS_timeslice(db_client=db_client,
                                       db_name=db_name,
                                       time_interval=time_interval,
                                       path_data=path_data,
                                       normalization=normalization,
                                       method_rd=method_rd,
                                       dissimilarity=dissimilarity,
                                       filter_ego_list=filter_ego_list)
    resp = {"egoPointList": ego_points_obj_list, "overviewTimeSteps": overviews_timestep}
    return jsonify(resp)


# fixme: responding to the request "click a point to investigate the corresponding dyegonet" from the frontend.
@app.route('/egonetsequences/dyegonet', methods=['GET', 'POST'])
def get_selected_dyegonet():
    param = json.loads(request.values.get('param'))
    db_name = param["dbname"]
    db_client = gi.db_client
    time_interval = param["timeInterval"]  # [] or ["2001-01", "2002-01"]
    if len(time_interval) == 0:
        time_interval = None
    ego = param["ego"]  # 唯一标识
    print("db_name: " + db_name)
    print("time_interval:")
    print(time_interval)
    print("ego: " + ego)
    n_level = param["egonetLevel1"]
    if n_level:
        n_level = 1
    else:
        n_level = 2
    time_line = db_client[db_name]["timeline"].find_one()
    time_steps_list = time_line["time_steps"]  # fixme: 获取时间步. [2000-03, 2000-04, ...]
    """
    dyegonet = get_dyegonet(db_client=db_client,
                            db_name=db_name,
                            global_dyngraph=gi.global_dyngraph,
                            time_steps_list=time_steps_list,
                            ego=ego,
                            time_interval=time_interval,
                            n_level=n_level)
    """
    dyegonet = get_dyegonet_info(db_client=db_client,
                            db_name=db_name,
                            global_dyngraph=gi.global_dyngraph,
                            time_steps_list=time_steps_list,
                            ego=ego,
                            time_interval=time_interval,
                            n_level=n_level)

    # print("dyegonet")
    # print(dyegonet)
    return jsonify(dyegonet)


# fixme: responding to the request "get the time curve view" from the frontend.
@app.route('/timecurveview/getalltimecurves', methods=['GET', 'POST'])
def get_all_timecurve():
    param = json.loads(request.values.get('param'))
    db_name = param["dbname"]
    db_client = gi.db_client
    ego_list = param["selectedegolist"]
    time_interval = param["timeInterval"]  # [] or ["2001-01", "2002-01"]
    dissimilarity = param["whichDistance"]
    method_rd = param["whichMethodRD"]
    # print("dissimilarity timecurve")
    # print(dissimilarity)
    if len(time_interval) == 0:
        time_interval = None
    time_curve_obj = get_time_curves(db_client=db_client, db_name=db_name, ego_list=ego_list, time_interval=time_interval, dissimilarity=dissimilarity, method_rd=method_rd)
    return jsonify(time_curve_obj)


# fixme: responding to the request "get field value" from the frontend.
@app.route('/searchbox/getfieldallval', methods=['GET', 'POST'])
def get_field_all_val():
    param = json.loads(request.values.get('param'))
    db_name = param["dbname"]
    db_client = gi.db_client
    field = param["field"]
    print("field")
    print(field)
    field_val_list = fetch_all_val(db_client=db_client, db_name=db_name, field=field)
    return jsonify(field_val_list)


# fixme: responding to the request "search" from the frontend.
@app.route('/searchbox/getqueryresults', methods=['GET', 'POST'])
def get_query_results():
    param = json.loads(request.values.get('param'))
    db_name = param["dbname"]
    db_client = gi.db_client
    field = param["field"]
    query_item = param["queryKeywords"]
    print("field")
    print(field)
    print("query_item")
    print(query_item)
    query_results = query_match_nodes(db_client=db_client, db_name=db_name, field=field, query_item=query_item)
    return jsonify(query_results)


# fixme: responding to the request "click filter icon" from the frontend.
@app.route("/overview/filter", methods=['GET', 'POST'])
def get_filter_information():
    param = json.loads(request.values.get('param'))
    db_name = param["dbname"]
    # print("get_filter_information")
    # print(db_name)
    path = "data/" + db_name.lower() + "/" + db_name.lower() + "_filter_info.json"
    load_obj = json.load(open(path, "r"))
    return jsonify(load_obj)


# fixme: 获得对应的dyegonet信息.
@app.route("/overview/dyegonetDetail", methods=['GET', 'POST'])
def dyegonet_detail():
    param = json.loads(request.values.get('param'))
    db_name = param["dbname"]
    db_client = gi.db_client
    egoId = param["egoId"]
    infoObj = get_dyegonet_detail(db_client=db_client, db_name=db_name, egoId=egoId)
    return jsonify(infoObj)


@app.route("/overview/nodeDetail", methods=['GET', 'POST'])
def dyegonet_node_detail():
    param = json.loads(request.values.get('param'))
    db_client = gi.db_client
    db_name = param["dbname"]
    ego_id = param["egoId"]
    node_id = param["nodeId"]
    tslice = param["tslice"]  # time slice: [4, 7]
    # print("ego_id")
    # print(ego_id)
    # print("node_id")
    # print(node_id)
    result = get_node_info(dyegonet=gi.global_dyngraph,
                           db_client=db_client,
                           db_name=db_name,
                           ego_id=ego_id,
                           node_id=node_id,
                           tslice=tslice)
    return jsonify(result)


@app.route("/stackedGraph/data", methods=['GET', 'POST'])
def get_stacked_graph():
    param = json.loads(request.values.get('param'))
    db_name = param["dbname"]
    db_client = gi.db_client
    time_interval = param["timeInterval"]
    if len(time_interval) == 0:
        time_interval = None
    ego_list = param["selectedegolist"]
    feature = param["feature"]
    stacked_graph_obj = get_stacked_graph_data(db_client=db_client,
                                               db_name=db_name,
                                               time_interval=time_interval,
                                               ego_list=ego_list,
                                               feature=feature)
    return jsonify(stacked_graph_obj)


if __name__ == "__main__":
    app.run(port=5000, debug=True)