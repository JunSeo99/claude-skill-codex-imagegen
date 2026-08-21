# claude-skill-codex-imagegen

**[Claude Code](https://docs.claude.com/en/docs/claude-code) 안에서 OpenAI의 [gpt-image-2](https://developers.openai.com/api/docs/models/gpt-image-2) — 가장 강력한 이미지 생성 모델 — 를 그대로 사용하세요.**

🌐 [English](./README.md) · **한국어** · [日本語](./README.ja.md) · [简体中文](./README.zh-CN.md)

---

### 📦 무엇 (What)

자연어 요청 — *"히어로 이미지 만들어줘"*, *"파비콘 생성"*, *"사이트에 어울리는 이미지들 삽입해줘"* — 만으로 Codex CLI의 `$imagegen` (gpt-image-2) 을 호출하고, 결과 파일을 원하는 경로에 정확히 저장해주는 Claude Code 스킬입니다. 외울 슬래시 커맨드도, 새 CLI도 없습니다. Claude가 작업 중 알아서 호출합니다.

### 💡 왜 (Why)

Claude Code에는 자체 이미지 모델이 없습니다. 그래서 대부분의 "바이브 코딩"된 사이트는 이미지 없이 출시되거나, 사이트 톤과 맞지 않는 스톡 사진을 끼워 넣게 됩니다. 게다가 1년 전만 해도 생성된 이미지는 레이아웃보다 더 "AI 느낌"을 강하게 풍겼기 때문에 다들 시도 자체를 포기했죠. **gpt-image-2가 그 기준을 드디어 넘었습니다** — 텍스트 렌더링 거의 완벽, 일관된 조명, 의도된 구도. 그래서 *이미지 레이어*가 "AI로 만든 사이트들이 다 똑같이 생기는" 함정에서 빠져나오는 가장 싼 출구가 되었습니다.

이 스킬은 그 작업을 **세션 중 자동으로 일어나는 한 단계**로 만듭니다. 프로젝트 루트에 `DESIGN.md` 를 두면 일관된 톤의 이미지 세트를 사이트 전체에 자동 배치해 줍니다.

특히 **디자이너 없이 혼자 개발하는 사람**에게 가장 큰 차이를 만들어 줍니다.

### 🚀 빠른 시작

```bash
npx skills add https://github.com/JunSeo99/claude-skill-codex-imagegen \
  --skill codex-imagegen
```

새 Claude Code 세션을 시작한 뒤 자연어로 요청:

> *"이 랜딩 페이지에 어울리는 1600×900 히어로 이미지 만들어서 assets/hero.png 에 저장해줘."*

전체 사이트에 일관된 비주얼이 필요하다면, 프로젝트 루트에 `DESIGN.md` (팔레트 · 타이포 · 일러스트 스타일) 를 두고:

> *"DESIGN.md를 참고하여, 웹사이트에 어울리는 이미지들을 삽입해줘."*

이게 전부입니다. 나머지는 스킬이 알아서 처리합니다.

---

## 더 자세한 내용

세부 사항(설치 옵션, 격리된 실행 방식, Codex 에이전트의 프롬프트 재가공 구조와 네이티브 스키마, 투명 배경 네이티브 알파 생성·픽셀 검증, 사이즈 규칙, 보안, 알려진 한계, 비교 데모)은 **[영문 README](./README.md)** 에 정리되어 있습니다.

## 라이선스

[MIT](LICENSE) © 2026 JunSeo99
