#!/usr/bin/env python3
"""Deploy a clean vault and maintain job workspaces. Python 3.10+, stdlib only."""
import argparse
import datetime as dt
import json
import re
import shutil
import sys
import unicodedata
import uuid
from pathlib import Path

SKILL = Path(__file__).resolve().parents[1]
TEMPLATE = SKILL / 'assets' / 'vault'
TYPES = {'big':'大厂','foreign':'外企','soe':'国企','central':'央企','bank':'银行','public':'事业单位','civil':'公务员','private':'其他民企','firm':'事务所'}
DATA = 'Resource/投递记录数据.md'
PATTERN = re.compile(r'(<!-- JOB_APPLICATIONS_DATA_START -->\s*```json\s*)([\s\S]*?)(\s*```\s*<!-- JOB_APPLICATIONS_DATA_END -->)')

def safe_name(value):
    text = unicodedata.normalize('NFC', str(value))
    text = re.sub(r'[\x00-\x1f\x7f<>:"/\\|?*#\[\]^]', '-', text)
    return re.sub(r'\s+', ' ', text).strip(' .')[:60] or '未命名'

def inside(root, relative):
    path = root / relative
    if not path.resolve().is_relative_to(root.resolve()):
        raise ValueError(f'路径越界或符号链接指向仓库外：{relative}')
    return path

def create(path, text):
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists():
        if not path.is_file():
            raise ValueError(f'文件路径被目录占用：{path}')
        return False
    with path.open('x', encoding='utf-8') as f:
        f.write(text)
    return True

def dump(value):
    return json.dumps(value, ensure_ascii=False, indent=2) + '\n'

def atomic_write(path, text, expected):
    if path.read_text(encoding='utf-8') != expected:
        raise ValueError('文件已被其他窗口修改，停止写入；请重新读取后重试')
    tmp = path.with_name(path.name + '.pending-' + uuid.uuid4().hex)
    try:
        tmp.write_text(text, encoding='utf-8')
        tmp.replace(path)
    finally:
        tmp.unlink(missing_ok=True)

def initialize(root, year):
    root.mkdir(parents=True, exist_ok=True)
    made, kept = [], []
    for source in sorted(TEMPLATE.rglob('*')):
        if not source.is_file():
            continue
        rel = source.relative_to(TEMPLATE)
        dest = inside(root, rel)
        content = source.read_text(encoding='utf-8')
        # Only change the decorative campaign year. The public exam page is byte-preserved.
        if str(rel) in ('投递进度.md', '秋招关注.md'):
            content = content.replace('APPLICATION LEDGER  /  2026', f'APPLICATION LEDGER  /  {year}')
            content = content.replace('WATCHLIST  /  2026 AUTUMN', f'WATCHLIST  /  {year} AUTUMN')
        (made if create(dest, content) else kept).append(str(rel))
    for rel in ('已投递岗位','简历分解','Resource/Images','Resource/Resumes','Resource/Attachments','.obsidian'):
        inside(root, rel).mkdir(parents=True, exist_ok=True)
    # A real, independent vault config. Never copy personal plugin credentials or symlinks.
    create(inside(root, '.obsidian/app.json'), dump({'attachmentFolderPath':'Resource/Images'}))
    print(dump({'created':made, 'preserved':kept, 'next':'读取简历并完成深挖、简历分解；按使用说明启用 Dataview。'}))

def read_records(root):
    path = inside(root, DATA)
    original = path.read_text(encoding='utf-8')
    match = PATTERN.search(original)
    if not match:
        raise ValueError('投递记录数据标记丢失；不覆盖文件')
    records = json.loads(match[2])
    if not isinstance(records, list):
        raise ValueError('投递记录必须为数组')
    ids = set()
    for item in records:
        validate_record(item)
        if item['id'] in ids:
            raise ValueError('投递 id 重复')
        ids.add(item['id'])
    return path, original, records

