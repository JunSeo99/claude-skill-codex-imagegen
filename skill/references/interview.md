# Interview only what changes the image

Use Claude Code's `AskUserQuestion` if available; otherwise ask one concise message
in the user's language. Bundle at most three questions with useful choices and a
recommended default. Do not ask about facts already provided or make users choose
model slugs, sampler settings, or CLI options.

Prioritize:
1. Use and audience: where will this appear, and what must viewers understand?
2. Art direction: two or three concrete alternatives suited to that purpose.
3. Hard constraints: exact wording, supplied brand/product reference, crop, or alpha.

For “카페 홍보 이미지 만들어줘, 뭐가 좋을지 모르겠어”:
- “주로 어디에 쓰나요?” Instagram square / wide website hero / printed poster.
- “어떤 느낌이 맞나요?” Warm product photo / bold graphic poster / hand-drawn scene.
- “반드시 들어갈 문구나 제품 사진이 있나요?” Only when the intended image needs them.

If the user asks for an interview, wait for their answer before image generation.
If a critical source image or exact required copy is missing, obtain it first.
For ordinary vague requests, use available context to make one reasonable image;
do not force an interview. “알아서”, “surprise me”, or “no questions” means decide
and proceed, noting only important assumptions. Do not invent brand facts.

Once direction is clear, translate answers into a compact brief and generate.
No second approval checkpoint unless the user requested one. If they want options,
offer distinct visual approaches; do not show three paraphrases of the same style.
