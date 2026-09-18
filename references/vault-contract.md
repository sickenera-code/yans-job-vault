# 仓库契约与脚本输入

## 必需产物

```text
目标仓库/
├── CLAUDE.md
├── AGENTS.md
├── .claude/CLAUDE.md
├── .obsidian/app.json
├── 使用说明.md
├── 00-我的简历.md                     Agent 读取用户原件后生成
├── 00-我的简历-深挖分析.md            Agent 完成分析后生成
├── 投递进度.md                       保留原页面布局与交互
├── 秋招关注.md                       保留原页面布局与交互
├── 公考时间.md                       原样复制，不替换年份
├── Resource/
│   ├── 投递记录数据.md               JSON 初始 []
│   ├── 秋招关注数据.md               JSON 初始 []
│   ├── 岗位评级数据.md               五档路径数组，初始为空
│   ├── 简历结构.json                 Agent 从简历提取的模块清单
│   ├── 简历分解映射.json             脚本维护稳定模块 id → 文件夹
│   ├── Resumes/                      语义化原始简历
│   ├── Images/                       语义化媒体资源
│   └── Attachments/                  其他原件
├── 简历分解/
│   ├── 00-索引.md
│   └── NN-实际经历名称/00-经历概览.md
└── 已投递岗位/
    ├── 00-从夯到拉.md                 五档拖拽评级板
    ├── NN-公司 岗位.md
    └── NN-公司 岗位/00-资料索引.md
```

空文件夹由脚本创建，因此不依赖版本控制保留空目录。`语料库/`、`Clippings/` 等只有用户需要时再创建，不捆绑插件数据。

## 页面与数据

两个原页面为 `dataviewjs` 代码块。保留 CSS、DOM 排版与筛选/增删/导入导出交互。投递页功能层增加同名文件夹、路径清洗、唯一 id、加载/导入补齐与失败重试，并移除跨仓库 localStorage 迁移。原始页面年份 2026 的装饰标题在初始化时按 `--year` 替换；公考页不变。

数据必须写在固定标记内：

| 文件 | 起始标记 | 结束标记 |
| --- | --- | --- |
| Resource/投递记录数据.md | `<!-- JOB_APPLICATIONS_DATA_START -->` | `<!-- JOB_APPLICATIONS_DATA_END -->` |
| Resource/秋招关注数据.md | `<!-- WATCH_POSITIONS_DATA_START -->` | `<!-- WATCH_POSITIONS_DATA_END -->` |

标记之间为一个 `json` 代码块，内容为数组。不要把数据写回页面源码或 localStorage。

### 投递记录

```json
{
  "id": "稳定唯一字符串",
  "company": "实际企业名称",
  "type": "private",
  "position": "实际岗位名称",
  "date": "2026-09-14",
  "link": "",
  "stages": [],
  "terminated": false,
  "offer": false
}
```

示例仅说明字段，不能写进空白模板。`id` 使用 UUID 或仅包含字母/数字/下划线/连字符的稳定标识。日期使用用户真实投递日期；不要从当前日期捏造已经发生的投递。`link` 为空或 HTTP(S) 地址。企业类型：`big` 大厂、`foreign` 外企、`soe` 国企、`central` 央企、`bank` 银行、`public` 事业单位、`civil` 公务员、`private` 其他民企、`firm` 事务所。

脚本 / 页面维护 `notePath` 与 `folderPath`。已有记录 id 重试不新增；相同公司不同岗位或不同批次可独立记录。删除列表条目保留笔记与资料，避免丢失准备成果。删除后重新投递产生新 id 与新编号。

`add-job` 用于新增或同 id 重试，不负责修改所有旧字段。更新阶段/链接/Offer 优先用页面；Agent 修改时备份数据并同步岗位笔记的相关状态，不能重写用户整理的 JD 和正文。

### 关注记录

字段：`id`、`company`、`type`、`expectedDate`（`YYYY-MM` 或空）、`url`、`status`（`watching` / `opened`）、`note`、`stages`（数组），可有 `openedDate`。未知字段保留。关注不会被当作已投递；用户明确已经投递后才新增投递记录。

### 命名与失败恢复

文件 stem 与同名资料文件夹严格相同。公司、岗位各截取前 60 字符；换行/连续空白规整为空格，`<>:"/\|?*#[]^` 和控制字符替换为 `-`，去掉首尾空格与点。序号扫描 `已投递岗位/` 的笔记和文件夹，取最大编号 + 1，至少两位。

路径一旦写入数据则为关联依据，不能每次重新按公司名称推算。没有路径但有 `application_id` 的笔记会被重试流程认领。创建已存在的同名目录不会清空它；已有岗位笔记也不覆盖。`00-资料索引.md` 含回链，关联资料表格位于岗位页，最后一列“资料价值”留给用户。

Agent 脚本数据写入前生成时间标记备份，并做内容变化检查。它与 Obsidian 页面之间没有跨进程事务锁，因此操作时只使用一个写入入口；不要同时开两个 Agent 写同一数据文件。页面局部目录失败会保留记录，下次加载再补齐。存在权限或路径占用错误时先解决该问题，再执行 `sync-jobs`；不能通过删掉原笔记来重试。

## 简历结构 JSON

```json
{
  "modules": [
    {
      "id": "experience-01",
      "title": "企业简称-实习岗位",
      "category": "实习经历",
      "source": "实习经历 / 对应企业 / 第1条",
      "excerpt": "用户简历中的完整原文",
      "evidence_needed": "基于该经历实际缺口写出的待补充证据"
    }
  ]
}
```

按简历真实顺序或准备顺序生成模块，id 不因目录重排改变。学校/教育、每段独立实习、工作、项目、实践、竞赛和重要技能主题分别判断；同一经历的多条 bullet 放在同一个模块的 excerpt，不机械地每句建一个文件夹。无简历就不填示例占位经历。`decompose` 默认保留已有概览正文；更新经历内容需 Agent 比较原文后定向合并。

## 验收命令

```bash
python3 "<技能目录>/scripts/vault.py" check --vault "<目标仓库>" --complete
python3 "<技能目录>/tests/test_vault.py"
node "<技能目录>/tests/test_pages.cjs"
node "<技能目录>/tests/test_ranking.cjs"
```

测试使用临时目录与 Obsidian Vault API 模拟，检查持久化和目录联动，不代表真实插件 UI 已测试。技能制作阶段不在用户真实记录里插入测试数据。

## 评级数据

`Resource/岗位评级数据.md` 的 `JOB_RANKS_DATA_START` / `JOB_RANKS_DATA_END` HTML 注释标记之间为 JSON 对象，键为 `夯`、`顶级`、`人上人`、`NPC`、`拉完了`，值为岗位笔记路径数组。初始化均为空；不迁移 localStorage，避免携带提供者的旧评级。页面保留原样式与卡片交互，空仓库展示空看板。笔记改名需要同步评级路径；删除投递记录但保留笔记时仍参与评级。新增卡片来自 Dataview 岗位笔记索引，保存用 Vault.process 检查冲突，失败恢复操作前的状态。
