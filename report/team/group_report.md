# Báo cáo nhóm — Day 03 Research Agent Tool Eval

## 1. Thông tin nhóm

- Tên nhóm: MeoConSatThu (1 thành viên: Nguyễn Sỹ Huy Kiên, 2A202603641)
- Thành viên và phân công: xem [TEAM.md](../../TEAM.md)
- Provider/model dùng cho v0–v6: OpenAI `gpt-4o-mini` (`--provider openai`, model mặc định của provider)

## 2. Mục tiêu và cách tiếp cận — PHẦN A: Giới thiệu agent

### A1. Agent này làm được gì

Research agent tiếng Việt: tìm tin tức trên web, xem tweet theo tài khoản hoặc theo chủ đề, xem Hacker News đang bàn gì, đọc nội dung một URL. Agent hỏi lại khi thiếu thông tin (tài khoản, URL), từ chối câu ngoài phạm vi research, và luôn xin xác nhận trước khi đăng lên Telegram.

**Cách chạy UI** (từ `starter_v0/`, đã thêm `streamlit>=1.30` vào `requirements.txt`):

```bash
pip install -r requirements.txt
streamlit run app.py      # mở http://localhost:8501
```

UI ghi mỗi lượt chat vào `starter_v0/transcripts/ui_*.transcript.json` và hiển thị tool call của từng câu trả lời.

**Link dùng thử (deploy):** chưa deploy, chạy local tại `http://localhost:8501`. Có thể mở link public tạm bằng `cloudflared tunnel --url http://localhost:8501` (xem README).

### A2. Tool agent có

| Tên tool | Làm được gì | Tool mới nhóm thêm? |
|---|---|---|
| clarify | Hỏi lại người dùng khi thiếu thông tin (`text`) hoặc xin xác nhận (`yes_no`) | không |
| timeline | Lấy tweet gần đây của một tài khoản (handle không có @) | không |
| social_search | Tìm tweet theo chủ đề, sắp xếp `Latest`/`Top` | không |
| lookup | Tìm trên web (Tavily), `topic=news` cho tin tức, `timeframe` day/week/month/year | không |
| fetch | Đọc nội dung một URL cụ thể (Firecrawl) | không |
| format | Trình bày item đã có thành digest markdown | không |
| send | Gửi text lên Telegram, chỉ khi `confirmed=true` | không |
| policy, papers, paper_text | Tìm policy nội bộ, tìm paper arXiv, đọc text paper | không |
| **hn_search** | Tìm bài trên Hacker News theo từ khóa (Algolia API, không cần key) | **có** |

### A3. Câu hỏi mẫu để thử

1. Tin tức AI hôm nay có gì nổi bật?
2. Lấy 3 tweet mới nhất của Sam Altman
3. Hacker News đang bàn gì về Rust?
4. Tóm tắt bài này giúp mình (agent sẽ hỏi lại link)
5. Đăng bản tin AI hôm nay lên Telegram (agent sẽ hỏi xác nhận)

## 3. Giải pháp

- `system_prompt.md`: bỏ persona "fast, proactive", bỏ chỉ dẫn "đừng hỏi lại, tự đoán (chọn Sam Altman, tự bịa URL)" và "cứ gửi luôn"; thay bằng persona "careful", rule hỏi lại bằng `clarify(response_type="text")` khi thiếu tài khoản/URL, rule xác nhận bằng `clarify(response_type="yes_no")` trước khi `send`, và rule hội thoại nhiều lượt (chỉ thị ở lượt sau ghi đè lượt trước).
- `tools.yaml`:
  - `lookup`: mô tả quy ước `query` (chỉ chủ đề cốt lõi), `topic` (`news` cho tin tức), `timeframe`; description nêu khi nào dùng / không dùng.
  - `social_search`: description nêu rõ là Twitter/X, không dùng khi user yêu cầu web/tin tức hoặc đã bảo bỏ Twitter.
  - `clarify`: đưa `response_type` vào `required`.
  - Thêm tool mới `hn_search`.
