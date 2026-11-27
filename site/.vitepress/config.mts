import { defineConfig } from 'vitepress'

const repo = 'https://github.com/128-bit-net/pak256'

export default defineConfig({
  lang: 'ja-JP',
  title: 'pak256.LongScale',
  description: 'Simutrans の 256px タイルの pak セット pak256.LongScale の説明書',
  // GitHub Pages のプロジェクトサイト（https://128-bit-net.github.io/pak256/）で配信する。
  base: '/pak256/',
  cleanUrls: true,
  themeConfig: {
    nav: [
      { text: '導入方法', link: '/install' },
      { text: 'ダウンロード', link: `${repo}/releases/latest` },
    ],
    sidebar: [
      { text: 'pak256.LongScale とは', link: '/' },
      { text: '導入方法', link: '/install' },
    ],
    socialLinks: [{ icon: 'github', link: repo }],
    editLink: {
      pattern: `${repo}/edit/main/site/:path`,
      text: 'このページを GitHub で編集する',
    },
    search: {
      provider: 'local',
      options: {
        translations: {
          button: { buttonText: '検索', buttonAriaLabel: '検索' },
          modal: {
            displayDetails: '詳しく表示する',
            noResultsText: '見つかりませんでした',
            resetButtonTitle: '消す',
            backButtonTitle: '戻る',
            footer: { selectText: '開く', navigateText: '移動', closeText: '閉じる' },
          },
        },
      },
    },
    outline: { level: [2, 3], label: 'このページの目次' },
    docFooter: { prev: '前のページ', next: '次のページ' },
    darkModeSwitchLabel: '表示',
    lightModeSwitchTitle: '明るい表示にする',
    darkModeSwitchTitle: '暗い表示にする',
    sidebarMenuLabel: 'メニュー',
    returnToTopLabel: '先頭へ戻る',
    skipToContentLabel: '本文へ移る',
    notFound: {
      title: 'ページが見つかりません',
      quote: 'このアドレスのページはありません。',
      linkLabel: '最初のページへ',
      linkText: '最初のページへ',
    },
    externalLinkIcon: true,
  },
})
