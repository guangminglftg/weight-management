import os
from datetime import date

for proxy_name in ("HTTP_PROXY", "HTTPS_PROXY", "ALL_PROXY", "http_proxy", "https_proxy", "all_proxy"):
    if os.environ.get(proxy_name, "").lower().startswith("socks://"):
        os.environ.pop(proxy_name)

import gradio as gr

from chart import build_clickable_chart
from config import get_settings
from database import HealthRepository
from llm_client import HealthAssistant
from ui import default_dates, journal_cards, load_form_values, parse_weight, summary_text


settings = get_settings()
repository = HealthRepository(settings.database_path)

CSS = """
.gradio-container { max-width:1520px !important; width:100% !important; margin:auto; padding:16px 20px !important; background:#f5f5f7 !important; font-family:-apple-system,BlinkMacSystemFont,"SF Pro Text","Helvetica Neue","Noto Sans",sans-serif !important; --body-text-color:#1d1d1f; --body-text-color-subdued:#6e6e73; --input-background-fill:#f5f5f7; --input-border-color:#e5e5ea; --block-border-color:#e5e5ea; --block-radius:14px; }
.main { max-width:none !important; width:100% !important; padding:0 !important; }
footer { display:none !important; }
body { background:#f5f5f7 !important; }
#dashboard { gap:20px; align-items:stretch; }
#panel, #chat-panel { border:1px solid #e8e8ed; border-radius:24px; background:#fff; padding:20px; gap:10px; flex-wrap:nowrap; height:calc(100dvh - 80px); min-height:620px; box-shadow:0 8px 30px #1d1d1f05; }
#panel { overflow:visible; }
#chat-panel { min-width:360px; }
#title h1 { color:#1d1d1f; font-size:26px; font-weight:650; letter-spacing:-.7px; margin:0; }
#title p, #notice p, #chart-hint p, #model-info p { color:#86868b; font-size:12px; line-height:1.5; margin:4px 0 0; }
#panel h2, #chat-panel h2 { color:#1d1d1f; font-size:20px; font-weight:600; letter-spacing:-.4px; margin:0; }
#record-fields { align-items:flex-end; gap:12px; }
#save, #ask { background:#007aff !important; border:0 !important; color:white !important; font-size:14px !important; font-weight:500 !important; border-radius:12px; box-shadow:none !important; white-space:nowrap; transition:background .15s; }
#save { min-width:112px !important; width:112px; flex:none !important; height:44px; margin-bottom:1px; padding:0 16px; }
#save:hover, #ask:hover { background:#0066d6 !important; }
#ask { min-height:44px; }
#trend-header { align-items:center; flex-wrap:nowrap; gap:10px; padding-top:12px; border-top:1px solid #f0f0f3; }
#trend-title { flex:1; min-width:90px; }
#trend-title h2 { white-space:nowrap; }
#trend-header > .form { min-width:126px !important; width:126px; flex:none !important; background:transparent; border:0; }
#trend-range { padding:0; min-width:126px !important; width:126px; border-radius:12px; }
.trend-date { min-width:150px !important; width:150px; flex:none !important; gap:0; }
.trend-date .block { padding:0 !important; border:0 !important; }
.trend-date input { font-size:13px !important; }
#chart { border:0; border-radius:16px; background:#fafafa; padding:12px; flex:1; min-height:180px; }
.chart-shell { height:100%; display:flex; flex-direction:column; justify-content:center; }
.chart-shell svg { width:100%; height:clamp(170px,26vh,300px); }
.chart-labels { display:flex; justify-content:space-between; color:#86868b; font-size:12px; padding:0 8px; }
.empty-chart { padding:40px 12px; color:#86868b; text-align:center; }
#summary p { color:#6e6e73; font-size:12px; text-align:center; }
#chatbot { flex:1; min-height:180px; height:0 !important; background:#fafafa; border:1px solid #f0f0f3; border-radius:16px; }
#question { border-radius:14px; }
@media (max-width: 800px) {
  .gradio-container { padding:10px !important; }
  #dashboard { flex-direction:column; gap:14px; }
  #panel, #chat-panel { height:auto; min-height:0; padding:18px; border-radius:20px; }
  #chat-panel { min-width:0; }
  #chatbot { flex:auto; height:360px !important; min-height:260px; }
  #trend-header { gap:8px; flex-wrap:wrap; }
  #trend-title { flex:1; }
  .trend-date { flex:1 !important; min-width:140px !important; width:auto; }
  #trend-title h2 { font-size:18px; }

}
"""

