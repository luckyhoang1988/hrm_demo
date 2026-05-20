# Lộ trình tích hợp Ký số (Digital Signature) vào HRM App

## Context

Hệ thống HRM hiện có chức năng quản lý hợp đồng lao động (app `contracts`) với khả năng upload file PDF. Bước tiếp theo là cho phép **ký số trực tuyến** — cả bên công ty (HR/admin) và nhân viên có thể ký điện tử hợp lệ theo pháp luật Việt Nam (Luật Giao dịch điện tử 20/2023/QH15, hiệu lực 01/07/2024).

---

## Nhà cung cấp khuyến nghị: VNPT SmartCA

**Lý do chọn VNPT SmartCA:**
- Được cấp phép bởi Bộ TT&TT Việt Nam → chữ ký có giá trị pháp lý đầy đủ
- Tài liệu API công khai nhất trong các nhà cung cấp Việt Nam
- Hỗ trợ ký từ xa (remote signing) qua web/app SmartCA
- Không yêu cầu token USB vật lý → phù hợp ký online

**Các nhà cung cấp thay thế (đều hợp quy định):**
| Nhà cung cấp | Portal | Phù hợp khi |
|---|---|---|
| **VNPT SmartCA** | doitac-smartca.vnpt.vn | Ưu tiên 1 — tài liệu tốt nhất |
| **Viettel vContract** | esign.viettel.vn | Công ty đang dùng Viettel |
| **FPT eSign** | FPT ecosystem | Công ty đang dùng hệ sinh thái FPT |
| **BKAV eSign** | BKAV | Cần xác thực sinh trắc học |

> **Lưu ý tài chính:** Giá khoảng 1–1.5 triệu VND/năm/chứng chỉ. Cần mua chứng chỉ cho **tài khoản doanh nghiệp** (ký phía công ty) + mỗi nhân viên cần có chứng chỉ (hoặc dùng OTP nếu nhà cung cấp hỗ trợ).

---

## Kiến trúc tổng thể

```
┌─────────────────────────────────────────────────┐
│                HRM App (Django)                   │
│                                                   │
│  contract_print → PDF          ┌──────────────┐  │
│  [Gửi ký số] button ──────────▶│  VNPT SmartCA │  │
│                                │  API          │  │
│  Webhook endpoint ◀────────────│  (bên thứ 3)  │  │
│  /contracts/signature/callback/└──────────────┘  │
│         │                                         │
│         ▼                                         │
│  Lưu file đã ký + cập nhật trạng thái DB          │
└─────────────────────────────────────────────────┘
```

### Flow ký số (6 bước):
1. HR tạo hợp đồng, upload file PDF → lưu `contract.contract_file`
2. HR nhấn **"Gửi ký số"** → app gửi file lên VNPT API, nhận `signing_session_id` + `signing_url`
3. App gửi `signing_url` cho nhân viên (qua email hoặc hiển thị trực tiếp)
4. Nhân viên mở link → ký trên app VNPT SmartCA (OTP hoặc chứng chỉ số)
5. VNPT gửi **webhook callback** → app nhận, verify HMAC-SHA256, lưu trạng thái
6. App tải về **file PDF đã ký** → lưu `contract.signed_file`

---

## Thay đổi Database (Migration mới)

Thêm vào `contracts/models.py` — **Contract model**:

```python
SIGNATURE_STATUS = [
    ('none',      'Chưa gửi ký'),
    ('pending',   'Đang chờ ký'),
    ('signed',    'Đã ký'),
    ('rejected',  'Từ chối ký'),
    ('expired',   'Hết hạn ký'),
]

# Fields mới
signature_status     = CharField(choices=SIGNATURE_STATUS, default='none')
signature_session_id = CharField(max_length=200, blank=True)  # ID từ VNPT
signature_url        = CharField(max_length=500, blank=True)  # Link ký cho NV
signed_file          = FileField(upload_to='contracts/signed/', null=True, blank=True)
signature_date       = DateTimeField(null=True, blank=True)   # Khi ký xong
signature_metadata   = JSONField(null=True, blank=True)       # Raw response từ VNPT
```

---

## Files cần tạo/thay đổi

### Tạo mới:
| File | Chức năng |
|---|---|
| `contracts/esign_client.py` | Client class gọi VNPT API (tách biệt, dễ thay đổi nhà cung cấp sau này) |
| `contracts/templates/contracts/contract_signature.html` | Trang hiển thị trạng thái ký + QR code link ký |

### Sửa có sẵn:
| File | Thay đổi |
|---|---|
| `contracts/models.py` | Thêm 6 fields signature |
| `contracts/views.py` | Thêm 3 views: `contract_request_signature`, `contract_signature_callback`, `contract_signature_status` |
| `contracts/urls.py` | Thêm 3 URL patterns |
| `contracts/templates/contracts/contract_detail.html` | Thêm section ký số + nút "Gửi ký số" |
| `contracts/migrations/` | Migration mới cho 6 fields |

---

## Phân chia theo giai đoạn

### Giai đoạn 1 — Chuẩn bị & Kết nối API (2–3 ngày)
- [ ] Đăng ký tài khoản đối tác tại doitac-smartca.vnpt.vn
- [ ] Lấy `sp_id`, `sp_password`, `secret_key` từ VNPT
- [ ] Thêm vào `.env`: `VNPT_SP_ID`, `VNPT_SP_PASSWORD`, `VNPT_SECRET_KEY`, `VNPT_API_URL`
- [ ] Tạo `contracts/esign_client.py` với các method: `get_token()`, `create_session()`, `get_signed_file()`
- [ ] Test kết nối API với môi trường sandbox của VNPT

