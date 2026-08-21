# claude-skill-codex-imagegen

**在 [Claude Code](https://docs.claude.com/en/docs/claude-code) 中直接使用 OpenAI 的 [gpt-image-2](https://developers.openai.com/api/docs/models/gpt-image-2) — 目前最强大的图像生成模型。**

🌐 [English](./README.md) · [한국어](./README.ko.md) · [日本語](./README.ja.md) · **简体中文**

---

### 📦 What

一个 Claude Code 技能(skill),通过自然语言请求 — *"生成一张主视觉图"*、*"做一个 favicon"*、*"为网站插入合适的图片"* — 即可调用 Codex CLI 的 `$imagegen`(gpt-image-2),并把结果文件精确保存到你想要的位置。不需要记新的斜杠命令。Claude 在工作过程中自然调用。

### 💡 Why

Claude Code 本身没有内置图像模型。所以大多数"氛围编码"出来的网站要么发布时没有图片,要么硬塞与网站调性不符的库存图。而且一年前,生成图比布局更明显地透露出"AI 味",大家因此放弃尝试。**gpt-image-2 终于跨过了这个门槛** — 文本渲染接近完美、光照一致、主体构图有意图。这让 *图像层* 成为摆脱"所有 AI 生成的网站都长得一样"陷阱最便宜的出口。

这个技能把这件事变成 **会话中自动发生的一步**。在项目根目录放一个 `DESIGN.md`,它就会为整个网站自动布置风格一致的图像集合。

对 **没有设计师、一个人独立开发** 的开发者影响最大。

### 🚀 快速开始

```bash
npx skills add https://github.com/JunSeo99/claude-skill-codex-imagegen \
  --skill codex-imagegen
```

启动新的 Claude Code 会话,然后用自然语言:

> *"为这个 landing page 生成一张 1600×900 的主视觉图,保存到 assets/hero.png。"*

如果需要整站视觉一致,在项目根目录放一个 `DESIGN.md`(调色板·字体·插画风格),然后:

> *"以 DESIGN.md 作为风格参考,为网站插入合适的图片。"*

就这些。其余的交给技能处理。

---

## 更多信息

完整细节(安装方式、隔离执行方式、Codex 代理的 prompt 重构机制与原生 schema、透明背景原生 Alpha 生成与像素验证、尺寸规则、安全、已知限制、对比 demo)请见 **[英文 README](./README.md)**。

## 许可证

[MIT](LICENSE) © 2026 JunSeo99
