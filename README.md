# Biorxiv- 每日文献推送 / Daily Literature Push

科学问题跟进，文献学习及分享。

[![BioRxiv 每日推送](https://github.com/LML1qa2ws/Biorxiv-/actions/workflows/daily_push.yml/badge.svg)](https://github.com/LML1qa2ws/Biorxiv-/actions/workflows/daily_push.yml)

## 简介 / Overview

本项目通过 GitHub Actions 每天自动抓取 [BioRxiv](https://www.biorxiv.org/) 和 [MedRxiv](https://www.medrxiv.org/) 最新预印本文献，按关键词过滤后生成中英文日报，并与 [OpenClaw](https://openclaw.ai/) 联动完成多渠道推送。

This project uses GitHub Actions to automatically fetch the latest preprints from BioRxiv and MedRxiv daily, filters them by keywords, generates a bilingual daily report, and integrates with [OpenClaw](https://openclaw.ai/) for multi-channel push notifications.

## 功能特性 / Features

- 📅 **每日定时抓取**：北京时间 08:30 自动运行 / Daily scheduled fetch at Beijing 08:30
- 🔍 **关键词过滤**：支持 AND/OR 逻辑 / Keyword filtering with AND/OR logic
- 📝 **自动生成日报**：结构化 Markdown 文档存储于 `reports/` / Structured Markdown reports in `reports/`
- 🤖 **OpenClaw 联动**：通过 OpenClaw 推送到 Telegram、Slack、邮件等渠道 / OpenClaw push to Telegram, Slack, Email, etc.
- 🔧 **灵活配置**：通过 `config.yaml` 自定义关键词、来源、输出格式 / Flexible configuration via `config.yaml`

## 快速开始 / Quick Start

### 1. 配置关键词 / Configure Keywords

编辑 `config.yaml`，自定义搜索关键词：

```yaml
search_queries:
  - "machine learning AND genomics"
  - "single-cell sequencing"
  - "CRISPR"
```

### 2. 配置 OpenClaw 推送 / Configure OpenClaw Push

在 GitHub 仓库的 **Settings → Secrets and variables → Actions** 中添加以下 Secrets：

| Secret 名称 | 说明 |
|-------------|------|
| `OPENCLAW_API_URL` | OpenClaw API 地址 / OpenClaw API base URL |
| `OPENCLAW_API_KEY` | OpenClaw API 密钥 / OpenClaw API key |

### 3. 手动触发 / Manual Trigger

在 GitHub Actions 页面点击 **Run workflow**，可选填日期参数（格式 `YYYY-MM-DD`）。

### 4. 本地运行 / Run Locally

```bash
pip install -r requirements.txt
python scripts/fetch_biorxiv.py --config config.yaml
# 或指定日期 / Or specify a date:
python scripts/fetch_biorxiv.py --config config.yaml --date 2026-04-02
```

## 目录结构 / Project Structure

```
Biorxiv-/
├── .github/
│   └── workflows/
│       └── daily_push.yml     # GitHub Actions 工作流 / Workflow
├── openclaw/
│   └── skill.yaml             # OpenClaw skill 配置 / Skill config
├── reports/                   # 自动生成的日报 / Auto-generated reports
├── scripts/
│   └── fetch_biorxiv.py       # 文献抓取脚本 / Paper fetching script
├── config.yaml                # 配置文件 / Configuration
└── requirements.txt           # Python 依赖 / Dependencies
```

## 日报示例 / Report Example

日报保存于 `reports/YYYY-MM-DD.md`，包含：

- 匹配关键词列表
- 文章标题、作者、DOI 链接
- 摘要（截取前 300 字）

## 许可证 / License

MIT
