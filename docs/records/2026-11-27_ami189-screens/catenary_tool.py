"""路面軌道の架線が、本体でどの種類の way-object として扱われるか（ツールバーの wayobjs(N) の N）と、架線の撤去の道具
（general_tool[33] の引数 2 = 線路）で消えるかを確かめる。MIT License。
使い方（リポジトリの直下で）: python -X utf8 docs/records/2026-11-27_ami189-screens/catenary_tool.py <検証環境> <ポート> <build のフォルダ>"""
import os
import sys

sys.path.insert(0, os.path.abspath("tools"))
from game import Game  # noqa: E402

env, port, build = sys.argv[1], int(sys.argv[2]), os.path.abspath(sys.argv[3])
with Game(env, "flat_512_left_v64", port, build=build) as g:
    for wt in ("wt_rail", "wt_tram"):
        print(wt, g.sq(f'local s=""; foreach (d in wayobj_desc_x.get_available_wayobjs({wt})) if (d.get_name().find("ami_tram") == 0) s += d.get_name()+" "; return s'), flush=True)
    a, b = "coord3d(60,60,0)", "coord3d(66,60,0)"
    has = "return \"\" + (tile_x(63,60,0).find_object(mo_wayobj) != null)"
    print("way", g.sq(f'return command_x(tool_build_way).work(player_x(0), {a}, {b}, "ami_tram")'))
    print("build", g.sq(f'return command_x.build_wayobj(player_x(0), {a}, {b}, wayobj_desc_x("ami_tram_catenary"))'), g.sq(has))
    print("remove", g.sq(f'return command_x(tool_remove_wayobj).work(player_x(0), {a}, {b}, "2")'), g.sq(has), flush=True)
    if g.left_over:
        sys.exit(1)
