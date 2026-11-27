import type { MarkdownRenderer } from 'vitepress'

// 本文の `#RRGGBB` のコードの前に、その色の四角（見本）を付ける。色の値は md に 1 回だけ書く。
export function colorChips(md: MarkdownRenderer) {
  const render = md.renderer.rules.code_inline!
  md.renderer.rules.code_inline = (tokens, idx, options, env, self) => {
    const code = render(tokens, idx, options, env, self)
    const color = tokens[idx].content
    if (!/^#[0-9A-Fa-f]{6}$/.test(color)) return code
    return `<span class="color-chip"><span class="color-chip-box" style="background-color:${color}" aria-hidden="true"></span>${code}</span>`
  }
}