def validate_record(record):
    if not isinstance(record,dict):
        raise ValueError('投递条目必须是对象')
    for key in ('id','company','position','date','type'):
        if not isinstance(record.get(key), str) or not record[key].strip():
            raise ValueError(f'投递记录缺少字符串字段：{key}')
    if not re.fullmatch(r'[A-Za-z0-9_-]+',record['id']):
        raise ValueError('投递 id 仅允许字母、数字、下划线和连字符')
    if record['type'] not in TYPES:
        raise ValueError('不支持的企业类型')
    if not re.fullmatch(r'\d{4}-\d{2}-\d{2}', record['date']):
        raise ValueError('投递日期必须为 YYYY-MM-DD')
    dt.date.fromisoformat(record['date'])
    if not isinstance(record.get('stages', []),list) or any(not isinstance(v,str) for v in record.get('stages', [])):
        raise ValueError('stages 必须是字符串数组')
    for key in ('offer','terminated'):
        if key in record and not isinstance(record[key],bool):
            raise ValueError(f'{key} 必须是布尔值')
    link = record.get('link', '')
    if not isinstance(link,str) or (link and not re.match(r'^https?://\S+$',link)):
        raise ValueError('岗位链接必须为空或 http/https URL')
    path = record.get('notePath')
    if path and not re.fullmatch(r'已投递岗位/[^/\\]+\.md', path):
        raise ValueError('notePath 必须指向已投递岗位下的直接子 Markdown 文件')

def save_records(path, original, records):
    updated = PATTERN.sub(lambda m: m[1]+dump(records).rstrip()+m[3], original, count=1)
    if updated != original:
        backup = path.with_name(path.stem + '-备份-' + dt.datetime.now().strftime('%Y%m%d-%H%M%S-%f') + '.md')
        shutil.copyfile(path, backup)
        atomic_write(path, updated, original)

def job_workspace(root, record):
    validate_record(record)
    folder = inside(root,'已投递岗位')
    folder.mkdir(parents=True,exist_ok=True)
    note_path = record.get('notePath')
    if not note_path:
        id_line = 'application_id: '+json.dumps(record['id'], ensure_ascii=False)
        for child in sorted(folder.glob('*.md')):
            if id_line in child.read_text(encoding='utf-8').splitlines():
                note_path = child.relative_to(root).as_posix()
                break
    used = [int(m[1]) for child in folder.iterdir() if (m:=re.match(r'^(\d+)-',child.name))]
    seq = f'{max(used,default=0)+1:02d}'
    if note_path:
        match = re.match(r'^(\d+)-',Path(note_path).name)
        if match:
            seq = match[1]
    else:
        note_path = f'已投递岗位/{seq}-{safe_name(record["company"])} {safe_name(record["position"])}.md'
    material_path = note_path[:-3]
    q = lambda value: json.dumps(str(value),ensure_ascii=False)
    title = record['company']+' '+record['position']
    fields = {'title':title,'application_id':record['id'],'company':record['company'],'position':record['position'],'date':record['date'],'type':TYPES[record['type']],'link':record.get('link',''),'offer':str(record.get('offer',False)).lower(),'seq':seq,'materials':material_path}
    frontmatter = '\n'.join(k+': '+q(v) for k,v in fields.items())
    link = f'\n> [!link] 岗位链接\n> [点击跳转]({record["link"]})\n' if record.get('link') else ''
    body = f'''---
{frontmatter}
tags:
  - 求职
  - 已投递
---

# {title}

> [!info] {record['position']}
> **企业**：{record['company']} ｜ **类型**：{TYPES[record['type']]}
> **投递日期**：{record['date']} ｜ **编号**：{seq}
{link}
## 岗位职责

## 任职要求

## 投递进度

## 📚 关联准备资料

| 资料 | 重点映射 JD 维度 | 关键覆盖点 | 资料价值 |
| --- | --- | --- | --- |

## 岗位资料目录

[[{material_path}/00-资料索引|打开本岗位资料索引]]
'''
    existing = inside(root,note_path)
    if existing.is_file():
        owner = re.search(r'^application_id: (.+)$',existing.read_text(encoding='utf-8'),re.M)
        if owner and json.loads(owner[1]) != record['id']:
            raise ValueError('该笔记已属于其他投递 id')
    create(existing,body)
    inside(root,material_path).mkdir(parents=True,exist_ok=True)
    create(inside(root,material_path+'/00-资料索引.md'),f'# {title} · 资料索引\n\n> [!info] 服务岗位\n> [[{note_path[:-3]}|{title}]]\n\n本文件夹用于存放该岗位的前期调研、JD 分析、面试语料与复盘。\n\n## 资料清单\n\n在此追加资料链接；图片统一保存在 Resource/Images/。\n')
    record.update(notePath=note_path,folderPath=material_path)
    return note_path

