gui.close_all_windows();
local cx = 235, cy = 235;
local out = "";
local cnt = {};
for (local y = cy-16; y <= cy+16; y++) {
  for (local x = cx-16; x <= cx+16; x++) {
    local t = square_x(x,y).get_ground_tile();
    local c = ".";
    local b = t.find_object(mo_building);
    if (b != null) { local n = b.get_desc().get_name(); if (!(n in cnt)) cnt[n] <- 0; cnt[n]++; c = (n.find("townhall")!=null) ? "T" : "H"; }
    else if (t.has_way(wt_road)) c = "s";
    else if (t.find_object(mo_tree) != null) c = "t";
    out += c;
  }
  out += "\n";
}
local s = "";
foreach (k, v in cnt) s += k + "=" + v + " ";
local tm = world.get_time();
local ci = ""; foreach (c in city_list_x()) ci += " citizens=" + c.get_citizens()[0];
return "yr=" + tm.year + " mo=" + tm.month + ci + " " + s + "\n" + out;
