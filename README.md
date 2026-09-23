# Weight Management · 个人健康记录

一个本地优先的个人健康记录应用：用体重趋势保留结构化指标，用每日随笔记录饮食、睡眠、情绪、运动和身体感受，并让 AI 通过受限的只读工具按需分析记录。

[![Python](https://img.shields.io/badge/Python-3.10%2B-3776AB?logo=python&logoColor=white)](https://www.python.org/)
[![Gradio](https://img.shields.io/badge/UI-Gradio-F97316)](https://www.gradio.app/)
[![SQLite](https://img.shields.io/badge/Storage-SQLite-003B57?logo=sqlite&logoColor=white)](https://sqlite.org/)

## 亮点

- 最近七天、最近三十天、最近九十天体重趋势，支持直接调整开始和结束日期。
- 点击趋势图上的体重点即可载入对应日期，编辑体重和健康随笔。
- AI 只能调用 `search_health_journals`、`get_weight_records`、`get_daily_health_record`、`get_summary` 四个只读工具。
- 数据默认保存在本机 SQLite，不上传健康记录；AI 结论是记录相关性观察，不是医疗诊断。
- AI 输入支持 Enter 发送、Alt+Enter 换行。

## 快速开始

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
export LLM_BASE_URL='https://api.openai.com/v1'
export LLM_API_KEY='从安全位置读取，不要写入仓库'
export LLM_MODEL='gpt-4o-mini'
python app.py
```

打开 `http://127.0.0.1:7862`。数据保存在 `data/health.sqlite3`，默认只监听本机。

点击趋势图上的体重点会切换到对应日期，并加载当天体重和日志；可直接修改后点击「保存记录」。记录日期和趋势范围均支持日历选择。未保存的修改应先保存再切换日期。

右侧显示 AI 模型与密钥配置状态。提问时，相关记录会通过查询工具发送给配置的 AI 服务；密钥不会传给网页。

AI 只能通过应用内的 `search_health_journals`、`get_weight_records`、`get_daily_health_record`、`get_summary` 四个只读工具查询本项目数据，不能访问项目外文件或修改记录。

## 后台运行与开机启动

临时后台运行：

```bash
./start.sh
./status.sh
./stop.sh
```

开机自动启动（用户级 systemd）：

```bash
mkdir -p ~/.config
mkdir -p ~/.config/systemd/user
cat > ~/.config/weight-management.env <<'EOF'
LLM_BASE_URL=https://api.openai.com/v1
LLM_API_KEY=请填入你的密钥
LLM_MODEL=gpt-4o-mini
EOF
cp weight-management.service ~/.config/systemd/user/weight-management.service
systemctl --user daemon-reload
systemctl --user enable --now weight-management.service
```

密钥只放在 `~/.config/weight-management.env`，不要提交到仓库。查看日志：`journalctl --user -u weight-management.service -f`。

界面采用紧凑双栏布局，趋势默认近七天；开始和结束日期直接显示在范围选择器右侧，可自行调整。随笔通过点击图表上的体重点查看。AI 输入框 Enter 发送，Alt+Enter 换行，中文输入法选词不会触发发送。

## 项目结构

`app.py` 负责 Gradio 页面和交互，`database.py` 负责本地 SQLite，`chart.py` 负责趋势图，`tools.py` 提供 AI 只读查询工具，`llm_client.py` 负责工具调用对话循环。

## 隐私与边界

健康记录和 API 密钥不会提交到仓库。应用不提供医疗诊断，也不把完整历史记录固定塞进提示词；AI 只在问题需要时查询相关数据。