def decompose(root, profile_file):
    profile = json.loads(profile_file.read_text(encoding='utf-8'))
    modules = profile.get('modules',[])
    if not modules:
        raise ValueError('profile.modules 不能为空，必须来自用户的真实简历')
    folder = inside(root,'简历分解'); folder.mkdir(parents=True,exist_ok=True)
    manifest_path = inside(root,'Resource/简历分解映射.json')
    manifest = json.loads(manifest_path.read_text()) if manifest_path.exists() else {}
    for module in modules:
        for field in ('id','title','category','source','excerpt'):
            if not isinstance(module.get(field),str) or not module[field].strip():
                raise ValueError(f'每个模块必须包含非空 {field}')
    if len({m['id'] for m in modules}) != len(modules):
        raise ValueError('模块 id 必须唯一')
    for module in modules:
        key = module['id']
        if key not in manifest:
            used = [int(m[1]) for child in folder.iterdir() if (m:=re.match(r'^(\d+)-',child.name))]
            name = f'{max(used,default=0)+1:02d}-{safe_name(module["title"])}'
            manifest[key] = '简历分解/'+name
        rel = manifest[key]
        dest = inside(root,rel); dest.mkdir(parents=True,exist_ok=True)
        excerpt = '\n'.join('> '+line for line in module['excerpt'].splitlines())
        create(dest/'00-经历概览.md',f'''# {module['title']}

> [!info] 简历来源
> [[00-我的简历]] · {module['source']}
> 类别：{module['category']}

## 简历原文

{excerpt}

## 深挖分析

[[00-我的简历-深挖分析]]

## 待补充证据

{module.get('evidence_needed','根据深挖报告，补充职责边界、方法、成果口径和可公开的佐证。')}

## 语料索引

在本文件夹追加专题笔记，并在此登记链接。
''')
    if manifest_path.exists():
        original=manifest_path.read_text(encoding='utf-8')
        atomic_write(manifest_path,dump(manifest),original)
    else:
        create(manifest_path,dump(manifest))
    index = '# 简历分解索引\n\n[[00-我的简历]] · [[00-我的简历-深挖分析]]\n\n'
    index += '\n'.join(f'- [[{rel}/00-经历概览|{Path(rel).name}]]' for rel in manifest.values())+'\n'
    index_path=folder/'00-索引.md'
    if index_path.exists():
        # Preserve user additions; only append links for newly discovered modules.
        original=index_path.read_text(encoding='utf-8')
        additions=[line for line in index.splitlines() if line.startswith('- [[') and line not in original]
        if additions: atomic_write(index_path,original+'\n'+'\n'.join(additions)+'\n',original)
    else: create(index_path,index)
    print(dump(manifest))