CHAT_KEYS = r"""
() => {
    if (window.healthChatKeysInstalled) return;
    window.healthChatKeysInstalled = true;
    document.addEventListener('keydown', (event) => {
        const input = event.target;
        if (!input.matches('#question textarea') || event.key !== 'Enter') return;
        if (event.isComposing || event.keyCode === 229) return;
        event.preventDefault();
        event.stopImmediatePropagation();
        if (event.altKey) {
            input.setRangeText('\n', input.selectionStart, input.selectionEnd, 'end');
            input.dispatchEvent(new Event('input', {bubbles:true}));
        } else if (!event.repeat && input.value.trim()) {
            document.querySelector('#ask')?.click();
        }
    }, true);
}
"""


def assistant_or_error():
    if not settings.llm_api_key:
        return None, "未配置 LLM_API_KEY；本地记录和图表仍可正常使用。"
    try:
        from openai import OpenAI
    except ImportError:
        return None, "尚未安装 openai 依赖；请执行 pip install -r requirements.txt。"
    import httpx
    client = OpenAI(api_key=settings.llm_api_key, base_url=settings.llm_base_url,
                    http_client=httpx.Client(trust_env=False), timeout=60, max_retries=1)
    return HealthAssistant(repository, client, settings.llm_model), ""


def range_values(start_date, end_date):
    start_date, end_date = normalize_date(start_date), normalize_date(end_date)
    records = repository.daily_records(start_date or None, end_date or None)
    chart = build_clickable_chart(records)
    return chart, summary_text(repository.summary(start_date or None, end_date or None)), journal_cards(records)


def save_record(record_date, weight, journal, start_date, end_date):
    try:
        record_date = normalize_date(record_date)
        parsed_weight = parse_weight(weight)
        if parsed_weight is not None:
            repository.save_weight(record_date, parsed_weight)
        repository.save_journal(record_date, journal or "")
        chart, summary, journals = range_values(start_date, end_date)
        return "已保存", chart, summary, journals
    except (ValueError, TypeError) as error:
        return f"保存失败：{error}", gr.update(), gr.update(), gr.update()


def load_record(record_date):
    try:
        record_date = normalize_date(record_date)
        weight, journal = load_form_values(repository, record_date)
        return weight, journal
    except ValueError:
        return gr.update(value=None), gr.update(value="")


def normalize_date(value):
    return date.fromisoformat(str(value)[:10]).isoformat()


def select_chart_point(event: gr.SelectData):
    try:
        selected_date = normalize_date(event.value)
    except (TypeError, ValueError):
        return gr.update(), gr.update(), gr.update()
    weight, journal = load_form_values(repository, selected_date)
    return selected_date, weight, journal


def ask_ai(message, history):
    if not message or not message.strip():
        return history, ""
    assistant, error = assistant_or_error()
    if error:
        return history + [
            {"role": "user", "content": message.strip()},
            {"role": "assistant", "content": error},
        ], ""
    messages = []
    for item in history or []:
        if isinstance(item, dict) and item.get("role") in {"user", "assistant"}:
            content = item.get("content", "")
            if isinstance(content, list):
                content = "\n".join(part.get("text", "") for part in content if part.get("type") == "text")
            messages.append({"role": item["role"], "content": content})
    messages.append({"role": "user", "content": message.strip()})
    try:
        answer = assistant.ask(messages)
    except Exception:
        answer = "AI 服务暂时不可用，请检查 LLM 地址、密钥和网络。"
    return history + [
        {"role": "user", "content": message.strip()},
        {"role": "assistant", "content": answer},
    ], ""


