---
name: new-feature
description: Checklist chuẩn bị trước khi bắt đầu làm tính năng mới cho HRM
---

Trước khi bắt đầu tính năng mới, thực hiện theo thứ tự:

1. Đọc `CLAUDE.md` phần "Tính năng đã hoàn thành" để nắm context
2. Hỏi người dùng mô tả tính năng muốn làm (nếu chưa rõ)
3. Dùng agent `researcher` để tìm code hiện có liên quan
4. Lập kế hoạch: file nào cần sửa, có cần migration không, template nào bị ảnh hưởng
5. Trình bày kế hoạch cho người dùng xác nhận trước khi code

Luôn ưu tiên tái sử dụng code có sẵn. Không tạo function mới nếu đã có function tương tự.
