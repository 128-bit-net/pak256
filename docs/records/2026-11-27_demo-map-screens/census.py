"""地面の物を種類と名前ごとに数える（pak の版の違いで demo.sve の物が欠けないかを比べる）。MIT License。

使い方（リポジトリの直下から。環境の写しの save/ に demo.sve を置く。出力は work/79/census_<札>.txt）:
    python -X utf8 docs/records/2026-11-27_demo-map-screens/census.py <環境の写し> <ポート> <作業フォルダ> <build> <root> <札>
"""
import collections
import os
import sys

sys.path.insert(0, "tools")
import game  # noqa: E402

os.makedirs("work/79", exist_ok=True)
env, port, work, build, root, tag = sys.argv[1], int(sys.argv[2]), sys.argv[3], sys.argv[4], sys.argv[5], sys.argv[6]

# 地面（kartenboden）の物の (種類, 名前) を数える。列の帯ごとに分ける。
CENSUS = ('local n={}; for (local x=__A__; x<__B__; x++) for (local y=0; y<256; y++) { '
          'local t=square_x(x,y).get_ground_tile(); foreach (ob in t.get_objects()) { local ty=ob.get_type(); '
          'if (ty>=64) continue; local d="?"; try { d=ob.get_desc().get_name(); } catch(e) {} '
          'local k=ty+":"+d; if (k in n) n[k]++; else n[k]<-1; } } '
          'local s=""; foreach (k,v in n) s+=k+"="+v+";"; return s;')
STATS = ('local s=""; foreach (c in city_list_x()) s+=c.get_name()+"="+c.get_citizens()[0]+";"; '
         'foreach (f in factory_list_x()) s+=f.get_name()+";"; return s;')

with game.Game(env, "demo", port, work=work, build=build, root=root, rewrite_roads=False, keep=True) as g:
    total = collections.Counter()
    for a in range(0, 256, 32):
        out = g.sq(CENSUS.replace("__A__", str(a)).replace("__B__", str(a + 32)), timeout=120)
        for item in out.split(";"):
            if item:
                k, v = item.rsplit("=", 1)
                total[k] += int(v)
    with open(f"work/79/census_{tag}.txt", "w", encoding="utf-8") as f:
        for k in sorted(total):
            f.write(f"{k}={total[k]}\n")
        f.write(g.sq(STATS).replace(";", "\n"))
    print("done", len(total), sum(total.values()))
