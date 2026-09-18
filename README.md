# Yan's job vault

一个面向 Claude Code、Codex 和 Obsidian Claudian 的秋招求职仓库部署 Skill。

它可以从用户自己的 PDF、Word 或 Markdown 简历出发，创建一个本地 Obsidian 求职仓库，并生成简历深挖、经历拆分、投递管理、岗位资料目录和“从夯到拉”岗位评级板。

> 项目创作者：**aheart Yan**  
> 联系邮箱：**953800971@qq.com**  
> Skill 标识：`yans-job-vault`

## 主要功能

- 从用户真实简历建立 `00-我的简历.md` 和完整深挖报告。
- 按教育、实习、工作、项目和实践经历生成独立资料目录。
- 使用 Obsidian DataviewJS 管理投递进度和秋招关注列表。
- 新增投递后自动建立岗位笔记及同名准备资料文件夹。
- 用“夯 / 顶级 / 人上人 / NPC / 拉完了”五档拖拽评价已投岗位。
- 在仓库内保存投递、关注和评级数据，便于备份与同步。
- 同时提供 Claude Code、Claudian 和 Codex 项目规则。

仓库模板不包含创作者的个人简历、投递记录或岗位评级。用户数据只会写入用户自己选择的本地目标目录。

## 让 Agent 从 GitHub 安装

把本仓库链接发送给 Claude Code 或 Codex，并使用类似提示：

```text
请安装并使用这个 GitHub 仓库中的 yans-job-vault Skill：
https://github.com/sickenera-code/yans-job-vault

读取完整 SKILL.md 和所引用的资源，把整个仓库安装到当前 Agent 的用户级 Skill 目录。不要只复制 SKILL.md。安装完成后，使用它和我提供的简历，在我指定的目录创建 Obsidian 秋招求职仓库。
```

Agent 应当根据自己的运行环境选择技能目录。常见目录包括：

| 环境 | 用户级 Skill 目录 |
| --- | --- |
| Claude Code / Claudian 的 Claude 模式 | `~/.claude/skills/yans-job-vault/` |
| Codex | `~/.agents/skills/yans-job-vault/` 或当前环境配置的 Codex Skill 目录 |

不同版本的 Agent 可能使用不同目录，因此应让 Agent先检查本机配置。复制时必须保留 `assets/`、`scripts/`、`references/`、`agents/` 和 `SKILL.md`。

## 使用 Git 安装

Claude Code：

```bash
git clone https://github.com/sickenera-code/yans-job-vault.git ~/.claude/skills/yans-job-vault
```

Codex：

```bash
git clone https://github.com/sickenera-code/yans-job-vault.git ~/.agents/skills/yans-job-vault
```

如果目标目录已经存在，不要再次克隆覆盖。先备份用户修改，再使用 `git pull` 更新。

安装后可以这样调用：

```text
使用 $yans-job-vault，读取我提供的简历，在“我的秋招”目录中部署一个完整的 Obsidian 求职仓库。
```

## 不安装也可以使用

克隆仓库后，可以直接告诉 Agent：

```text
读取 /实际路径/yans-job-vault/SKILL.md，按照其中的流程使用我的简历部署求职仓库。
```

如果只需要创建空白仓库结构，可运行：

```bash
python3 scripts/vault.py init --vault "/目标路径/我的秋招" --year 2027
```

初始化脚本使用 Python 标准库。完整简历分析仍需由 Claude Code 或 Codex 根据 `SKILL.md` 完成。

## Obsidian 运行要求

部署完成后，在 Obsidian 中打开生成的目录，并安装、启用 Dataview；在 Dataview 设置中开启 JavaScript Queries。若要在 Obsidian 内直接调用 Agent，可以另外安装 Claudian，并配置自己使用的 Claude Code 或 Codex 环境。

本仓库不会捆绑 Obsidian 插件、AI 账户、API 密钥或个人配置。

## 项目结构

```text
yans-job-vault/
├── SKILL.md
├── NOTICE.md
├── LICENSE
├── agents/
├── assets/vault/
├── references/
├── scripts/
└── tests/
```

- `SKILL.md`：Agent 的主入口。
- `assets/vault/`：将被部署到用户仓库的干净模板。
- `scripts/`：初始化、岗位同步、简历文本提取和结构检查。
- `references/`：仓库契约、简历深挖方法、输入处理和来源说明。
- `tests/`：在临时目录验证部署和数据保存行为，不接触用户真实仓库。

## 本地验证

```bash
python3 tests/test_vault.py
node tests/test_pages.cjs
node tests/test_ranking.cjs
```

技能格式还可以使用 Codex 的 `skill-creator` 验证器检查。测试通过不等于所有 Obsidian 主题和插件版本都已完成界面验证。

## 版权与来源

Copyright © 2026 aheart Yan.

本项目采用 [MIT License](LICENSE)。他人可以使用、修改和传播，但副本或重要部分中必须保留版权声明和许可声明。

项目整合方法和模板的来源范围记录在 [references/provenance.md](references/provenance.md)。该署名只适用于本项目的仓库设计、页面模板、脚本与技能整合，不将用户的简历、经历或个人笔记归为项目创作者作品。