def check(root, complete=False):
    problems=[]
    for rel in ('投递进度.md','秋招关注.md','公考时间.md','CLAUDE.md','AGENTS.md','Resource/投递记录数据.md','Resource/秋招关注数据.md','已投递岗位/00-从夯到拉.md','Resource/岗位评级数据.md'):
        if not inside(root,rel).is_file(): problems.append('缺少 '+rel)
    if not problems:
        _,_,records=read_records(root)
        for record in records:
            for key in ('notePath','folderPath'):
                if not record.get(key) or not inside(root,record[key]).exists(): problems.append(f'{record["id"]} 缺少 {key}')
            if record.get('folderPath') != record.get('notePath','')[:-3]: problems.append('岗位笔记与文件夹不同名')
        watch=inside(root,'Resource/秋招关注数据.md').read_text()
        match=re.search(r'<!-- WATCH_POSITIONS_DATA_START -->\s*```json\s*([\s\S]*?)\s*```\s*<!-- WATCH_POSITIONS_DATA_END -->',watch)
        if not match or not isinstance(json.loads(match[1]),list): problems.append('关注数据格式错误')
    rank_path = inside(root,'Resource/岗位评级数据.md')
    if rank_path.is_file():
        match = re.search(r'<!-- JOB_RANKS_DATA_START -->\s*```json\s*([\s\S]*?)\s*```\s*<!-- JOB_RANKS_DATA_END -->',rank_path.read_text())
        try:
            ranks = json.loads(match[1]) if match else None
            if not isinstance(ranks,dict) or any(not isinstance(ranks.get(k),list) or any(not isinstance(v,str) for v in ranks[k]) for k in ('夯','顶级','人上人','NPC','拉完了')):
                problems.append('岗位评级数据格式错误')
        except (ValueError,TypeError):
            problems.append('岗位评级数据格式错误')
    if complete:
        for rel in ('00-我的简历.md','00-我的简历-深挖分析.md','简历分解/00-索引.md','Resource/简历分解映射.json'):
            if not inside(root,rel).is_file() or inside(root,rel).stat().st_size < 10: problems.append('尚未完成 '+rel)
    print(dump({'ok':not problems,'problems':problems,'note':'结构检查不替代 Agent 对深挖内容和 Obsidian 实际渲染的检查。'}))
    return not problems

def main():
    parser=argparse.ArgumentParser(description=__doc__)
    sub=parser.add_subparsers(dest='command',required=True)
    p=sub.add_parser('init');p.add_argument('--vault',required=True,type=Path);p.add_argument('--year',type=int,default=dt.date.today().year)
    p=sub.add_parser('decompose');p.add_argument('--vault',required=True,type=Path);p.add_argument('--profile',required=True,type=Path)
    p=sub.add_parser('sync-jobs');p.add_argument('--vault',required=True,type=Path)
    p=sub.add_parser('add-job');p.add_argument('--vault',required=True,type=Path);p.add_argument('--record',required=True,type=Path)
    p=sub.add_parser('check');p.add_argument('--vault',required=True,type=Path);p.add_argument('--complete',action='store_true')
    args=parser.parse_args();root=args.vault.expanduser().resolve()
    if args.command=='init': initialize(root,args.year)
    elif args.command=='decompose': decompose(root,args.profile)
    elif args.command=='check': return 0 if check(root,args.complete) else 1
    else:
        path,original,records=read_records(root)
        if args.command=='add-job':
            record=json.loads(args.record.read_text(encoding='utf-8'))
            record.setdefault('id',str(uuid.uuid4()));record.setdefault('stages',[]);record.setdefault('offer',False);record.setdefault('terminated',False);record.setdefault('link','')
            validate_record(record)
            prior=next((r for r in records if r['id']==record['id']),None)
            if prior:
                if any(prior[k]!=record[k] for k in ('company','position','date','type')): raise ValueError('该 id 已属于其他岗位')
                record=prior
            else: records.append(record)
            job_workspace(root,record)
        else:
            for record in records: job_workspace(root,record)
        save_records(path,original,records)
        print(dump({'records':len(records),'paths':[r.get('notePath') for r in records]}))
    return 0

if __name__=='__main__':
    try: sys.exit(main())
    except (ValueError,OSError,KeyError,TypeError) as exc:
        print(f'错误：{exc}',file=sys.stderr);sys.exit(1)
