# Intelligent Traffic Demo

## English

This repository demonstrates a simple PyQt5 application that integrates with the NetSDK library to connect to network video devices. The UI lets you log in, preview video, and receive plate recognition alarms. Any captured images are written to the **Global** and **Small** folders. These photos are included only to showcase the interface and are not from real traffic.

### Requirements
- Python 3.8 or higher
- [PyQt5](https://pypi.org/project/PyQt5/)
- NetSDK Python modules (not provided here)

### Getting Started
1. Place the NetSDK modules next to this project so `from NetSDK.NetSDK import NetClient` works.
2. Install dependencies: `pip install PyQt5`.
3. Run the application:
   ```bash
   python TrafficDemo.py
   ```
The script `testGUI.py` can be used to test the interface.

### History Search
Each recognized event is written to `event_history.csv`. You can filter and
display past records with:

```bash
python history_search.py --start "2023-01-01 00:00:00" --end "2023-01-02 00:00:00"
```

## Tiếng Việt

Kho lưu trữ này minh họa một ứng dụng PyQt5 đơn giản sử dụng thư viện NetSDK để kết nối tới thiết bị video mạng. Giao diện cho phép đăng nhập, xem trực tiếp và nhận sự kiện nhận dạng biển số. Ảnh lưu trong thư mục **Global** và **Small** chỉ dùng để trình bày giao diện và không phải dữ liệu thực tế.

### Yêu cầu
- Python 3.8 trở lên
- Gói [PyQt5](https://pypi.org/project/PyQt5/)
- Các module NetSDK cho Python (không kèm theo)

### Bắt đầu
1. Chép các module NetSDK vào cùng thư mục để lệnh `from NetSDK.NetSDK import NetClient` hoạt động.
2. Cài đặt phụ thuộc: `pip install PyQt5`.
3. Chạy ứng dụng:
   ```bash
   python TrafficDemo.py
   ```
   File `testGUI.py` chỉ nhằm mục đích kiểm thử giao diện.
export DISPLAY=127.0.0.1:0
### Tra cứu lịch sử
Mỗi sự kiện nhận dạng được ghi vào `event_history.csv`. Bạn có thể lọc và xem
lại lịch sử bằng lệnh:

```bash
python history_search.py --start "2023-01-01 00:00:00" --end "2023-01-02 00:00:00"
```