- Tool mới `hn_search` (`starter_v0/tools/hn_search/`): nhận `query`, `limit` (ép về 1–20, giá trị sai kiểu dùng mặc định 5), trả `items` gồm title/url/points/comments. Agent gọi khi user nhắc Hacker News/HN; không dùng cho tin web chung (lookup) hay Twitter (social_search).

## 4. Kết quả — PHẦN B: Chi tiết và bằng chứng

### B1. Version Evidence

Mọi run dưới đây có `provider_error_cases = 0` và `measured_cases = total_cases`. Chi tiết hash ở `starter_v0/artifacts/version_log.csv`.

| Version | Changed Artifact | Hypothesis | Metric Before | Metric After | Run File |
|---|---|---|---:|---:|---|
| v0 | baseline (starter) | — | — | 0.70 (14/20) | `runs/v0_B_base_openai_20261110T154523084089.json` |
| v1 | `tools.yaml` (lookup: query/topic/timeframe) | R13 sai args vì mô tả `query`/`topic` không nêu quy ước tách chủ đề và loại tin | 0.70 | 0.75 (R13 → PASS, không regression) | `runs/v1_B_base_openai_20261110T220127146788.json` |
| v2 | `system_prompt.md` (careful, clarify khi thiếu info, confirm trước send) | Prompt ra lệnh chủ động, cấm hỏi, tự đoán, tự gửi nên R10/R11/R12 sai | 0.75 | 0.90 (R08/R12/R14 PASS ổn định; R10, M06 FAIL; R10/R11/M06 lật giữa các lần chạy) | `runs/v2_B_base_openai_20261110T223220440455.json` |
| v3 | `tools.yaml` (clarify: `response_type` required) | R10 gọi đúng `clarify` nhưng `response_type=None` vì tham số optional | 0.90 | 0.95 (R10/R11 PASS; M06 FAIL) | `runs/v3_B_base_openai_20261110T224526168907.json` |
| v4 | `system_prompt.md` (rule nhiều lượt) | M06 sai vì prompt không có rule "lượt sau ghi đè lượt trước" | 0.95 | 0.95 (không cải thiện, M06 vẫn gọi `social_search`) | `runs/v4_B_base_openai_20261110T225302564400.json` |
| v5 | `tools.yaml` (description social_search/lookup) | Description không nhắc Twitter/web nên model không nối "chuyển sang web tin tức" với `lookup` | 0.95 | 1.00 (20/20, lặp lại 20/20 ở lần chạy thứ hai) | `runs/v5_B_base_openai_20261110T230139777663.json` |
| v6 | `tools.yaml` (thêm `hn_search`) + `eval_group.json` | Tool mới có description rõ không gây nhầm routing | 1.00 | base 1.00 (20/20), group 1.00 (10/10) | `runs/v6_B_base_openai_20261110T231554087788.json`, `runs/v6_B_group_openai_20261110T231630961584.json` |

### B2. Failure Analysis

Từ `results[*].result` của run v0 (và các run sau cho lỗi phát sinh).

| Case ID | Failure Type | Actual Tool Calls | What Failed | Fix |
|---|---|---|---|---|
| R08_out_of_scope | out_of_scope | `send` | expected no tool call; model dùng `send` như cách "trả lời" | v2: persona careful + `send` phải có xác nhận → không gọi tool |
| R14_out_of_scope_coding | out_of_scope | `send` | expected no tool call | v2 (như R08) |
| R10_missing_handle | missing_info | `timeline` | missing `clarify`; model tự đoán tài khoản theo prompt "pick Sam Altman" | v2: clarify khi thiếu tài khoản; v3: `response_type` required (v2 còn `response_type=None`) |
| R11_missing_url | missing_info | `fetch` | missing `clarify`; model tự bịa URL theo prompt "assume a likely URL" | v2 + v3 |
| R12_confirm_before_send | wrong_boundary | `send` | missing `clarify(yes_no)`; prompt bảo "just go ahead and do it" | v2: confirm bằng `clarify(yes_no)` trước `send` |
| R13_parallel_web_and_tweets | wrong_tool | `lookup` + `social_search` | gọi đủ 2 tool nhưng `query='AI news'` (expected `AI`), `topic=None` (expected `news`) | v1: quy ước args của `lookup` |
| M06_switch_tool (từ v2) | wrong_tool | `social_search(query=OpenAI)` | mang theo chủ đề nhưng bỏ qua chỉ thị "bỏ Twitter, chuyển sang web" | v4 (không đủ) → v5: description phân biệt Twitter/web |