def build_demo():
    start_default, end_default = default_dates()
    with gr.Blocks(title="个人健康记录", analytics_enabled=False) as demo:
        with gr.Row(elem_id="dashboard"):
            with gr.Column(scale=6, elem_id="panel"):
                gr.Markdown("# 我的健康记录\n记录体重、饮食、睡眠和每天的感受。", elem_id="title")
                with gr.Row(elem_id="record-fields"):
                    record_date = gr.DateTime(value=date.today().isoformat(), include_time=False, type="string", label="记录日期", interactive=True, min_width=150)
                    weight = gr.Number(value=None, label="体重（kg）", precision=2, min_width=100)
                    save = gr.Button("保存记录", variant="primary", elem_id="save", min_width=112, scale=0)
                journal = gr.Textbox(
                    label="今日健康随笔",
                    placeholder="今天吃了什么？睡得怎么样？心情、压力、运动和身体感受如何？",
                    lines=3, max_lines=4,
                )
                notice = gr.Markdown("记录保存在本机；提问时，AI 会按需读取相关记录。", elem_id="notice")
                with gr.Row(elem_id="trend-header"):
                    gr.Markdown("## 体重趋势", elem_id="trend-title")
                    quick_range = gr.Dropdown(["最近七天", "最近三十天", "最近九十天"], value="最近七天", show_label=False, label="趋势范围", min_width=120, scale=0, elem_id="trend-range", filterable=False)
                    with gr.Column(scale=0, min_width=150, elem_classes="trend-date"):
                        start_date = gr.DateTime(value=start_default, include_time=False, type="string", label="开始日期", show_label=False, interactive=True, elem_id="trend-start")
                    with gr.Column(scale=0, min_width=150, elem_classes="trend-date"):
                        end_date = gr.DateTime(value=end_default, include_time=False, type="string", label="结束日期", show_label=False, interactive=True, elem_id="trend-end")
                gr.Markdown("点选图上的体重，查看或编辑当天记录。", elem_id="chart-hint")
                chart = gr.HTML(
                    js_on_load="""
                    const selectPoint = (event) => {
                        const point = event.target.closest('[data-date]');
                        if (!point) return;
                        if (event.type === 'keydown' && !['Enter', ' '].includes(event.key)) return;
                        event.preventDefault();
                        trigger('select', {index: point.dataset.date, value: point.dataset.date});
                    };
                    element.addEventListener('click', selectPoint);
                    element.addEventListener('keydown', selectPoint);
                    """,
                    elem_id="chart",
                )
                summary = gr.Markdown(elem_id="summary")
                journals = gr.State()
            with gr.Column(scale=4, elem_id="chat-panel"):
                gr.Markdown("## 和你的健康记录对话")
                gr.Markdown(f"模型：{settings.llm_model} · {'密钥已配置' if settings.llm_api_key else '密钥未配置'}", elem_id="model-info")
                chatbot = gr.Chatbot(elem_id="chatbot")
                question = gr.Textbox(label="问一个问题", placeholder="例如：我最近的体重和睡眠有什么关系？", lines=2, max_lines=4, elem_id="question", info="Enter 发送 · Alt+Enter 换行")
                ask = gr.Button("发送", variant="primary", elem_id="ask")

        def quick_change(value):
            days = {"最近七天": 6, "最近三十天": 29, "最近九十天": 89}[value]
            end = date.today().isoformat()
            start = (date.today() - __import__("datetime").timedelta(days=days)).isoformat()
            chart_html, summary_text_value, journal_html = range_values(start, end)
            return start, end, chart_html, summary_text_value, journal_html

        quick_range.change(quick_change, quick_range, [start_date, end_date, chart, summary, journals])
        for trigger in (start_date.change, end_date.change):
            trigger(range_values, [start_date, end_date], [chart, summary, journals])
        save.click(save_record, [record_date, weight, journal, start_date, end_date], [notice, chart, summary, journals])
        record_date.change(load_record, inputs=record_date, outputs=[weight, journal])
        chart.select(select_chart_point, None, [record_date, weight, journal], scroll_to_output=False)
        ask.click(ask_ai, [question, chatbot], [chatbot, question])
        demo.load(fn=None, js=CHAT_KEYS)
        chart_html, summary_text_value, journal_html = range_values(start_default, end_default)
        demo.load(
            lambda: (
                chart_html,
                summary_text_value,
                journal_html,
                *load_record(date.today().isoformat()),
            ),
            outputs=[chart, summary, journals, weight, journal],
        )
    return demo


if __name__ == "__main__":
    build_demo().launch(server_name=settings.host, server_port=settings.port, theme=gr.themes.Soft(primary_hue="blue", neutral_hue="gray"), css=CSS)
