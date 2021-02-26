## 前端
### 步骤:
1.安装好node.js后,使用cnpm(国内服务器)替代npm安装会快些.安装cnpm:

    sudo npm install -g cnpm --registry=https://registry.npm.taobao.org

2.安装webpack打包器:
  
    sudo cnpm i webpack -g

3.安装vue:
	
    sudo cnpm install vue
    
4.安装vue-cli脚手架构建工具(用于创建一个项目结构)

    # 全局安装 vue-cli
    $ sudo cnpm install --global vue-cli

5.在一个文件夹下,创建一个项目.
   
    # my-project为自定义项目名
    $ sudo vue init webpack my-project
 
6.在项目路径下,安装安装项目的依赖:

    sudo cnpm install
    
7.运行项目,打开界面验证是否成功:

    sudo cnpm run dev

###安装常用工具
1.安装element-ui:

    sudo cnpm install element-ui --save

###遇到的问题以及解决方法
1.使用vue-cli创建的vue项目(文件夹)带锁(其中的文件编辑后保存需要输入密码).
解决方法:在项目所在路径下打开终端输入:
     
     #sudo chown 用户名 文件夹名/ -R 
     sudo chown maotingyun my-project/ -R
去掉锁标志后,copy整个项目到任何路径都能运行.

## Vue遇到的问题
1.组件如何监听store中state的状态变化?
	
    //store.js
    import Vue from 'vue'
    import Vuex from 'vuex'
    Vue.use(Vuex);

    const store = new Vuex.Store({
    	state: {
          name: null,
          dataList: []
        }
    });
    
    // children.vue
    
    方法1:
    import { mapState } from 'vuex'
    computed: {
      ...mapState([
       "name", "dataList" // 使用...mapState将需要监听的状态映射到这个组件
      ]),
    },
    watch: {
        name: function (curVal, oldVal){
          // 可以响应状态变化. 比如,一旦'name'发生变化,就执行这里.
        }
    }
    
    方法2:
    watch: {
        "$store.state.name": function (curVal, oldVal){
          // 可以响应状态变化. 比如,一旦'name'发生变化,就执行这里.
        }
    }
2.组件中使用store中state.
前提: vuex不开启严格模式(strict: true),严格模式一般只在开发模式下开启,以便监听状态变化.而在发布模式下需要关闭该严格模式以便提高性能.
    // store.js
    //store.js
    import Vue from 'vue'
    import Vuex from 'vuex'
    Vue.use(Vuex);

    const store = new Vuex.Store({
    	state: {
          selectedDataset: null,
          datasetList: []
        }
    });
    
    // selectDb.vue
    <template>		    
	 <div id=select-dataset>      
        <el-select 
          v-model="$store.state.selectedDataset"          
          placeholder="Select Dataset">
          <el-option
              v-for="(item, index) in $store.state.datasetList"
              :key="item"
              :label="item"
              :value="item">
          </el-option>
        </el-select>
    </div>		
    </template>
总结: 
    1. 在template中使用时不用加this,如 $store.state.selectedDataset
    2. 在script中使用时,du需要加this
3.vue组件什么时候进入updated()钩子函数.
	当组件中的template渲染完事后,进入mounted状态. 当template中使用的"响应式的变量"发生变化时,该组件进行更新,更新完事后进入updated()钩子函数,然后又处于mounted状态. 注意"响应式的变量"包括: data中的属性 + computed属性 + vuex中的state状态. 举几个例:
    
    例子1:
    <template>
      <div id="time-slice-refresh">           
        <div class="slice-class" id="reflesh-time-slice">
          <div v-show='$store.getters.getselectedDataset' id='reflesh-block' class="widget-tool">
            <img class="img-icon" id="reflesh-img" width="20" height="20" src="../../static/img/refresh.svg">
          </div>
      </div>
      </div>  
    </template>
    使用了vue指令v-show,当vuex状态selectedDataset发生变化时,显示img,完毕后进入updated钩子函数.
    
    例子2:
    <template>
      <div id="egonet-sequences-box">           
       <div id="show-egonet-seq"> 
        <svg id="svg-dyegonet" :width="svgWidth" :height="$store.getters.getselectedEgoList.length * svgBaseH"></svg>    
       </div>
      </div>  
    </template>
    svg元素的属性width+height绑定了data属性或vuex状态,由于绑定的属性是响应式的,所以更新后也会进入updated钩子函数.
总结:template中使用了"响应式变量"就会进入updated钩子函数.
    
4.多个div同步滚动.
	
    // 实现效果: 滚动div1时,div2同步滚动.
    <template>
    	<div>
            <div id="div1" @scroll="scrollEvent">
            	<svg></svg>
            </div>
            <div id="div">
            	<svg></svg>
            </div>
        </div>
    </template>
    <script>
    export default {
        data(){
          return {

          }
        },
        methods:{
        	scrollEvent(eve){
             $("#div2").scrollLeft(eve.srcElement.scrollLeft); // div同步横向滚动条
            }
        }
    }
    </script>
    <style>
        #div1{
            width: 100px;
            overflow-x: auto;
            overflow-y: hidden;
        }
        #div2{
            width: 100px;
        }
    </style>
    
