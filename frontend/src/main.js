// The Vue build version to load with the `import` command
// (runtime-only or standalone) has been set in webpack.base.conf with an alias.
import Vue from 'vue'
import App from './App'
import Element from 'element-ui' 
import 'element-ui/lib/theme-chalk/index.css'
import locale from 'element-ui/lib/locale/lang/en'
Vue.use(Element, {locale}) // Vue.use(plugin), 添加一个插件.
Vue.config.productionTip = false
import {store} from './store' // vuex状态管理.
// console.log("here main.js")
// import VueNouislider from 'vue-nouislider' 
// Vue.use(VueNouislider)
// eslint-disable-next-line
/* eslint-disable */
new Vue({
  el: '#app',
  store,
  components: {App},
  template: '<App/>'
})
