# 跨平台兼容性报告

## 支持的操作系统

| 系统 | 版本 | Python | PyQt6 | 状态 |
|-----|------|--------|-------|------|
| Windows 7 | SP1 x64 | 3.8 | 6.1.0 | ✅ 专用版本 |
| Windows 10/11 | 全版本 | 3.10+ | 最新 | ✅ 完全支持 |
| macOS | 10.14+ | 3.10+ | 最新 | ✅ 完全支持 |
| 统信 UOS | 20/21 | 3.10+ | 最新 | ✅ 完全支持 |

## 已检查并确认的兼容性

### 1. 平台检测 ✅

文件: `src/utils/config.py`

```python
def _detect_platform():
    s = platform.system()
    if s == "Darwin": return "mac"
    if s == "Windows":
        v = platform.release()
        if v == "7": return "win7"
        return "win10"
    return "linux"
```

- 正确区分 Windows 7 / Windows 10 / macOS / Linux
- Win7 自动启用 Legacy 模式（禁用渐变、阴影）

### 2. 机器码生成 ✅

文件: `src/core/license_manager.py`

- **Windows**: 使用 `wmic csproduct get uuid` + 计算机名
- **macOS**: 使用 `ioreg` 获取硬件 UUID
- **Linux/UOS**: 使用 `/etc/machine-id` 或 `/var/lib/dbus/machine-id`
- 均有 fallback 方案（MAC 地址）

### 3. 日志目录 ✅

文件: `src/utils/log_manager.py`

- **Windows**: `%APPDATA%/InvoiceMaster/logs`
- **macOS**: `~/Library/Logs/InvoiceMaster`
- **Linux/UOS**: `~/.local/share/InvoiceMaster/logs`

### 4. 打开 PDF 文件 ✅

文件: `src/ui/main_window.py`

```python
if platform.system() == "Windows":
    os.startfile(out_path, "print")
elif platform.system() == "Darwin":
    os.system(f"open '{out_path}'")
else:
    os.system(f"xdg-open '{out_path}'")
```

### 5. 打印机枚举 ✅

文件: `src/ui/main_window.py`

```python
if platform.system() in ["Windows", "Linux"]: 
    for p in QPrinterInfo.availablePrinterNames():
        self.cb_pr.addItem(f"🖨️ {p}")
```

- macOS 默认使用系统打印对话框

### 6. 文件编码 ✅

- 所有文件操作使用 `encoding='utf-8'`
- CSV 导出使用 `utf-8-sig` 支持 Excel

### 7. 路径处理 ✅

- 使用 `os.path.join()` 而非硬编码路径分隔符
- 无硬编码的 Windows 盘符 (C:, D:)
- 无 Windows 特定的路径格式

### 8. UI 自适应 ✅

文件: `src/utils/config.py`

Win7 Legacy 模式：
- 禁用渐变背景
- 禁用阴影效果
- 降低预览分辨率

## GitHub Actions 构建配置

### Windows 7 专用版

- Python 3.8 (最后支持 Win7)
- PyMuPDF 1.23.26 (锁定版本)
- PyQt6 6.1.0 (锁定版本)
- opencv-python-headless (兼容性更好)
- pyzbar DLL 打包

### Windows 10/11 现代版

- Python 3.10
- PyMuPDF 1.23.26
- 最新 PyQt6

### macOS 版

- Python 3.10
- 标准依赖

### Linux/UOS 版

- Python 3.10
- 安装 libzbar-dev 用于二维码
- 安装 libxcb-cursor0 修复 Qt 光标

## 依赖版本

### requirements.txt

```
PyQt6
pdfplumber
pandas
requests
openpyxl
pymupdf
pyzbar
opencv-python
```

### Win7 专用锁定版本

```
PyQt6==6.1.0
PyQt6-Qt6==6.1.0
PyQt6-sip==13.1.0
pymupdf==1.23.26
opencv-python-headless
```

## 注意事项

### Windows 7

1. 需要安装 Visual C++ Redistributable 2015-2019
2. 需要 Windows 7 SP1 和更新
3. 使用专门的 Win7 兼容版本

### 统信 UOS

1. 需要安装 libzbar
2. 打印功能使用 xdg-open 调用系统默认程序

### macOS

1. 建议使用 10.14 (Mojave) 或更高版本
2. 首次运行可能需要授权

## 更新日期

2024-12-15
