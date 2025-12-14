# 智能发票管理助手 - 授权系统

## 📚 文档说明

本项目已集成激活码授权系统，以下是相关文档：

### 使用文档
1. **激活码使用说明.md** - 激活码生成工具快速使用指南
2. **授权系统说明.md** - 授权系统完整功能说明

### 核心文件
1. **license_manager.py** - 授权管理核心模块
2. **generate_activation_code.py** - 激活码生成工具（仅供开发者使用）
3. **InvoiceMaster.py** - 主程序（已集成授权功能）

---

## 🚀 快速使用

### 生成激活码

```bash
# 进入项目目录
cd /Users/jane/Desktop/Invoice-Project

# 运行激活码生成工具
python3 generate_activation_code.py
```

### 用户激活流程

1. 用户打开软件 → 设置 → 激活管理
2. 复制机器码发送给您
3. 您使用工具生成激活码
4. 用户输入激活码激活

---

## 💡 试用机制

- 未激活：10 次免费试用
- 试用期间：显示剩余次数
- 试用用完：必须激活
- 已激活：无限制使用

---

## ⚠️ 重要提示

**请勿分发以下文件给用户：**
- `generate_activation_code.py`
- 本 README 文件

**密钥位置：**
- `license_manager.py` 第 12 行
- `generate_activation_code.py` 第 16 行

如需修改密钥，必须同时修改两个文件。

---

## 📞 更多信息

详细说明请查看：
- `激活码使用说明.md`
- `授权系统说明.md`
