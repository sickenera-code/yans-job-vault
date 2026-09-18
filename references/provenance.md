# Yan's job vault · 来源与保留范围

来源检查日期：2026-09-14。

项目创作者：aheart Yan · 953800971@qq.com。项目名称与署名更新于 2026-09-18；项目创作和整合署名不改变下列已有方法的来源说明。

## 页面

三个交互页面来源于用户提供的秋招 Obsidian 仓库。`投递进度.md` 和 `秋招关注.md` 保留视觉与页面结构，仅调整部署所需的数据/目录逻辑；两个 Resource 数据文件的 JSON 数组清空为 `[]`。用户的简历、深挖成稿、岗位记录、经历目录、准备语料及插件状态没有包含在 skill 中。

`公考时间.md` 原样复制，SHA-256 与源文件一致。原始五个文件的摘要记录于 [source-manifest.json](source-manifest.json)，用于确认本次制作没有改动源文件；不包含源文件内容。

## resume-deep-dive

检查本地提供版本的 `SKILL.md`、`README.md`、`references/output-templates.md`、`references/output-examples.md` 与目录清单，未发现作者、版权声明或独立 LICENSE 文件。没有推断作者身份或凭空添加署名，也不将“未标注”表述成公共领域授权。

按用户要求把全景诊断、五维深挖、三层追问、STAR、自评与分阶段学习路线整合进本 skill。参考流程和模板重新整理为独立文件，无需访问原作者机器上的路径。保留方法，调整了批次询问逻辑以支持一次性完整仓库交付，补充事实边界，未复制示例人物或原仓库候选人的分析。

如果后续得到明确作者或许可信息，应更新此说明，并按真实署名要求在生成的深挖报告中标注；不虚构“原创作者”。

## 运行依据

- [Dataview JavaScript API](https://blacksmithgu.github.io/obsidian-dataview/api/intro/)：页面运行环境。
- [Claudian 官方项目](https://github.com/YishenTu/claudian)：Obsidian 中的 Agent 集成与安装说明。
- [Obsidian Vault.createFolder](https://docs.obsidian.md/Reference/TypeScript+API/Vault/createFolder)：创建资料目录的 API。

不捆绑第三方插件二进制、字体文件、用户凭据或聊天历史。

## 补充：从夯到拉评级板

原仓库的 `已投递岗位/00-从夯到拉.md` 已补入模板。保留 CSS 和渲染组件，将 localStorage 持久化替换为仓库内 Markdown 数据文件，并显示空仓库状态。没有导入个人评级；原仓库页面不修改。
