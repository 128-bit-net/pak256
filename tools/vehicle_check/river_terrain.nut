// 川の確かめの地形（docs/records の川の記録・#158）。MIT License。
// flat_512_left_v64（平らな地図）に、南東の海と丘の群れを作る。この後に地図の拡大（Games の窓。河川の数を指定）を
// すると、丘から海へ川が引かれる。地形は公共のプレーヤーで作る。長くなるので、行を分けて流す。
// 先頭で STEP を定義して流す: STEP=0 は海（Y0 から Y0+19 の行）、STEP=1 は丘（HILL 番目）。
local pu = player_x(1);
if (STEP == 0) {
	// 地面を地下水位（-2）まで掘る。水は STEP=2 で入れる（掘るだけでは水にならない）
	for (local y = Y0; y < Y0 + 20; y++)
		for (local x = 190; x <= 235; x++)
			for (local i = 0; i < 2 && square_x(x, y).get_ground_tile().z > -2; i++) command_x.grid_lower(pu, coord3d(x, y, 0));
	return "sea " + Y0;
}
if (STEP == 2) {
	local g = square_x(212, 200).get_ground_tile();
	local r = command_x(tool_change_water_height).work(pu, coord3d(212, 200, g.z), "1");
	g = square_x(212, 200).get_ground_tile();
	return "water=[" + r + "] z=" + g.z + " water=" + g.is_water();
}
// 丘: [中心 x, 中心 y, 高さ]。中心を高さの回数だけ上げると、裾の広い角すいになる
local hills = [[64, 120, 10], [96, 160, 8], [48, 200, 9], [120, 110, 7], [140, 190, 10], [80, 250, 8],
               [150, 260, 9], [112, 220, 6], [40, 300, 10], [100, 310, 7], [170, 140, 6], [70, 80, 8]];
local h = hills[HILL];
for (local i = 0; i < h[2]; i++) command_x.grid_raise(pu, coord3d(h[0], h[1], i));
return "hill " + HILL + " top=" + square_x(h[0], h[1]).get_ground_tile().z;
