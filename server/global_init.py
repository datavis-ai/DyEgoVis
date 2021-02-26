# coding: utf-8
import pymongo
# import dynetx as dn  # 原来使用安装的库,现在使用自己的文件
import dynamic_graph_lib as dn
db_client = pymongo.MongoClient("mongodb://localhost:27017/")
global_dyngraph = dn.DynGraph(edge_removal=True)  # 视为无向图

