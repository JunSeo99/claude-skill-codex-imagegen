# Codex Imagegen

### 在 Claude Code 中生成图片、比较方案、修改细节。

**图片在后台生成，代码继续写。** 使用现有的 Codex 订阅，无需图片 API 密钥，也没有额外的 API 账单。

[English](README.md) · [한국어](README.ko.md) · [日本語](README.ja.md) · **简体中文**

```bash
npx skills add https://github.com/JunSeo99/claude-skill-codex-imagegen --skill codex-imagegen
```

| 摄影方案 | 纸艺插画 | 修改选中的图片 |
|:---:|:---:|:---:|
| ![石灰石上的陶杯](assets/demo/a-studio.png) | ![纸艺质感的陶杯](assets/demo/b-paper.png) | ![改为绿色的陶杯](assets/demo/a-studio-v2.png) |

这些图片由仓库自带的启动器实际生成。[提示词和验证记录](docs/validation.md)均可查看。图片模型由 Codex 管理，因此我们不将这些结果标注为某个特定模型的输出。

## 用自然语言开始

| 目标 | 示例 |
|---|---|
| 直接生成 | “为这个页面生成一张主视觉。” |
| 明确方向 | “我还没想好，先简短地问我几个问题。” |
| 比较方案 | “给我三个明显不同的方向。” |
| 局部修改 | “选第二张，只改背景。” |
| 透明图片 | “把商品做成透明 PNG。” |
| 并行工作 | “图片生成期间继续完成 UI。” |

需求清晰就直接执行，只在需要时访谈。每个方案保存为独立图片；修改时保留原图，并明确哪些内容改变、哪些需要保持。

## 安装要求

macOS/Linux、Python 3.9+、Claude Code，以及已登录的 Codex CLI 0.153.4+。

```bash
npm install -g @openai/codex
codex login
```

安装技能后打开新的 Claude Code 会话即可。可以指定 `DESIGN.md`、参考图片和保存路径。手动安装时，将 `skill/` 复制到 `~/.claude/skills/codex-imagegen/`。通过 Skills CLI 安装后可用 `npx skills update` 更新。

## 后台与并行生成

独立的 Python 工作进程负责等待 Codex，立即向 Claude 返回任务信息。默认同时运行两个生成任务，最多四个。PNG、对比用 HTML、状态文件和日志都保存在本地。状态查询不会调用 Codex。失败后检查错误再恢复，已经完成的图片不会重新生成。电脑需要保持运行；部分宿主环境可能需要自己的后台任务机制。

```bash
python3 skill/scripts/image_project.py --prompt-file brief.txt --out-dir output/hero-v1 --background
python3 skill/scripts/image_project.py --out-dir output/hero-v1 --status
```

提示词以 `$imagegen` 开头。多个方案可用 `--plan` 传入[JSON 计划](tests/prompts/demo/plan.json)。

## 精简上下文，明确能力边界

Claude 负责访谈、构思与检查；Codex 只接收完成后的简短图片指令。默认中继模型为 `gpt-5.6-luna`，推理设为 `none`，省去通用编码指令和技能目录。[验证记录](docs/validation.md)中的上下文缩减不代表总 token 或成本同比例下降。

官方将 [Flare](https://developers.openai.com/api/docs/models/gpt-image-2.5-flare)定位为快速日常生成，将 [Sunburst](https://developers.openai.com/api/docs/models/gpt-image-2.5-sunburst)定位为高质量生成与精细编辑。但**当前订阅路径无法固定选择这两个模型**。`--model` 设置的是文本中继模型，不是图片模型。没有切换到付费图片 API 的路径。

透明 PNG 会检查真实的 alpha 像素。Claude 会查看文字、形状和非预期变化；生成式编辑不保证其他区域像素完全不变。

[完整文档（英文）](README.md) · [更新日志](CHANGELOG.md) · [安全说明](SECURITY.md) · [MIT](LICENSE)

如果这个技能对你有用，欢迎 Star 保存并关注后续版本。本项目独立于 Anthropic 和 OpenAI。
