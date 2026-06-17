# Agnes Vision Proxy

[中文](#中文) | [English](#english)

---

## 中文

**Hermes Agent → Agnes 2.0 Flash 视觉代理**

Hermes Agent 发图片给视觉模型时使用 base64 编码（`data:image/png;base64,...`），但 Agnes 2.0 Flash 只接受公网 HTTP URL。这个代理坐在中间，自动把 base64 图片上传到 [0x0.st](https://0x0.st) 免费图床，换成公网 URL 再转发给 Agnes API。

### 为什么需要它

| 模型 | 接受 base64 | 接受公网 URL | 费用 |
|------|------------|-------------|------|
| GPT-4V / Claude / Gemini | ✅ | ✅ | 💰💰💰 |
| 豆包 Seed 2.0 Pro | ✅ | ✅ | 💰 |
| **Agnes 2.0 Flash** | ❌ | ✅ | **🆓 免费** |

Agnes 2.0 Flash 是少数只接受 URL 的视觉模型，同时也是极少数完全免费的。这个代理就是补上"base64 → URL"这一步。

### 快速开始

```bash
# 1. 设置 API Key
echo "AGNES_API_KEY=*** >> ~/AppData/Local/hermes/.env

# 2. 修改 Hermes config.yaml
#    auxiliary.vision.provider: openai
#    auxiliary.vision.model: agnes-2.0-flash
#    auxiliary.vision.base_url: http://localhost:8899/v1

# 3. 启动代理
python agnes-vision-proxy.py
# 看到 "[proxy] 等待请求..." 就就绪

# 4. 正常用 Hermes，截图粘贴即可
```

### 工作原理

```
截图 → Hermes (base64) → 代理 :8899 → 0x0.st 上传 → 公网 URL → Agnes API → 结果
```

### 依赖

- Python 3（标准库，零额外安装）
- curl（系统自带）
- 0x0.st（免费图床，无需注册）
- Agnes AI API Key（[免费注册](https://platform.agnes-ai.com)）

### 成本

- Agnes 2.0 Flash：当前 **$0/百万 token**（输入和输出都免费）
- 0x0.st：免费，512MB 上限，文件保留 30 天+

---

## English

**Hermes Agent → Agnes 2.0 Flash Vision Proxy**

Bridges the gap between Hermes Agent (which sends images as base64 data URLs) and Agnes 2.0 Flash (which only accepts public HTTP URLs). Automatically uploads base64 images to 0x0.st free image hosting and replaces them with public URLs before forwarding to the Agnes API.

### Why

Most vision models (GPT-4V, Claude, Gemini) accept base64 images. Agnes 2.0 Flash doesn't — but it's completely free. This proxy fills the gap.

### Quick Start

```bash
# 1. Set API key
echo "AGNES_API_KEY=*** >> ~/.hermes/.env

# 2. Configure Hermes auxiliary.vision:
#    provider: openai
#    model: agnes-2.0-flash
#    base_url: http://localhost:8899/v1

# 3. Start the proxy
python agnes-vision-proxy.py

# 4. Paste screenshots into Hermes as usual
```

### How It Works

```
Screenshot → Hermes (base64) → Proxy :8899 → 0x0.st upload → Public URL → Agnes API → Result
```

### Dependencies

- Python 3 (stdlib only, zero extra packages)
- curl
- 0x0.st (free image hosting)
- Agnes AI API Key ([free signup](https://platform.agnes-ai.com))

### Cost

Agnes 2.0 Flash: currently **$0/million tokens** (both input and output). 0x0.st: free.

---

MIT License
