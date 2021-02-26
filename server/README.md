---
title: Ubuntu错误解决记录
categories: 工具使用
tags: [问题解决,Ubuntu]
mathjax: true
---

### python相关库安装问题

#### 问题1：无法正常卸载库

 　　在<span class="blockFont">升级scipy</span> 的过程中，出现了如下问题：

```python
Cannot uninstall 'scipy'. It is a distutils installed project and thus we cannot accurately
determine which files belong to it which would lead to only a partial uninstall.
```

　　这是因为已经没有了旧版本scipy已安装文件的元数据，从而不能正常卸载，需要我们来手动删除，其解决步骤如下：

1. 搜索scipy模块的路径

   ```
   import scipy
   print(scipy.__file__)  # 通常路径为：usr/lib/python3/dist-packages
   ```

2. 找到并删除该路径下的 scipy文件夹以及相应的.egg-info文件

#### 问题2：库文件下载超时

 　　在进行安装python相关库的过程中，需要下载<span class="blockFont">.whl文件</span>，由于下载源的问题，导致一些文件下载异常的缓慢，从而产生下载超时的问题，中断下载安装：

```python
raise ReadTimeoutError(self._pool, None, 'Read timed 
out.')p._vendor.requests.packages.urllib3.exceptions.ReadTimeoutError: 
HTTPSConnectionPool(host='pypi.python.org', port=443): Read timed out
```

　　**解决：**

　　方法一：修改超时时间（不建议下载慢的话可以选择）

```python
pip --default-timeout=1000 install -U module_name
```

　　方法二：将下载和安装的过程分开来，先在安装信息里找到<span class="blockFont">.whl文件</span>的下载链接，然后拷贝到其他网速情况较好的环境里（比如在PC端电脑上）将.whl文件下载好来，最后拷贝到Ubuntu上进行安装。
　　文件下载链接格式如下：

```python
https://files.pythonhosted.org/packages/cd/32/5196b64476bd41d596a8aba43506e2403e019c90e1a3dfc21d
51b83db5a6/scipy-1.1.0-cp35-cp35m-manylinux1_x86_64.whl
```

　　安装方式如pip：

```python
sudo pip3 install scipy-1.1.0-cp35-cp35m-manylinux1_x86_64.whl
```

### Ubuntu系统操作错误问题

#### 问题1：系统卡死在桌面无法操作

　　linux有多个虚拟终端（virtual console ），也就是<span class="blockFont">tty终端</span>，tty1~tty6都是只有命令行的，而tty7模式是GUI，即图形界面的（如果切换到tty7终端的话，就是退出其他tty终端，返回到桌面），解决步骤如下：

1. 按住Ctrl+Alt+F1进入tty1终端（同理进入tty2 - tty7，按Ctrl+Alt+F2 - Ctrl+Alt+F7）；

2. 进入tty终端后先输入你的用户名和密码登录；

3. 先尝试使用sudo重启桌面，如果不行就继续第4步；

   ```
   sudo restart  lightdm
   ```

4. 切换到root权限：

   ```
   su root
   ```

5. 输入如下命令重启桌面：

   ```
   service lightdm restart
   ```
   
6. ModuleNotFoundError: No module named 'numpy.testing.decorators'
   
   pip install -U numpy==1.18.0   
   
   numpy升级到1.18.0版本后，发现原有正常的程序报错。
   ModuleNotFoundError: No module named 'numpy.testing.decorators'

   google一下，发现其他人在github上提问了

   发现是由于1.18.0版本新引出的问题。

   无奈只能卸载1.18.0版本的numpy，重新安装1.17.0的numpy

   sudo pip uninstall numpy
   sudo pip install numpy==1.17.0
   
   numpy版本为1.17.0时，程序可以正常运行了。   

### DBLP数据处理问题.
从Aminer下载的数据DBLP.V12.json为12G, 作为本地文件使用python处理时会造成内存溢出,解决方法:
1.创建数据库"DBLP", 在该数据库中创建一个表"papers".
2.将数据导入mongodb数据库中. 具体地, 在文件所在路径打开终端, 输入以下命令:
		
    mongoimport --db "DBLP" --collection "papers" --type json --file "dblp.v12.json" --jsonArray

### dynamic_graph_lib.py中动态图存储结构
现在只用到了无向图, 对于有向图而言, 需要将其转化成无向图.

    
    attr_obj = global_dyngraph.get_edge_data(u=ego, v=each_one)  # {'weight': {0: 100, 1: 100}, 't': [[0, 1]]}
    