# 地面一式（温帯）をゲームで確かめた記録（2026-11-25）

[#5](https://github.com/128-bit-net/pak256/issues/5) の地面を、OTRP v64（`sim-WinGDI64-OTRPv64.exe`）で確かめた。寸法と本体の読み方は [ground.md](../ground.md)。

## 手順

1. `python -X utf8 tools/build.py --no-ami` で `ground.Outside.pak`・`ground.temperate.pak` を組む。
2. 検証用に 手元の検証環境（`addon_check`）を写した作業フォルダ（`-set_workdir`）の `pak/` に、`work/pak256poc`（2 倍にした pak128）から地面の物（`ground.Outside.pak`・`landscape.grounds.all.pak`）を除いたものを入れ、上の 2 つを足した。`landscape.grounds.all.pak` の中の `Sidewalk`・`TunnelTexture`（`misc`）は本体が無いと止まるので、`work/src/landscape/grounds` の `sidewalk.dat` だけを別に組んで足した。地面の物以外は #5 の範囲外（pak128 由来の借り物）。
3. pak の `config/simuconf.tab` は `tile_height = 8`（`work/pak256poc/config` の写し）。AMI の 256 版は `work/ami256` の試しの pak。
4. 本体は `-objects pak/ -load flat -freeplay -mute -mcp-port 47860 -screensize 1500x950` で起動。保存データは `flat_512_left_v64.sve`（平らな 512 四方）。送信用の記録（`settings.xml`）は空にした。
5. 地形はスクリプト（このフォルダの `terrain_all.nut`・`rail.nut`・`cliff.nut`）で作った: 丘（単段の坂、座標 232〜241）、複段の坂の丘（222〜229）、湖（256〜267、水位を 2 回上げて海岸の斜面を出す）、線路（AMI の `ami_rail_ballast`）、1 段高い台地（300〜303。壁と柵）。
6. 画面は `gui.set_zoom(2)`・`gui.jump` と MCP の `capture_screen`。ツールバーとステータスバーは切り落とした。

## 画像

| 画像 | 見所（地図の座標） |
|---|---|
| `1_flat-slope.png` | 平地・単段の坂・台地（237,237） |
| `2_double-slope.png` | 複段の坂（226,236） |
| `3_coast-water.png` | 海岸の斜面と水（259,237） |
| `4_lake.png` | 湖の全景（262,239） |
| `5_wall-fence.png` | 壁と柵（302,302）。周りは雪（arctic の仮の色） |
| `6_map-edge.png` | 地図の端の壁と地図の外（511,511） |
| `7_ami-rail-on-slope.png` | AMI の 256 版の線路が坂に合う（232,236） |

## 分かったこと

- 本体は、起動のときに `ground.Outside.pak` というファイルを探す。別のフォルダにしないと pak の名前が合わない。
- 水は、深さごとの行にそれぞれ全コマが要る（無いと動かない）。
- 保存データは平らな地図の `groundwater = -2` で、ノードを下げられるのは -5 まで。水は、水位を上げる道具（`tool_change_water_height`）で入れる。

## 確かめていないこと

- `Marker`・`Basement` のゲーム内の見た目（絵の比較だけ）。
- 新しく生成した地図での起動（起動の最初の画面が必ず出るので、MCP から進められなかった）。保存データを読んで地形を作った。
- 非温帯の気候（仮の色）、雪線の遷移。
- CI（Linux 版 makeobj）。
