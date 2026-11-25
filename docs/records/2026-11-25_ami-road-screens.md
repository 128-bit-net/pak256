# AMI の 256 版の道路をゲームで確かめた記録（2026-11-25）

[#7](https://github.com/128-bit-net/pak256/issues/7) で同梱した AMI の 256 版（`ami-256-alpha.1`、`ami_road.pak` だけ）で、街が AMI の道路で建つことを OTRP v64（`sim-WinGDI64-OTRPv64.exe`）で確かめた。

## 手順

1. `python -X utf8 tools/build.py` で組む。AMI は Release の zip から取り、SHA-256 が合った。makeobj のログに `Warning`・`ERROR` は無い。
2. 検証環境（`addon_check`）の実行ファイル・`themes/`・`font/`・`text/`・`script/` などを写した作業フォルダ（`-set_workdir`）に、`work/pak256poc`（2 倍にした pak128）から GUI・地面・道路（`infrastructure.roads`）を除いたものと、自前の pak と `ami_road.pak` を入れた。道路は AMI だけにするため、借り物の道路を外した。`config/*.tab` は `pak/config/` に置いた。`settings.xml` は `settings.xml.v64` の写しで、送信用の記録は中身を空にした。
3. `-objects pak/ -noaddons -load flat_512_left_v64.sve -freeplay -mute -mcp-port 47880 -screensize 1700x950` で起動し、MCP の `run_squirrel` で `tool_add_city` を 2 回使って街を置いた。

## 結果

- 街の道路は `ami_road_local`（`square_x(x,y).get_ground_tile().find_object(mo_way)` で道路の名前を数えた。街の道路 4 タイルすべて）。街の最初の家も道路に沿って建った。
- 画像 `2026-11-25_ami-road-screens/1_city-road.png`: 街「竹原」（座標 100,100）、1930 年、拡大 3。役場の前の道が AMI の生活道路。役場・家・木は借り物。
- 起動のログに `ami_road.pak` の読み込みの誤りは無い（`symbol.BigLogo.pak` が無いという行は、`pak/` に無いファイルを本体が試すだけで、いつものこと）。

## `ami_road_general` が無いときの本体の動き（本体のコード）

- `settings.cc` の `get_timeline_road_type`: 名前の道路が無ければ飛ばす。全部無ければ `NULL`。
- 街の道路（`city_road[0]` は `ami_road_local` なので影響しない）。`NULL` のときは `recalc_average_speed` が `weg_search(road_wt,50,…)`、街どうしは `distribute_cities` が `weg_search(road_wt,80,…)` で代わりにする。`ami_road_local` は 40km/h なので、AMI だけの pak ではこれが選ばれる。
- 止まらないので `simuconf.tab` の道路の行は直さない。`ami_road_general` が入れば 1930 年から自動で使われる。

## 確かめていないこと

- 街どうしの道路（`intercity_road`）は、新しい地図を作るときにしか引かれず、保存データを読んだ後は動かせないので、実際には見ていない。上のコードの読みだけ。
- 街の成長（本体の時間が遅く、数分では家 2 軒まで）。道路の太さ・家との並びの見た目。
- 借り物の pak（2 倍にした pak128）と混ぜているので、自前の物だけの見た目ではない。
