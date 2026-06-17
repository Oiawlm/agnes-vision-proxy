---
name: agnes-vision-proxy
description: 本地代理，自动将 Hermes 发出的 base64 图片上传 0x0.st 换取公网 URL，再转发给 Agnes 2.0 Flash 视觉模型（Agnes 只接受公网 URL，不吃 base64）。
version: 1.0.0
metadata:
  hermes:
    tags: [vision, proxy, agnes, image, base64, free]
    related_skills: [hermes-config-scripting]
---

# Agnes 视觉代理

## 解决什么问题

Hermes 发图片给视觉模型时用的是 base64 编码（`data:image/png;base64,...`）。
Agnes 2.0 Flash 只接受公网 HTTP URL（`https://example.com/image.png`），不吃 base64。

这个代理坐在 Hermes 和 Agnes 之间，自动把 base64 图片上传到 0x0.st 免费图床，换成公网 URL 再转发。

## 前置条件

- Python 3（系统自带够用，不需要额外装包）
- curl（Windows Git Bash 自带）
- Agnes AI API Key（免费注册 https://platform.agnes-ai.com）
- 网络能访问 0x0.st 和 apihub.agnes-ai.com

## 安装

代理脚本：`D:\App\agnes-vision-proxy.py`

```bash
# 1. 写入 API Key 到 Hermes .env
echo "AGNES_API_KEY=*** >> ~/AppData/Local/hermes/.env

# 2. 修改 Hermes config.yaml 的 auxiliary.vision
#    model: agnes-2.0-flash
#    base_url: http://localhost:8899/v1
#    provider: openai
```

**改 config.yaml 前先备份：**
```bash
cp ~/AppData/Local/hermes/config.yaml ~/AppData/Local/hermes/config.yaml.bak
```

## 使用

```bash
# 启动代理
python D:\App\agnes-vision-proxy.py
# 看到 "[proxy] 等待请求..." 就就绪
```

然后正常用 Hermes，截图粘贴即可。代理在后台自动转换。

**不需要视觉时关掉代理就行**——主模型不受影响。

## 工作原理

```
你截图 → Hermes (base64) → 代理:8899 → 0x0.st (上传) → 拿公网URL → Agnes API → 返回描述
```

- 代理只拦截 `image_url` 里带 `data:` 前缀的 base64 图片
- 文本消息和普通 URL 图片直接透传
- 0x0.st 免费，512MB 上限，文件保留 30 天+

## 故障排查

**代理启动失败 "AGNES_API_KEY 未设置"**
→ 检查 `~/AppData/Local/hermes/.env` 里有没有 `AGNES_API_KEY=***`

**图片上传失败**
→ 0x0.st 可能暂时不可用。代理会保留原始 base64 继续请求（Agnes 大概率报错，但不会丢数据）

**视觉返回 400**
→ 检查 API Key 是否有效，是否还有免费额度

## 成本

Agnes 2.0 Flash 当前完全免费（$0/百万 token）。0x0.st 免费。
唯一开销：图片上传占一点带宽。

## 文件

- 代理脚本：`D:\App\agnes-vision-proxy.py`
- Hermes 配置：`auxiliary.vision` 指向 `http://localhost:8899/v1`
