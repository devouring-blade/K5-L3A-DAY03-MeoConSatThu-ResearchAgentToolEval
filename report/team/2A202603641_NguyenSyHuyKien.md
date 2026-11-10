# Báo cáo cá nhân — NguyenSyHuyKien-2A202603641

## 1. Thông tin thành viên

- Họ tên: Nguyễn Sỹ Huy Kiên
- MSSV: 2A202603641
- Email: kien27903@gmail.com

## 2. Phần việc phụ trách

Làm một mình toàn bộ bài lab: fork và setup môi trường (venv, `.env`, preflight, pytest), chạy baseline v0, phân tích lỗi, sáu vòng tối ưu v1–v6, viết tool mới `hn_search` và unit test, viết 10 eval case nhóm, dựng UI Streamlit, chạy chat live và viết báo cáo.

## 3. Đóng góp cụ thể

- **Setup:** dùng provider OpenAI (`gpt-4o-mini`), kiểm tra cả 4 tool chạy thật. Phát hiện lệnh smoke test trong `TOOL-SETUP.md` không nạp `.env`, sửa bằng cách gọi `load_lab_env` trước.
- **Baseline v0:** 14/20 (0.70). Đọc `analysis/v0_base.csv` để gán loại lỗi cho 6 case FAIL theo hành vi thật của model (vd R08/R14 gọi `send`, R13 gọi đủ 2 tool nhưng sai args), thay vì đoán.
- **v1 (`tools.yaml`):** tự đặt giả thuyết R13 sai do mô tả `query`/`topic` của `lookup` không nêu quy ước; tự viết lại description; R13 PASS, không regression (0.75).
- **v2 (`system_prompt.md`):** nhóm R10/R11/R12 chung một nguyên nhân "model tự hành động thay vì hỏi user"; xác định 3 mệnh đề thay thế: persona careful, hỏi lại khi thiếu thông tin, xin phép trước hành động có tác động thật (0.90).
- **Phát hiện lỗi quy trình:** lần chạy v2 đầu không có tác dụng; nhận ra qua `prompt_hash` không đổi (file chưa lưu). Chạy lại v2 nhiều lần, thấy R10/R11/M06 lật PASS/FAIL, không coi lần chạy chưa khẳng định là một version.
- **v3:** từ log `response_type: expected 'text', got None`, tự đề xuất đưa `response_type` vào `required` (0.95).
- **v4–v5:** v4 thêm rule nhiều lượt vào prompt nhưng M06 không cải thiện, ghi lại trung thực; v5 sửa description `social_search`/`lookup` thì đạt 20/20, lặp lại 20/20.
- **v6:** thêm tool `hn_search`, 4 unit test, 10 eval case; base 20/20, group 10/10.
- **UI:** `app.py` Streamlit, ghi transcript. Chat live 4 lượt: agent tìm tin đúng args, hỏi lại tài khoản, carry `limit=5` sang lượt sau, và xin xác nhận trước khi đăng Telegram. Phát hiện trong UI agent hỏi lại bằng văn bản thay vì gọi `clarify` (vì UI không ép `tool_choice=required` như eval).

## 4. Bằng chứng

- File: `starter_v0/artifacts/version_log.csv`, `starter_v0/runs/v0…v6_*.json`, `starter_v0/analysis/*.csv`, `starter_v0/tools/hn_search/`, `starter_v0/tests/test_tools_todo.py`, `starter_v0/data/eval_group.json`, `starter_v0/app.py`, `starter_v0/transcripts/ui_v6_openai_20261110T232124125281.transcript.json`
- Commit: `59f5024` (v0–v5), `2712574` (v6: hn_search, test, eval nhóm), 358f074
- AI/công cụ đã dùng và cách tự kiểm tra kết quả: dùng Claude để giải thích output eval và code chấm điểm, thảo luận nguyên nhân lỗi, gợi ý cấu trúc prompt/description, viết `hn_search`, unit test, eval case, `app.py` và nháp báo cáo. Tự kiểm tra bằng cách: đọc `failures`/`actual_tool_calls` trong run JSON trước khi kết luận; kiểm tra `+p`/`+t` trong `artifact_version` sau mỗi version; chạy `pytest` (71 passed, 0 failed); chạy lại eval để phân biệt cải thiện thật với dao động; tự chạy UI và xem tool call.

## 5. Tự đánh giá

**Học được:**
- Khi model sai, nguyên nhân gần như luôn nằm ở hai file model đọc được: prompt (ra lệnh sai hoặc thiếu rule) và tool declaration (mô tả mơ hồ, tham số optional). Prompt gốc cố tình "cấm hỏi, tự đoán, tự gửi", và model làm đúng như được bảo.
- Tham số optional rất dễ bị model bỏ trống: gặp hai lần (`topic`, `response_type` đều ra `None`). Ghi rõ quy ước hoặc đưa vào `required` là cách sửa.
- Sửa prompt không phải lúc nào cũng đủ: rule nhiều lượt (v4) không cứu được M06, nhưng description tool phân biệt Twitter và web (v5) thì được.
- Một lần chạy không đủ để kết luận: cùng cấu hình mà case lật PASS/FAIL. Phải nhìn log để tìm nguyên nhân gốc thay vì tin vào một con số.
- Kiểm tra hash là cách rẻ nhất để chắc mình đang đo đúng thứ mình đã sửa.

**Còn làm chưa tốt:**
- Xoá mất hai file run của các lần chạy lại v2, trong khi đó là bằng chứng của hiện tượng dao động.
- Chưa bỏ câu "Always finish the request in a single step... best judgment" trong prompt (rubric C2 yêu cầu bỏ chỉ dẫn ép một bước; câu này cũng mâu thuẫn với "do not guess").
- Chưa điền đủ 14 test TODO cho các tool có sẵn, chưa làm bonus.
- Ban đầu sửa nhiều chỗ theo cảm nhận (vd sửa cả `timeframe` ở v1 dù log không báo sai) nên giả thuyết chưa thật gọn.
