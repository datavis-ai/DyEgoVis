// eslint-disable-next-line
/* eslint-disable */
const backPort = 'http://127.0.0.1:5000';
const vueFlaskRouterConfig = {	
	selectdataset: backPort + '/selectdataset/whichdb',
	dbnames: backPort + '/selectdataset/dbnames',
	timeSliceRefresh: backPort + '/timeslice/refresh',
	selecteddyegonet: backPort + '/egonetsequences/dyegonet',
	getalltimecurves: backPort + "/timecurveview/getalltimecurves",
	getFieldAllVal: backPort + "/searchbox/getfieldallval",
	getQueryResults: backPort + "/searchbox/getqueryresults",
	clickFilterEgos: backPort + "/overview/filter",
	dyegonetDetail: backPort + "/overview/dyegonetDetail",
	nodeDetail: backPort + "/overview/nodeDetail",
    getStackedGraph: backPort + "/stackedGraph/data"
};
// let searchFlag=false; // 搜索点击标志位.
export {	
	vueFlaskRouterConfig
	// searchFlag,
}