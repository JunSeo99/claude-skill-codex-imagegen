# Codex Imagegen

### Claude Codeで、画像を作り、選び、仕上げる。

**画像の生成中も、コーディングを続けられます。** 利用中のCodexサブスクリプションで動作し、画像APIキーや別途API料金は不要です。

[English](README.md) · [한국어](README.ko.md) · **日本語** · [简体中文](README.zh-CN.md)

```bash
npx skills add https://github.com/JunSeo99/claude-skill-codex-imagegen --skill codex-imagegen
```

| 写真の方向性 | ペーパーイラスト | 選んだ画像を編集 |
|:---:|:---:|:---:|
| ![テラコッタのカップ](assets/demo/a-studio.png) | ![紙の質感のカップ](assets/demo/b-paper.png) | ![緑色に編集したカップ](assets/demo/a-studio-v2.png) |

付属ランチャーで実際に生成した画像です。[プロンプトと検証記録](docs/validation.md)を公開しています。画像モデルはCodexが管理するため、特定のモデルの出力とは表示していません。

## 自然な言葉で依頼

| 目的 | 依頼の例 |
|---|---|
| すぐに生成 | 「このページに合うヒーロー画像を作って」 |
| 方向性を相談 | 「まだ決まっていないので、短く質問して」 |
| 候補を比較 | 「違う方向性で3案見せて」 |
| 部分編集 | 「2番を使って、背景だけ変えて」 |
| 透過画像 | 「商品を透明なPNGにして」 |
| 並列作業 | 「画像を生成している間にUIを仕上げて」 |

明確な依頼にはすぐ着手します。必要なときだけ質問し、候補は別々の画像として保存します。編集は元画像を残し、変更したい部分と保つ部分を区別します。

## セットアップ

macOS/Linux、Python 3.9+、Claude Code、ログイン済みのCodex CLI 0.153.4+が必要です。

```bash
npm install -g @openai/codex
codex login
```

上のコマンドでスキルをインストールしたら、新しいClaude Codeセッションで依頼してください。`DESIGN.md`や参考画像を指定すると、見た目を揃えられます。手動なら`skill/`を`~/.claude/skills/codex-imagegen/`へコピーします。Skills CLIの更新は`npx skills update`です。

## バックグラウンド生成

分離したPythonワーカーがCodexの応答を待ち、Claudeにはジョブ情報をすぐ返します。同時実行は標準2件、最大4件。PNG、比較用HTML、状態、ログをローカル保存します。状態確認はCodexを呼びません。失敗後に確認して再開すると、完了済み画像は再生成しません。PCは起動している必要があり、ホストによっては専用のバックグラウンド実行機能が必要です。

```bash
python3 skill/scripts/image_project.py --prompt-file brief.txt --out-dir output/hero-v1 --background
python3 skill/scripts/image_project.py --out-dir output/hero-v1 --status
```

プロンプトの先頭は`$imagegen`です。複数案は[JSONプラン](tests/prompts/demo/plan.json)を`--plan`で指定します。

## 小さなコンテキスト、明確な対応範囲

Claudeが企画と確認を担当し、Codexには完成した短い指示だけを渡します。中継モデルは標準で`gpt-5.6-luna`、推論は`none`。一般的なコーディング指示とスキル一覧を省きます。[検証](docs/validation.md)で確認したコンテキスト削減は、総トークンや料金の削減率を保証するものではありません。

公式には[Flare](https://developers.openai.com/api/docs/models/gpt-image-2.5-flare)は速度重視、[Sunburst](https://developers.openai.com/api/docs/models/gpt-image-2.5-sunburst)は品質と精密な編集を重視します。ただし、**このサブスクリプション経路では両モデルを固定できません**。`--model`はテキスト中継モデルの設定です。有料APIへ切り替える経路はありません。

透過PNGは実際のアルファ値を検証します。文字、形状、意図しない変更はClaudeが画像を見て確認します。生成編集にピクセル単位の保持保証はありません。

[詳細（英語）](README.md) · [変更履歴](CHANGELOG.md) · [セキュリティ](SECURITY.md) · [MIT](LICENSE)

役に立ったら、Starで保存して今後のリリースもチェックしてください。Anthropic/OpenAIとは独立したプロジェクトです。