### Giai đoạn 2 — Gửi ký & Hiển thị trạng thái (2–3 ngày)
- [ ] Thêm migration 6 fields vào Contract
- [ ] View `contract_request_signature(pk)` — gửi file, lưu session_id + signing_url
- [ ] URL + template `contract_signature.html` — hiển thị link ký, QR code
- [ ] Nút "Gửi ký số" trên `contract_detail.html` (chỉ hiện khi `signature_status='none'` và có file PDF)

### Giai đoạn 3 — Webhook & Lưu file đã ký (2–3 ngày)
- [ ] View `contract_signature_callback()` — `@csrf_exempt`, verify HMAC-SHA256, update DB
- [ ] Sau callback: gọi API VNPT tải về file đã ký → lưu `signed_file`
- [ ] Hiển thị file đã ký trên `contract_detail.html` (riêng với file gốc)
- [ ] Gửi email thông báo khi ký xong (nếu có cấu hình email)

### Giai đoạn 4 — Hoàn thiện (1–2 ngày)
- [ ] Xử lý trường hợp timeout / từ chối ký / hết hạn session
- [ ] Nút "Gửi lại" nếu hết hạn
- [ ] Thêm vào Activity Log: hành động `signature_request`, `signature_completed`
- [ ] Thêm cột "Trạng thái ký" vào `contract_list.html`
- [ ] Cập nhật Dashboard: thêm card "Chờ ký số"

---

## `contracts/esign_client.py` — Cấu trúc đề xuất

```python
# Abstraction layer — dễ đổi nhà cung cấp mà không ảnh hưởng views
class ESignClient:
    def get_token(self) -> str: ...
    def create_signing_session(self, pdf_bytes, contract_number, signer_email, signer_name) -> dict:
        # Returns: { session_id, signing_url, expires_at }
        ...
    def get_signed_document(self, session_id) -> bytes:
        # Returns: PDF bytes của file đã ký
        ...
    def get_session_status(self, session_id) -> str:
        # Returns: 'pending' | 'signed' | 'rejected' | 'expired'
        ...
```

Việc tách `esign_client.py` giúp sau này **đổi từ VNPT sang Viettel** chỉ cần viết lại 1 file, không cần sửa views.

---

## Webhook Security (bắt buộc)

```python
# contracts/views.py
@csrf_exempt
def contract_signature_callback(request):
    received_sig = request.META.get('HTTP_X_VNPT_SIGNATURE', '')
    expected_sig = hmac.new(
        settings.VNPT_SECRET_KEY.encode(),
        request.body,
        hashlib.sha256,
    ).hexdigest()
    if not hmac.compare_digest(received_sig, expected_sig):
        return HttpResponse(status=403)
    # ... xử lý callback
```

**Yêu cầu bắt buộc:**
- Dùng `hmac.compare_digest()` — tránh timing attack
- Lưu `signature_session_id` trước khi nhận callback để tránh xử lý giả mạo
- Idempotency: check `signature_status` trước khi xử lý lại (webhook có thể gửi nhiều lần)
- HTTPS bắt buộc cho endpoint webhook (dùng ngrok khi dev local)

---

## Lưu ý kỹ thuật quan trọng

1. **File PDF trước khi ký** — cần có `contract_file` dạng PDF. Hiện tại app cho upload PDF/DOC/DOCX. Nên yêu cầu **chỉ PDF** khi ký số, hoặc tự convert DOC→PDF trước khi gửi ký.

2. **Ai ký?** — Quyết định trước:
   - Chỉ nhân viên ký (đơn giản hơn)
   - Cả 2 bên: nhân viên + đại diện công ty (sequential signing, phức tạp hơn)

3. **Xác thực nhân viên** — VNPT SmartCA có thể yêu cầu nhân viên đã có chứng chỉ số. Nếu không, dùng phương thức OTP (đơn giản hơn nhưng giá trị pháp lý thấp hơn).

4. **Expose webhook ra internet** — cần server có domain thật. Khi dev local: dùng ngrok để test webhook.

5. **Không cần Celery ngay** — ban đầu có thể xử lý đồng bộ. Chỉ cần Celery nếu tải file đã ký mất > 2–3 giây.

---

## Kiểm thử (Verification)

1. **Sandbox VNPT**: Đăng ký tài khoản test → test gửi file, nhận link ký giả
2. **Webhook local**: Dùng `ngrok http 8000` → expose localhost → cấu hình URL callback trên VNPT portal
3. **Test flow đầy đủ**: Tạo HĐ → upload PDF → Gửi ký → Mở link → Ký giả → Check DB `signature_status='signed'` → Download `signed_file`
4. **Test lỗi**: Timeout, từ chối ký, gửi lại

---

## Ước tính thời gian phát triển

| Giai đoạn | Công việc | Thời gian |
|---|---|---|
| 0 | Đăng ký VNPT partner + lấy API credentials | 1–3 ngày (tùy VNPT duyệt) |
| 1 | `esign_client.py` + test kết nối sandbox | 2–3 ngày |
| 2 | Gửi ký + UI trạng thái | 2–3 ngày |
| 3 | Webhook + lưu file đã ký | 2–3 ngày |
| 4 | Hoàn thiện, edge cases | 1–2 ngày |
| **Tổng** | | **~8–14 ngày dev** |
