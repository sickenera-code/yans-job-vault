const fs = require('node:fs');
const path = require('node:path');
const vm = require('node:vm');
const assert = require('node:assert/strict');
const root = path.join(__dirname, '../assets/vault');
const markdown = fs.readFileSync(path.join(root,'已投递岗位/00-从夯到拉.md'),'utf8');
const code = markdown.match(/```dataviewjs\n([\s\S]*?)\n```/)[1];
new (Object.getPrototypeOf(async function(){}).constructor)('app','dv',code);
let text = fs.readFileSync(path.join(root,'Resource/岗位评级数据.md'),'utf8');
let fail = false;
const alerts = [];
const vault = {
  getAbstractFileByPath:()=>({}), read:async()=>text,
  process:async(file,update)=>{if(fail)throw Error('模拟写入失败');text=update(text);return text;}
};
const context = vm.createContext({app:{vault},alert:m=>alerts.push(m),confirm:()=>true,renderFull:()=>{}});
const constants=code.slice(code.indexOf('const LEVELS'),code.indexOf('// 数据源：dataview'));
const logic=code.slice(code.indexOf('// ---- 状态 ----'),code.indexOf('// ---- 渲染组件 ----'));
vm.runInContext(constants+logic+'\nglobalThis.api={loadRankMap,parseRankMap,rebuildState,moveItem,clearAllRanks,state};',context);
const api=context.api;
const job=n=>({company:'测试企业'+n,position:'岗位',seq:n,date:'2026-09-18',file:{path:`已投递岗位/0${n}-测试岗位.md`}});
(async()=>{
  let map=await api.loadRankMap();api.rebuildState([],map);
  assert.equal(api.state.pool.length,0);
  api.rebuildState([job(1),job(2)],map);
  await api.moveItem(job(1).file.path,'夯');
  assert.equal(api.parseRankMap(text)['夯'][0],job(1).file.path);
  map=await api.loadRankMap();api.rebuildState([job(1),job(2),job(3)],map);
  assert.equal(api.state.ranks['夯'].length,1);assert.equal(api.state.pool.length,2);
  await api.moveItem(job(1).file.path,'顶级');
  assert.equal(api.parseRankMap(text)['夯'].length,0);assert.equal(api.parseRankMap(text)['顶级'].length,1);
  fail=true;await api.moveItem(job(1).file.path,'拉完了');fail=false;
  assert.equal(api.state.ranks['顶级'].length,1);assert.equal(api.state.ranks['拉完了'].length,0);
  text+='\n其他窗口的修改\n';await api.moveItem(job(1).file.path,'夯');
  assert.equal(api.state.ranks['顶级'].length,1);assert.ok(text.endsWith('其他窗口的修改\n'));
  await api.loadRankMap();await api.moveItem(job(1).file.path,'pool');
  assert.equal(api.state.pool.length,3);
  await api.moveItem(job(2).file.path,'NPC');await api.clearAllRanks();
  assert.equal(api.state.pool.length,3);assert.equal(api.parseRankMap(text)['NPC'].length,0);
  assert.throws(()=>api.parseRankMap('损坏的数据'));
  assert.equal(alerts.length,2);
  console.log('PASS: 评级页面编译、空仓库、新增岗位、跨档拖动、重开恢复、退回候补池、清除评级、写入失败与冲突保护');
})().catch(e=>{console.error(e);process.exitCode=1;});
