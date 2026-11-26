// 地図の拡大の窓・気候の窓の部品を探して押す（#158。river_run.py が使う）。MIT License。
// 座標は窓の部品の画面上の位置から取る（gui.get_window_components）。先頭で WHAT・N を定義して流す。
// 日本語の文字列リテラルは本体に化けて届くので使わない。拡大の窓は "enlarge map" のボタンがある窓、気候の窓はそれ以外の窓。
// WHAT = "size": 拡大の窓の X・Y を 1 段ずつ増やす。"climate": 気候の窓を開く。"rivers": 河川の数を N 回増やす。"start": 拡大する。
local list = [];
local walk;
walk = function(c) {
	list.append(c);
	foreach (k in c.children) walk(k);
};
local has_text = function(t) { foreach (c in list) if ("text" in c && c.text == t) return c; return null; };
local pick = function(is_enlarge) {
	foreach (w in gui.get_windows()) {
		list.clear();
		foreach (c in gui.get_window_components(w.id)) walk(c);
		if ((has_text("enlarge map") != null) == is_enlarge) return true;
	}
	return false;
};
// 数の入力欄（高さ 22・幅 100 未満の部品）。右端の三角が「増やす」
local inputs = function() { local out = []; foreach (c in list) if (c.role == "unknown" && c.screen_bounds.h == 22 && c.screen_bounds.w < 100) out.append(c); return out; };
local up = function(c) { local b = c.screen_bounds; gui.click(b.x + b.w - 6, b.y + b.h / 2); };
local button = function(c) { local b = c.screen_bounds; gui.click(b.x + b.w / 2, b.y + b.h / 2); };
if (WHAT == "size" || WHAT == "start" || WHAT == "climate") {
	if (!pick(true)) return "no enlarge window";
	if (WHAT == "size") { local in_ = inputs(); up(in_[0]); up(in_[1]); return "size"; }
	button(has_text(WHAT == "start" ? "enlarge map" : "Climate Control"));
	return WHAT;
}
if (!pick(false)) return "no climate window";
local in_ = inputs(); // 気候の窓の下の 4 つは、湖面水位・河川の数・最短長・最大長
if (in_.len() < 4) return "no river count";
for (local i = 0; i < N; i++) up(in_[in_.len() - 3]);
return "rivers";
