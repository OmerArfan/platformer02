local sub1 = {
	lvl1 = {
		-- Player init
		player = {
			x = 150, y = 600,
			spawn_x = 150, spawn_y = 600,
		},
		blocks = {
			{x = -1500, y = 906,  w = 900,  h = 100},
			{x = 100,   y = 750,  w = 2000, h = 900},
			{x = 100,   y = 300,  w = 2000, h = 50},
			{x = 100,   y = -150, w = 2200, h = 50},
			{x = -900,  y = -360, w = 1000, h = 9000},
			{x = 1220,  y = -425, w = 360,  h = 50},
		},
		jump_blocks = {
			{x = 950,  y = 700, w = 100, h = 50},
			{x = 2260, y = 750, w = 120, h = 120},
			{x = 2600, y = 285, w = 120, h = 120},
		},
		spikes = {
			{{900, 350}, {950, 400}, {1000, 350}},
			{{1000, 350}, {1050, 400}, {1100, 350}},
			{{2000, 750}, {2050, 700}, {2100, 750}},
		},
		saws = {
			{x = 620,  y = 750,  radius = 80, type = 'static' },
			{x = 1700, y = 325,  radius = 85, type = 'static' },
			{x = 1200, y = 325,  radius = 85, type = 'static' },
			{x = 800,  y = 325,  radius = 85, type = 'static' },
			{x = 1850, y = -170, radius = 80, type = 'static' },
			{x = 1550, y = -400, radius = 80, type = 'static' },
			{x = 1250, y = -400, radius = 80, type = 'static' },
			{x = 950,  y = -170, radius = 80, type = 'static' },
		},
		flags = {
			{x = 200,  y = 200,   w = 100, h = 125, save_x = 200,  save_y = 200},
			{x = 2080, y = -260,  w = 100, h = 125, save_x = 2080, save_y = -260},
		},
		key_block_pairs = {
			{
			key = {x = 250, y = 175, radius = 30, color = {255, 255, 0}},
			block = {x = 2550, y = 250, w = 200, h = 200},
			collected = false
			},
		},
		text = {
			saws = {name = "saws_message", fallback = "Saws are also dangerous!", color = {255, 0, 0}, x = 550, y = 600},
			key  = {name = "key_message", fallback = "Grab the coin and open the block!", color = {255, 255, 0}, x = 2500, y = 200},
		},
		exit = {x = 430, y = -350, w = 140, h = 180},
		next_page = "ship_1_lvl2",
	},

	lvl2 = {
		-- Player init
		player = {
			x = 250, y = 450,
			spawn_x = 250, spawn_y = 450,
		},
		blocks = {
			{x = 200,  y = 650, w = 650,  h = 100},
			{x = 1100, y = 510, w = 100,  h = 100},
			{x = 1450, y = 650, w = 650,  h = 100},
			{x = 2300, y = 230, w = 1000, h = 1800},
			{x = 2800, y = 400, w = 1200, h = 1600},
			{x = 2800, y = -370, w = 200, h = 400},
			{x = 3100, y = -300, w = 450, h = 100},
			{x = 3700, y = -100, w = 200, h = 100},
			{x = 4000, y = -370, w = 200, h = 400},
		},
		jump_blocks = {
			{x = 2200, y = 751, w = 100, h = 100},
			{x = 2400, y = 130, w = 120, h = 100},
		},
		spikes = {
			{{2000, 650}, {2050, 600}, {2100, 650}},
			{{3300, -300}, {3350, -350}, {3400, -300}},
			{{3800, 400}, {3850, 350}, {3900, 400}},
			{{3900, 400}, {3950, 350}, {4000, 400}},
		},
		moving_block = {
			{x = 4050, y = 450, w = 100, h = 50, axis = "x", direction = 1, speed = 2, min = 4050, max = 4350},
			{x = 4550, y = 450, w = 100, h = 50, axis = "x", direction = 1, speed = 3, min = 4550, max = 4850},
		},
		lasers = {
			{x = 3000, y = -50, w = 1000, h = 15},
		},
		saws = {
			{x = 650,  y = 630, radius = 70, type = 'static'},
			{x = 2520, y = 230, radius = 90, type = 'static'},
			{x = 4950, y = 150, radius = 100, type = 'static'},
			{x = 4950, y = 550, radius = 100, type = 'static'},
			{x = 4500, y = 425, radius = 60, type = 'static'},
			{radius = 40, orbit_radius = 230, angle = 0,   speed = 2, block = 1, type = 'rotating'},
			{radius = 40, orbit_radius = 230, angle = 180, speed = 2, block = 1, type = 'rotating'},	
			{radius = 80, speed = 5, x = 3800, y = -300, max = -50, min = -700, type = 'moving_y'},
		},
		flags = {
			{x = 1500, y = 550, w = 100, h = 125, save_x = 1500, save_y = 550},
			{x = 3200, y = 120, w = 100, h = 125, save_x = 3200, save_y = 120},
		},
		key_block_pairs = {
			{
			key = {x = 3800, y = -140, radius = 30, color = {255, 255, 0}},
			block = {x = 2800, y = 30, w = 200, h = 200},
			collected = false
			},
		},
		text = {
			saws = {name = "saws_message2", fallback = "Some saws rotate around a block...", color = {255, 0, 0}, x = 960, y = 430},
			key  = {name = "saws_message3", fallback = "... while others move in a specific direction.", color = {255, 0, 0}, x = 3100, y = -500},
		},
		exit = {x = 4870, y = 265, w = 140, h = 180},
		next_page = "ship_1_lvl3",
	},

	lvl3 = {
		-- Player init
		player = {
			x = 20, y = 500,
			spawn_x = 20, spawn_y = 500,
		},
		blocks = {
			{x = -50,  y = 650,  w = 860,  h = 100},
			{x = 920,  y = 510,  w = 100,  h = 100},
			{x = 1300, y = 650,  w = 800,  h = 100},
			{x = 1500, y = -50,  w = 700,  h = 50},
			{x = 1700, y = -350, w = 1050, h = 50},
			{x = 1500, y = -250, w = 50,   h = 200},
			{x = 2700, y = -180, w = 230,  h = 50},
			{x = 2880, y = -350, w = 700,  h = 50},
			{x = 3900, y = -350, w = 100,  h = 30},
			{x = 3900, y = -50,  w = 100,  h = 30},
			{x = 3900, y = -650, w = 100,  h = 30},
			{x = 4200, y = -150, w = 100,  h = 30},
			{x = 4200, y = -750, w = 100,  h = 30},
			{x = 4200, y = -450, w = 100,  h = 30},
			{x = 4500, y = -50,  w = 100,  h = 30},
			{x = 4500, y = -350, w = 100,  h = 30},
			{x = 4500, y = -650, w = 100,  h = 30},
			{x = 4800, y = -150, w = 100,  h = 30},
			{x = 4800, y = -750, w = 100,  h = 30},
			{x = 4800, y = -450, w = 100,  h = 30},
		},
		jump_blocks = {
			{x = 2200, y = 751, w = 100, h = 100},
			{x = 2570, y = 400, w = 100, h = 100},
		},
		spikes = {
			{{1660, 650}, {1710, 600}, {1760, 650}},
			{{2000, 650}, {2050, 600}, {2100, 650}},
			{{3300, -350}, {3350, -400}, {3400, -350}},
			{{3900, -50}, {3950, -100}, {4000, -50}},
			{{3900, -650}, {3950, -700}, {4000, -650}},
			{{4200, -450}, {4250, -500}, {4300, -450}},
			{{4500, -50}, {4550, -100}, {4600, -50}},
			{{4800, -750}, {4850, -800}, {4900, -750}},
			{{4800, -150}, {4850, -200}, {4900, -150}},
		},
		saws = {
			{x = 500,  y = 630,  radius = 80, type = 'static'},
			{x = 2200, y = -360, radius = 80, type = 'static'},
			{radius = 100, speed = 6, x = 1150, y = 200, max = 700, min = 200, type = 'moving_y'},
			{radius = 100, speed = 8, x = 2400, y = -500, max = 3300, min = 2400, type = 'moving_x'},
		},
		flags = {
			{x = 2100, y = -150, w = 100, h = 125, save_x = 2100, save_y = -150},
			{x = 3450, y = -450, w = 100, h = 125, save_x = 3450, save_y = -450},
		},
		key_block_pairs = {
			{
			key = {x = 4250, y = -900, radius = 30, color = {255, 255, 0}},
			block = {x = 1300, y = -250, w = 200, h = 250},
			collected = false
			},
		},
		exit = {x = 1360, y = 20, w = 140, h = 180},
		next_page = "ship_1_lvl4",
	},

	lvl4 = {
		-- Player init
		player = {
			x = 220, y = 500,
			spawn_x = 220, spawn_y = 500,
		},
		blocks = {
			{x = -200, y = 700, w = 1200, h = 100},
			{x = 800,  y = 400, w = 100,  h = 100},
			{x = 1400, y = 400, w = 100,  h = 100},
			{x = 1700, y = 400, w = 100,  h = 100},
			{x = 2000, y = 400, w = 100,  h = 100},
			{x = 2300, y = 500, w = 450,  h = 50},
			{x = 2900, y = 10,  w = 50,   h = 570},
			{x = 3150, y = 10,  w = 50,   h = 170},
			{x = 2950, y = 530, w = 2950, h = 50},
			{x = 3200, y = 130, w = 2700, h = 50},
		},
		jump_blocks = {
			{x = 1000, y = 600, w = 100, h = 50},
			{x = 400,  y = 650, w = 100, h = 50},
			{x = 2650, y = 400, w = 100, h = 100},
		},
		spikes = {
			{{500, 700}, {545, 600}, {590, 700}},
			{{600, 700}, {645, 600}, {690, 700}},
			{{700, 700}, {745, 600}, {790, 700}},
			{{800, 700}, {845, 600}, {890, 700}},
			{{900, 700}, {945, 600}, {990, 700}},
			{{4100, 130}, {4150, 80}, {4200, 130}},
			{{4610, 130}, {4660, 80}, {4710, 130}},
			{{4300, 530}, {4345, 480}, {4390, 530}},
			{{4400, 530}, {4445, 480}, {4490, 530}},
		},
		saws = {
			{x = 5000, y = 550, radius = 95, type = 'static'},
			{x = 5400, y = 550, radius = 95, type = 'static'},
			{radius = 100, speed = 20, x = 3800, y = -400, max = 600, min = -400, type = 'moving_y'},	
			{radius = 100, speed = 16, x = 4900, y = 165, max = 5800, min = 4900, type = 'moving_x'},
			{radius = 40, orbit_radius = 230, angle = 0,   speed = 2, block = 1, type = 'rotating'},
			{radius = 40, orbit_radius = 230, angle = 120, speed = 2, block = 1, type = 'rotating'},
			{radius = 40, orbit_radius = 230, angle = 240, speed = 2, block = 1, type = 'rotating'},
		},
		lasers = {
			{x = 5870, y = 180, w = 15, h = 350},
		},
		flags = {
			{x = 2400, y = 380, w = 100, h = 125, save_x = 2400, save_y = 380},
			{x = 3200, y = 410, w = 100, h = 125, save_x = 3200, save_y = 410},
		},
		key_block_pairs = {
			{
			key = {x = 5800, y = 50, radius = 30, color = {255, 255, 0}},
			block = {x = 2950, y = 10, w = 200, h = 170},
			collected = false
			},
		},
		exit = {x = 5630, y = 340, w = 140, h = 180},
		next_page = "quit",
	},
}

return {
	[1] = sub1
}