/* Exercises the actual DataviewJS logic with a minimal Obsidian Vault API. */
const fs = require('node:fs');
const path = require('node:path');
const vm = require('node:vm');
const assert = require('node:assert/strict');
const { webcrypto } = require('node:crypto');
const root = path.join(__dirname, '../assets/vault');
const codeOf = file => fs.readFileSync(path.join(root, file), 'utf8').replace(/^```dataviewjs\s*\n/, '').replace(/\n```\s*$/, '');
const AsyncFunction = Object.getPrototypeOf(async function(){}).constructor;
for (const file of ['投递进度.md', '秋招关注.md', '公考时间.md']) new AsyncFunction('dv','app',codeOf(file));
class Vault {
  constructor() { this.files = new Map(); this.failFolder = false; }
  getAbstractFileByPath(p) { return this.files.get(p) || null; }
  add(p, item) {
    if (this.files.has(p)) throw Error('Already exists: '+p);
    const parent = this.files.get(p.split('/').slice(0,-1).join('/'));
    if (p.includes('/') && !parent?.children) throw Error('Missing parent');
    item.name=p.split('/').pop(); item.path=p;
    this.files.set(p,item); if (parent) parent.children.push(item); return item;
  }
  async createFolder(p) {
    if (this.failFolder && p.startsWith('已投递岗位/')) { this.failFolder=false; throw Error('模拟目录失败'); }
    return this.add(p,{children:[]});
  }
  async create(p,text) { return this.add(p,{text}); }
  async read(file) { if (file.text===undefined) throw Error('Not file');return file.text; }
  async modify(file,text) { file.text=text; }
}
async function harness(file='投递进度.md') {
  const code=codeOf(file); const vault=new Vault(); const alerts=[];
  await vault.createFolder('Resource');
  const dataPath=file==='投递进度.md'?'Resource/投递记录数据.md':'Resource/秋招关注数据.md';
  await vault.create(dataPath,fs.readFileSync(path.join(root,dataPath),'utf8'));
  const ctx=vm.createContext({app:{vault}, console,crypto:webcrypto,alert:m=>alerts.push(m),window:{},render:()=>{},Date,URL,
    localStorage:{getItem:()=>{throw Error('不应读旧缓存');},removeItem:()=>{throw Error('不应改旧缓存');}}});
  const head=code.slice(0,code.indexOf('const styleId'));
  let functions=code.slice(code.indexOf('const DATA_FILE'),code.indexOf('function renderHeader'));
  const isJob=file==='投递进度.md';
  if (isJob) {
    const add=code.slice(code.indexOf('window.addApplication ='),code.indexOf('// 显示添加阶段模态框'));
    vm.runInContext(head+functions+add+`\nglobalThis.api={loadData,saveData,syncAllJobNotes,syncJobNote,buildJobNoteContent,parseDataFile,validateApplications,get:()=>applications,set:v=>applications=v};`,ctx);
  } else {
    // Watch helper functions below loadData do not need evaluation for persistence tests.
    functions=functions.slice(0,functions.indexOf('function getMonthsUntil'));
    vm.runInContext(head+functions+'\nglobalThis.api={loadData,saveData,parseDataFile,get:()=>watchPositions,set:v=>watchPositions=v};',ctx);
  }
  return {api:ctx.api,window:ctx.window,vault,alerts,dataPath};
}
const record=(id='one')=>({id,company:'示例/公司',position:'分析[实习]:岗',date:'2026-09-14',type:'private',link:'',stages:[],offer:false,terminated:false});
(async()=>{
  const {api,vault,dataPath}=await harness();
  await api.loadData();assert.equal(api.get().length,0);
  const item=record(); api.set([item]); await api.saveData();await api.syncAllJobNotes();
  assert.equal(item.notePath,'已投递岗位/01-示例-公司 分析-实习--岗.md');
  assert.equal(item.folderPath,item.notePath.slice(0,-3));
  const note=vault.getAbstractFileByPath(item.notePath);note.text+='\n用户整理的 JD\n';
  await vault.create(item.folderPath+'/专题.md','保留材料');
  await api.syncAllJobNotes();assert.match(note.text,/用户整理的 JD/);
  assert.equal(vault.getAbstractFileByPath(item.folderPath+'/专题.md').text,'保留材料');
  const retry=record();await api.syncJobNote(retry);assert.equal(retry.notePath,item.notePath);
  await vault.createFolder('已投递岗位/09-旧目录');
  const second=record('two');await api.syncJobNote(second);assert.match(second.notePath,/\/10-/);
  item.company='公司 $& $`';await api.saveData();
  assert.equal(api.parseDataFile(vault.getAbstractFileByPath(dataPath).text)[0].company,item.company);
  await assert.rejects(()=>api.syncJobNote({...record('escape'),notePath:'../外部.md'}));
  await assert.rejects(()=>api.syncJobNote({...item,id:'another-owner'}));
  assert.throws(()=>api.validateApplications([record(),record()]));
  assert.throws(()=>api.parseDataFile('损坏的正文'));
  console.log('PASS: 页面编译、空数据、目录命名、最大序号、保留内容、幂等、路径校验、字面量持久化');

  const failed=await harness();
  await failed.api.loadData();failed.vault.failFolder=true;
  const values={companyInput:'测试企业',positionInput:'测试岗位',typeInput:'private',dateInput:'2026-09-14',linkInput:''};
  await failed.window.addApplication({preventDefault(){},currentTarget:{querySelector:selector=>({value:values[selector.slice(1)]})}});
  assert.equal(failed.api.parseDataFile(failed.vault.getAbstractFileByPath(failed.dataPath).text).length,1);
  assert.ok(failed.alerts.some(a=>a.includes('已保存投递记录')));
  await failed.api.loadData();await failed.api.syncAllJobNotes();
  const repaired=failed.api.get()[0];
  assert.ok(failed.vault.getAbstractFileByPath(repaired.folderPath+'/00-资料索引.md'));
  assert.equal([...failed.vault.files.keys()].filter(p=>/^已投递岗位\/[^/]+\.md$/.test(p)).length,1);
  console.log('PASS: 表单记录先保存、目录失败后重新加载恢复、不重复创建笔记');

  const watch=await harness('秋招关注.md');await watch.api.loadData();assert.equal(watch.api.get().length,0);
  watch.api.set([{id:'watch-01',company:'关注 $& $`',type:'private',status:'watching',expectedDate:'2026-10',url:'',note:'备注',stages:[]}]);
  await watch.api.saveData();await watch.api.loadData();assert.equal(watch.api.get()[0].company,'关注 $& $`');
  console.log('PASS: 关注页持久化、重新加载不丢记录');
})().catch(error=>{console.error(error);process.exitCode=1;});