### B3. Team Eval Cases

Run: `runs/v6_B_group_openai_20261110T231630961584.json` (10/10 PASS).

| Case ID | What It Tests | Expected Tool/Behavior | Result |
|---|---|---|---|
| G01_hn_search_routing (single) | Nhắc Hacker News → tool mới | `hn_search(query=LLM)` | PASS |
| G02_timeframe_month (single) | "tháng này" → month | `lookup(Nvidia, news, month)` | PASS |
| G03_handle_mapping_new_person (single) | Map Satya Nadella → handle | `timeline(satyanadella, limit=3)` | PASS |
| G04_out_of_scope_translation (single) | Dịch thuật ngoài phạm vi | không gọi tool | PASS |
| G05_top_and_limit_args (single) | "10 tweet nổi bật nhất" | `social_search(Gemini, Top, 10)` | PASS |
| G06_send_after_confirmation (multi) | User đã xác nhận → gửi | `send(confirmed=true)` | PASS |
| G07_switch_to_hn (multi) | Đổi Twitter → Hacker News, giữ chủ đề | `hn_search(query=Rust)` | PASS |
| G08_cancel_send_then_search (multi) | Huỷ việc gửi, chuyển sang tìm tin | `lookup(AI, news, week)` | PASS |
| G09_correction_timeframe (multi) | Sửa day → week | `lookup(Apple, news, week)` | PASS |
| G10_hn_limit_carryover (multi) | Lượt cuối chỉ nói số lượng | `hn_search(Python, limit=3)` | PASS |

### B4. Live Chat Evidence

Transcript: `starter_v0/transcripts/ui_v6_openai_20261110T232124125281.transcript.json` (chạy qua UI Streamlit, version `v6+p42e5c681c56c+t6b49ab049c21`).

| Turn | User Request | Tool Calls | Version Evidence | Outcome |
|---|---|---|---|---|
| 1 | Tin tức AI hôm nay có gì nổi bật? | `lookup(query="AI", topic="news", timeframe="day", max_results=5)` | v6 | Trả 5 tin AI ngày 10/11/2026 có link nguồn (WilmerHale, The Register, Microsoft, Notre Dame, Pitt). Lưu ý: trả lời bằng tiếng Anh dù user hỏi tiếng Việt |
| 2 | Tóm tắt 5 tweet mới nhất | không gọi tool | v6 | Hỏi lại "tài khoản Twitter nào" bằng văn bản, không tự đoán tài khoản |
| 3 | Của Sam Altman | `timeline(screenname="sama", limit=5)` | v6 | Mang theo `limit=5` từ lượt 2, map Sam Altman → `sama`, tóm tắt 5 tweet bằng tiếng Việt |
| 4 | Đăng bản tin AI hôm nay lên Telegram | không gọi tool | v6 | Hỏi "Bạn có xác nhận muốn đăng... không?", không gọi `send` |

**Nhận xét:** hành vi đúng (hỏi lại khi thiếu tài khoản, xin xác nhận trước khi gửi), nhưng ở lượt 2 và 4 agent hỏi bằng văn bản thay vì gọi tool `clarify`. Lý do: trong eval, harness ép `tool_choice="required"` nên model buộc phải chọn `clarify`; trong UI/chat không ép, model được phép trả lời trực tiếp. Hệ quả: hỏi lại vẫn diễn ra nhưng không có trong `tool_events`, nên đo bằng log khó hơn. Đây là khác biệt giữa môi trường eval và môi trường thật.

### B5a. Required Evidence — Tool mới, unit test, UI

