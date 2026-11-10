"""Streamlit UI for the Research Agent.

Run from starter_v0/:  streamlit run app.py
Every turn is logged to transcripts/*.transcript.json (same format as chat.py).
"""
from __future__ import annotations

from datetime import datetime

import streamlit as st

from chat import (
    ARTIFACTS_DIR, ROOT, now_iso, run_model_tool_loop, safe_slug, trim_history, write_transcript,
)
from providers import make_provider
from tools import load_tool_declarations, to_openai_tools
from versioning import artifact_version_dict, build_artifact_version

PROVIDER = "openai"
VERSION = "v6"
PROMPT_PATH = ARTIFACTS_DIR / "system_prompt.md"
TOOLS_PATH = ARTIFACTS_DIR / "tools.yaml"

st.set_page_config(page_title="Research Agent", page_icon="🔎")
st.title("🔎 Research Agent")
st.caption("Tra tin web, Twitter/X, Hacker News, đọc URL. Agent hỏi lại khi thiếu thông tin và xin xác nhận trước khi gửi Telegram.")

if "transcript" not in st.session_state:
    version = build_artifact_version(VERSION, PROMPT_PATH, TOOLS_PATH)
    stamp = datetime.now().strftime("%Y%m%dT%H%M%S%f")
    tid = "_".join(["ui", safe_slug(VERSION), PROVIDER, stamp])
    st.session_state.transcript_path = ROOT / "transcripts" / f"{tid}.transcript.json"
    st.session_state.transcript = {
        "transcript_id": tid, **artifact_version_dict(version), "provider": PROVIDER,
        "source": "streamlit_ui", "created_at": now_iso(), "updated_at": now_iso(), "turns": [],
    }
    st.session_state.history = []
    st.session_state.display = []

system_prompt = PROMPT_PATH.read_text(encoding="utf-8")
tools = to_openai_tools(load_tool_declarations(TOOLS_PATH))
provider = make_provider(PROVIDER)

with st.sidebar:
    st.markdown(f"**Version:** `{st.session_state.transcript['artifact_version']}`")
    st.markdown("**Thử hỏi:**\n- Tin tức AI hôm nay có gì nổi bật?\n- 3 tweet mới nhất của Sam Altman\n"
                "- Hacker News đang bàn gì về Rust?\n- Tóm tắt bài này giúp mình\n- Đăng bản tin lên Telegram")
    st.caption(f"Transcript: {st.session_state.transcript_path.name}")

for msg in st.session_state.display:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])
        if msg.get("events"):
            with st.expander(f"🔧 {len(msg['events'])} tool call(s)"):
                st.json(msg["events"])

if user_text := st.chat_input("Hỏi agent..."):
    st.session_state.display.append({"role": "user", "content": user_text})
    with st.chat_message("user"):
        st.markdown(user_text)

    messages = [
        {"role": "system", "content": system_prompt},
        *trim_history(st.session_state.history, 5),
        {"role": "user", "content": user_text},
    ]
    turn = {"turn_index": len(st.session_state.transcript["turns"]) + 1, "started_at": now_iso(), "user": user_text}
    with st.chat_message("assistant"):
        try:
            with st.spinner("Đang chạy tool..."):
                result = run_model_tool_loop(provider=provider, messages=messages, tools=tools, model=None, max_tool_rounds=4)
            turn.update(result)
            answer = result["assistant_text"] or "(không có câu trả lời)"
            events = result["tool_events"]
            st.markdown(answer)
            if events:
                with st.expander(f"🔧 {len(events)} tool call(s)"):
                    st.json(events)
            st.session_state.history += [{"role": "user", "content": user_text}, {"role": "assistant", "content": answer}]
            st.session_state.display.append({"role": "assistant", "content": answer, "events": events})
        except Exception as exc:
            turn.update({"status": "provider_error", "error": f"{type(exc).__name__}: {exc}"})
            st.error(turn["error"])
    turn["ended_at"] = now_iso()
    st.session_state.transcript["turns"].append(turn)
    write_transcript(st.session_state.transcript_path, st.session_state.transcript)