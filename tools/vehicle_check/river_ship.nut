// 引かれた川を船が通れるかの確かめ（#158）。river_run.py の terrain・enlarge の後に流す。MIT License。
// 海に接する川の升から川をたどって、いちばん遠い平らな行き止まり（源）を探す。源に車庫、その手前の直線の升に船着き場、
// 海の升を行き先にして、旅客船を川で往復させる。戻り値に、置けたかと座標を返す。
// 川を引いた直後の回では、河口の海の升が川につながらず NO_ROUTE になる。保存して読み直すと走り出す（記録の「船が通れた」）。
local pu = player_x(1), pl = player_x(0);
local DIRS = [[1, 0, -1], [2, 1, 0], [4, 0, 1], [8, -1, 0]]; // ribi と隣の升
local size = world.get_size();
local get = function(x, y) {
	local g = square_x(x, y).get_ground_tile();
	return g.get_way(wt_water) == null ? null : g;
};
local best = null;
local seen = {};
for (local y = 99; y < 321; y++) {
	for (local x = 188; x < 238; x++) {
		local g = get(x, y);
		if (g == null) continue;
		local sea = null;
		foreach (d in DIRS) {
			local q = square_x(x + d[1], y + d[2]).get_ground_tile();
			if (q.is_water() && (g.get_way_dirs(wt_water) & d[0])) sea = q;
		}
		if (sea == null) continue;
		// 幅優先で上流へ
		local queue = [[x, y, [[x, y]]]];
		local visited = { [x + "," + y] = true };
		for (local head = 0; head < queue.len(); head++) {
			local c = queue[head];
			local cg = square_x(c[0], c[1]).get_ground_tile();
			local dirs = cg.get_way_dirs(wt_water);
			if (head > 0 && cg.get_slope() == 0 && (dirs == 1 || dirs == 2 || dirs == 4 || dirs == 8) && (best == null || c[2].len() > best.path.len()))
				best = { path = c[2], sea = sea };
			foreach (d in DIRS) {
				local nx = c[0] + d[1], ny = c[1] + d[2];
				if (!(dirs & d[0]) || nx < 0 || ny < 0 || nx >= size.x || ny >= size.y) continue;
				if ((nx + "," + ny) in visited || get(nx, ny) == null) continue;
				visited[nx + "," + ny] <- true;
				local path = clone c[2];
				path.append([nx, ny]);
				queue.append([nx, ny, path]);
			}
		}
	}
}
if (best == null) return "no river to the sea";
local path = best.path;
local tile = function(p) { return square_x(p[0], p[1]).get_ground_tile(); };
local out = "len=" + path.len() + " mouth=" + path[0][0] + "," + path[0][1] + " spring=" + path[path.len() - 1][0] + "," + path[path.len() - 1][1];
local widths = {};
foreach (p in path) { local n = tile(p).get_way(wt_water).get_desc().get_name(); if (!(n in widths)) widths[n] <- 0; widths[n]++; }
foreach (k, v in widths) out += " " + k + "=" + v;
local slopes = 0; foreach (p in path) if (tile(p).get_slope() != 0) slopes++;
out += " slopes=" + slopes;
local depot_desc = null;
foreach (d in building_desc_x.get_building_list(building_desc_x.depot)) if (d.get_name() == "ami_canal_depot") depot_desc = d;
local sp = path[path.len() - 1];
local g = tile(sp);
out += " depot=[" + command_x.build_depot(pl, coord3d(sp[0], sp[1], g.z), depot_desc) + "]";
// 船着き場: 源から下流へ見て、平らな直線の升
local wharf = null;
for (local i = path.len() - 4; i > 3 && wharf == null; i--) {
	local t = tile(path[i]);
	local d = t.get_way_dirs(wt_water);
	if (t.get_slope() == 0 && (d == 5 || d == 10)) {
		local r = command_x(tool_build_station).work(pl, coord3d(path[i][0], path[i][1], t.z), "pak256_canal_wharf");
		if (r == null) wharf = path[i];
		else out += " wharf?[" + r + "]";
	}
}
if (wharf == null) return out + " no wharf";
local w = tile(wharf);
local s = best.sea;
out += " wharf=" + wharf[0] + "," + wharf[1] + "," + w.z + " sea=" + s.x + "," + s.y + "," + s.z;
local ferry = null;
foreach (v in vehicle_desc_x.get_available_vehicles(wt_water)) if (v.get_name() == "pak256_ferry") ferry = v;
local depot = depot_x(sp[0], sp[1], g.z);
depot.append_vehicle(pl, convoy_x(0), ferry);
local list = depot.get_convoy_list();
local cnv = list[list.len() - 1];
cnv.change_schedule(pl, schedule_x(wt_water, [schedule_entry_x(coord3d(s.x, s.y, s.z), 0, 0), schedule_entry_x(coord3d(wharf[0], wharf[1], w.z), 0, 0)]));
depot.start_convoy(pl, cnv);
return out + " started";