| Item | Evidence File | What Worked | Risk / Guardrail |
|---|---|---|---|
| Tool mới `hn_search` | `starter_v0/tools/hn_search/tool.py`, `TOOL.md`, đăng ký trong `tools/__init__.py` + `tools.yaml` | Route đúng ở G01, G07, G10; không làm hỏng base (20/20) | Không side-effect; lỗi HTTP/input trả error dict, không raise |
| Unit test tool mới (4 test) | `starter_v0/tests/test_tools_todo.py`; `pytest`: 71 passed, 14 skipped, 0 failed | Happy path (assert request + mapping), query rỗng không gọi mạng, `limit` sai kiểu/ngoài khoảng, HTTP 503 | Test offline, mock bằng `fake_http` |
| UI Streamlit | `starter_v0/app.py`, `requirements.txt` | Chat, hiển thị tool call, ghi transcript | Hiển thị cả tool lỗi trong expander, không che lỗi |

Ví dụ lỗi unit test bắt được mà eval không bắt được: model gửi `limit="abc"`, `0` hoặc `999`. Eval chỉ chấm model có gọi đúng tool/args hay không; còn tool có xử lý các giá trị đó an toàn không (ép về 5, 1, 20) chỉ unit test `test_hn_search_bad_limit_from_model_is_clamped` mới kiểm tra.

### B5. Bonus Evidence

Không làm bonus.

## 5. Khó khăn và cách xử lý

- Lệnh smoke test trong `TOOL-SETUP.md` (`python -c "from tools import ..."`) luôn báo `Missing ... env var` dù `.env` đã điền, vì `tools` không tự nạp `.env` (chỉ `preflight_provider.py`, `run_eval.py`, `chat.py` gọi `load_lab_env`). Cách xử lý: gọi `load_lab_env(Path('.'))` trước khi import tools.
- Lần chạy v2 đầu tiên không có tác dụng vì file prompt chưa được lưu; phát hiện nhờ `prompt_hash` trong `artifact_version` không đổi so với v1. Từ đó luôn kiểm tra `+p`/`+t` trước khi đọc kết quả.
- Kết quả dao động giữa các lần chạy cùng cấu hình (v2: R10, R11, M06 lật PASS/FAIL dù temperature=0). Cách xử lý: chạy lại nhiều lần, chỉ kết luận với case ổn định, và tìm nguyên nhân gốc (R10 thực chất là thiếu `response_type`).

## 6. Tổng hợp đóng góp

Chi tiết đóng góp của từng thành viên nằm trong [TEAM.md](../../TEAM.md) và các báo cáo cá nhân `report/team/MSSV_HoTen.md`.

## 7. Hạn chế và hướng cải thiện — B6. Reflection

- **Fix thuộc `system_prompt.md`:** hành vi tổng thể (không tự đoán, hỏi lại, xác nhận trước hành động ghi, persona careful). Bằng chứng: v2 sửa R10/R11/R12 về mặt routing.
- **Fix thuộc `tools.yaml`:** quy ước args và ranh giới giữa các tool (v1 `query`/`topic`, v3 `required`, v5 Twitter vs web). Hai bài học: tham số optional dễ bị model bỏ trống (`topic`, `response_type` đều ra `None`); rule nhiều lượt trong prompt (v4) không đủ, phải để description tool phân biệt rõ nguồn (v5).
- **Eval khác môi trường thật:** eval ép `tool_choice="required"`, còn UI không ép, nên trong chat live agent hỏi lại bằng văn bản thay vì gọi `clarify` (transcript lượt 2, 4); lượt 1 lại trả lời bằng tiếng Anh. Prompt nên yêu cầu rõ "luôn dùng tool `clarify` để hỏi" và "trả lời bằng ngôn ngữ của user".
- **Cần review thủ công:** eval so khớp chính xác (`query='AI news'` bị tính sai dù đúng ý); case dao động giữa các lần chạy cần chạy lặp để kết luận.
- **Vòng tiếp theo:** bỏ câu còn sót "Always finish the request in a single step... using your best judgment" (mâu thuẫn với "do not guess"); chạy mỗi version 3 lần và báo cáo tỉ lệ pass; thử Small Local Model.

## 8. Tài liệu tham khảo

- README, RUBRIC, SUBMISSION của repo lab VinUni-AI20k/K5-L3-DAY03-ResearchAgentToolEval
- Hacker News Search API (Algolia): https://hn.algolia.com/api
