import { defineConfig } from 'vitepress'
import { colorChips } from './color-chips'

const repo = 'https://github.com/128-bit-net/pak256'

export default defineConfig({
  lang: 'ja-JP',
  title: 'pak256.LongScale',
  description: 'Simutrans の 256px タイルの pak セット pak256.LongScale の説明書',
  // GitHub Pages のプロジェクトサイト（https://128-bit-net.github.io/pak256/）で配信する。
  base: '/pak256/',
  cleanUrls: true,
  markdown: { config: colorChips },
  themeConfig: {
    nav: [
      { text: '導入方法', link: '/install' },
      { text: 'アドオン作者向けの仕様', link: '/spec/' },
      { text: 'ダウンロード', link: `${repo}/releases/latest` },
    ],
    sidebar: [
      { text: 'pak256.LongScale とは', link: '/' },
      { text: '導入方法', link: '/install' },
      {
        text: 'アドオン作者向けの仕様',
        items: [
          { text: '入口', link: '/spec/' },
          { text: '縮尺と大きさ', link: '/spec/scale' },
          { text: 'タイルとセル', link: '/spec/tile-and-cell' },
          { text: '絵の共通の決まり', link: '/spec/drawing' },
          { text: 'dat の共通のキー', link: '/spec/dat' },
        ],
      },
      {
        // 物の種類ごとのページ。書いたら link を足す（#177 の構成の順）。
        text: '種類ごと',
        items: [
          { text: '車両の大きさ', link: '/spec/vehicle-size' },
          { text: '線路の車両', link: '/spec/vehicle-rail' },
          { text: '道路の車両', link: '/spec/vehicle-road' },
          { text: '街の車', link: '/spec/citycar' },
          { text: '歩行者', link: '/spec/pedestrian' },
          { text: '駅・停留所', link: '/spec/station' },
          { text: '信号', link: '/spec/signal' },
          { text: '船・港', link: '/spec/ship' },
          { text: '飛行機・空港', link: '/spec/air' },
          { text: '川', link: '/spec/river' },
          { text: '建物・産業・貨物' },
          { text: '木と地面' },
          { text: 'GUI の絵' },
          { text: '煙と音' },
        ],
      },
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
