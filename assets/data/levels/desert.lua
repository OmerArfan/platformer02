local sub1 = {
	lvl1 = {
		player = {
			x = 600, y = 200,
			spawn_x = 600, spawn_y = 200,
		},
		blocks = {
			{x = 400,  y = 450, w = 1900, h = 100},
			{x = 1100,  y = -160, w = 100, h = 410},
			{x = 1750,  y = -660, w = 100, h = 1140},
			{x = 600, y = -160, w = 900, h = 100},
			{x = 2300, y = 750, w = 400, h = 100},
			{x = 2300, y = 450, w = 100, h = 300},
			{x = 2600, y = 450, w = 100, h = 300},
			{x = 2700, y = 450, w = 2700, h = 100},
			{x = 3000, y = 50, w = 1600, h = 100},
			{x = 5400, y = 300, w = 400, h = 250},
		},
		jump_blocks = {
			{x = 1560, y = 350, w = 100, h = 100}
		},
		spikes = {
			{{1100, 250}, {1050, 200}, {1100, 150}},
			{{1500, -160}, {1550, -110}, {1500, -60}},
			{{1750, -160}, {1700, -110}, {1750, -60}},
			{{300, -150}, {350, -210}, {400, -150}},
		},
		saws = {
			{radius = 95, speed = 9, x = 800, y = -160, max = 1400, min = 700, type = 'moving_x'},
			{radius = 95, speed = 13, x = -1200, y = -160, max = 0, min = -1400, type = 'moving_x'},
			{x = 910, y = 450, radius = 80, type = 'static'},
			{x = 1480, y = 450, radius = 95, type = 'static'},
		},
		lights ={
			{
				button = {x = 50, y = -250},
				block = {x = -2000, y = -160, w = 2600, h = 100}
			},
			{
				button = {x = -600, y = -365},
				block = {x = 0, y = 0, w = 0, h = 0}
			},
			{
				button = {x = -1300, y = -365},
				block = {x = 0, y = 0, w = 0, h = 0}
			},
		},
		speedster = {
			{x = 2700, y = 320},
		},
		teleporters = {
			{entry_x = -1800, entry_y = -400, entry_w = 140, entry_h = 180, exit_x = 1900, exit_y = 290, exit_w = 50, exit_h = 50},
		},
		cacti_spikes = {
			{cord = {{2405, 750}, {2450, 700}, {2495, 750}}, axis = 'y', dir = -1, limit = -800},
			{cord = {{2505, 750}, {2550, 700}, {2595, 750}}, axis = 'y', dir = -1, limit = -800},
			{cord = {{3005, 150}, {3050, 200}, {3095, 150}}, axis = 'y', dir = 1, limit = 1200},
			{cord = {{3005, 150}, {3050, 200}, {3095, 150}}, axis = 'y', dir = 1, limit = 1200},
			{cord = {{3105, 150}, {3150, 200}, {3195, 150}}, axis = 'y', dir = 1, limit = 1200},
			{cord = {{3205, 150}, {3250, 200}, {3295, 150}}, axis = 'y', dir = 1, limit = 1200},
			{cord = {{3305, 150}, {3350, 200}, {3395, 150}}, axis = 'y', dir = 1, limit = 1200},
			{cord = {{3405, 150}, {3450, 200}, {3495, 150}}, axis = 'y', dir = 1, limit = 1200},
			{cord = {{3505, 150}, {3550, 200}, {3595, 150}}, axis = 'y', dir = 1, limit = 1200},
			{cord = {{3605, 150}, {3650, 200}, {3695, 150}}, axis = 'y', dir = 1, limit = 1200},
			{cord = {{3705, 150}, {3750, 200}, {3795, 150}}, axis = 'y', dir = 1, limit = 1200},
			{cord = {{3805, 150}, {3850, 200}, {3895, 150}}, axis = 'y', dir = 1, limit = 1200},
			{cord = {{3905, 150}, {3950, 200}, {3995, 150}}, axis = 'y', dir = 1, limit = 1200},
			{cord = {{4005, 150}, {4050, 200}, {4095, 150}}, axis = 'y', dir = 1, limit = 1200},
			{cord = {{4105, 150}, {4150, 200}, {4195, 150}}, axis = 'y', dir = 1, limit = 1200},
			{cord = {{4205, 150}, {4250, 200}, {4295, 150}}, axis = 'y', dir = 1, limit = 1200},
			{cord = {{4305, 150}, {4350, 200}, {4395, 150}}, axis = 'y', dir = 1, limit = 1200},
			{cord = {{4405, 150}, {4450, 200}, {4495, 150}}, axis = 'y', dir = 1, limit = 1200},
			{cord = {{4505, 150}, {4550, 200}, {4595, 150}}, axis = 'y', dir = 1, limit = 1200},
			{cord = {{5400, 330}, {5320, 380}, {5400, 430}}, axis = 'x', dir = -1, limit = 600},
		},
		text = {
			cactus = {name = "cacti_warn", fallback = "Cacti spikes rush towards the direction they face if you pass by them!", color = {3, 104, 0}, x = 2100, y = 250},
		},
		flags = {{x = 2050, y = 340, w = 100, h = 125, save_x = 2050, save_y = 300}},
		exit = {x = 5600, y = 100, w = 140, h = 180}, 
		next_page = "desert_1_lvl2",
	},

	lvl2 = {
		player = {
			x = 500, y = 200,
			spawn_x = 500, spawn_y = 200,
		},
		blocks = {
			{x = 300,  y = 450, w = 1700, h = 100},
			{x = 400,  y = -50, w = 1900, h = 100},
			{x = 300,  y = -450, w = 100, h = 999},
			{x = 2300,  y = -50, w = 100, h = 1200},
			{x = -100,  y = 880, w = 2500, h = 100},
		},
		spikes = {
			{{1005, 450}, {1050, 400}, {1095, 450}},
			{{1105, 450}, {1150, 400}, {1195, 450}},
			{{1505, 450}, {1550, 400}, {1595, 450}},
			{{1605, 450}, {1650, 400}, {1695, 450}},
		},
		cacti_spikes = {
			{cord = {{705, 50}, {750, 100}, {795, 50}}, axis = 'y', dir = 1, limit = 450},
			{cord = {{805, 50}, {850, 100}, {895, 50}}, axis = 'y', dir = 1, limit = 450},
			{cord = {{1205, 50}, {1250, 100}, {1295, 50}}, axis = 'y', dir = 1, limit = 450},
			{cord = {{1305, 50}, {1350, 100}, {1395, 50}}, axis = 'y', dir = 1, limit = 450},
			{cord = {{1705, 50}, {1750, 100}, {1795, 50}}, axis = 'y', dir = 1, limit = 450},
			{cord = {{1805, 50}, {1850, 100}, {1895, 50}}, axis = 'y', dir = 1, limit = 450},
			{cord = {{910, -50}, {1050, -100}, {1190, -50}}, axis = 'y', dir = -1, limit = -1500},
			{cord = {{1610, -50}, {1750, -100}, {1890, -50}}, axis = 'y', dir = -1, limit = -1500},
			{cord = {{400, -440}, {450, -250}, {400, -60}}, axis = 'x', dir = 1, limit = 2000},
		},
		saws = {
			{x = 1600, y = 900, radius = 85, type = 'static'},
			{radius = 35, speed = 5, x = 1300, y = 900, max = 920, min = 500, type = 'moving_y'},
			{radius = 35, speed = 5, x = 950, y = 500, max = 920, min = 500, type = 'moving_y'},
			{radius = 35, speed = 5, x = 600, y = 900, max = 920, min = 500, type = 'moving_y'},
		},
		lights ={
			{
				button = {x = 500, y = 340},
				block = {x = 650, y = 50, w = 260, h = 400}
			},
		},
		grav_weak = {
			{x = 350, y = 750}
		},
		jump_blocks = {
			{x = 100, y = 780, w = 100, h = 100}
		},
		flags = {{x = 450, y = 770, w = 100, h = 125, save_x = 450, save_y = 730}},
		exit = {x = 2040, y = -250, w = 140, h = 180}, 
		next_page = "desert_1_lvl3",
	},

	lvl3 = {
		player = {
			x = 550, y = 200,
			spawn_x = 550, spawn_y = 200,
		},
		blocks = {
			{x = 500,  y = 450, w = 200, h = 100},
			{x = 1100,  y = 120, w = 750, h = 100},
			{x = 2200,  y = 450, w = 500, h = 100},
			{x = 3300,  y = 580, w = 1600, h = 150},
			{x = 3300,  y = -250, w = 600, h = 150},
			{x = 3600,  y = 320, w = 0, h = 0},
			{x = 4270,  y = 270, w = 300, h = 100},
			{x = 4870,  y = 70, w = 100, h = 630},
		},
		qsand = {
			{x = 700,  y = 450, w = 1500, h = 100},
			{x = 2870,  y = 270, w = 1400, h = 100},
		},
		saws = {
			{x = 950, y = 450, radius = 74, type = 'static'},
			{radius = 40, orbit_radius = 300, angle = 0, speed = 4, block = 5, type = 'rotating'},
			{radius = 55, orbit_radius = 180, angle = 65, speed = 7, block = 2, type = 'rotating'},
			{radius = 60, speed = 14, x = 3400, y = 600, max = 630, min = -200, dir = -1, type = 'rushing_y'},
			{radius = 60, speed = 11, x = 3800, y = 600, max = 630, min = -200, dir = -1, type = 'rushing_y'},
		},
		cacti_spikes = {
			{cord = {{4870, 580}, {4820, 475}, {4870, 370}}, axis = 'x', dir = -1, limit = 730},
		},
		text = {
			qsand = {name = "qsand_warn", fallback = "Caution! Be aware of where you are when you stand on quicksand! If you don't", color = {153, 102, 0}, x = 160, y = 200},
			qsand2 = {name = "qsand2_warn", fallback = "escape fast enough, you will get crushed as you're sucked inside!", color = {153, 102, 0}, x = 210, y = 240},
			qsand3 = {name = "qsand3_warn", fallback = "Because once you start getting sucked in, it becomes difficult to survive.", color = {153, 102, 0}, x = 180, y = 280},		
			qsand4 = {name = "qsand4_warn", fallback = "Or if you stand at the very corners... you might just get pushed out instead...", color = {153, 102, 0}, x = 2780, y = 10},
		},
		speedster = {
			{x = 4680, y = 320},
		},
		exit = {x = 3530, y = 385, w = 140, h = 180}, 
		next_page = "desert_1_lvl4",
	},

	lvl4 = {
		player = {
			x = 600, y = 200,
			spawn_x = 600, spawn_y = 200,
		},
		blocks = {
			{x = 400,  y = 450, w = 1000, h = 100},
			{x = 400,  y = 20, w = 900, h = 100},
			{x = 1300,  y = -1600, w = 100, h = 1720},
			{x = 1300,  y = -1700, w = 5000, h = 100},
			{x = 1750,  y = -980, w = 100, h = 1530},
			{x = 1850,  y = -650, w = 200, h = 100},
			{x = 1850,  y = 0, w = 2600, h = 100},
			{x = 5300,  y = -650, w = 400, h = 100},
			{x = 6000,  y = -650, w = 200, h = 100},
			{x = 6200,  y = -1600, w = 100, h = 1600},
			{x = 4700,  y = 0, w = 1500, h = 100},
			{x = 4700,  y = 0, w = 100, h = 800},
			{x = 4350,  y = 0, w = 100, h = 800},
			{x = 4350,  y = 700, w = 350, h = 100},
		},
		spikes = {
			{{1005, 450}, {1050, 400}, {1095, 450}},
			{{755, 120}, {800, 170}, {845, 120}},
			{{3570, -1200}, {3585, -1215}, {3600, -1200}},
		},
		saws = {
			{x = 5425, y = -635, radius = 115, type = 'static'},
			{x = 4750, y = 0, radius = 80, type = 'static'},
			{radius = 120, speed = 27, x = 3800, y = -1600, max = 5100, min = 2100, dir = -1, type = 'moving_x'},
			{radius = 120, speed = 35, x = 5200, y = -1600, max = 5700, min = 1900, dir = 1, type = 'moving_x'},
		},
		moving_block = {
			{x = 2800, y = -770, w = 100, h = 50, axis = "x", direction = 1, speed = 11, limit_x = 2200, limit_y = 3450},
			{x = 4100, y = -1000, w = 100, h = 50, axis = "x", direction = 1, speed = 8, limit_x = 3650, limit_y = 5200},
		},
		grav_weak = {
			{x = 1300, y = 330}
		},
		speedster = {
			{x = 5800, y = -530},
		},
		jump_blocks = {
			{x = 1500, y = 450, w = 100, h = 100},
			{x = 2600, y = -650, w = 100, h = 100},
		},
		cacti_spikes = {
			{cord = {{1400, 20}, {1450, -80}, {1400, -180}}, axis = 'x', dir = 1, limit = 350},
			{cord = {{1400, -190}, {1450, -290}, {1400, -390}}, axis = 'x', dir = 1, limit = 350},
			{cord = {{1750, 20}, {1700, -80}, {1750, -180}}, axis = 'x', dir = -1, limit = 350},
			{cord = {{1750, -190}, {1700, -290}, {1750, -390}}, axis = 'x', dir = -1, limit = 350},
			{cord = {{6200, -10}, {6100, -275}, {6200, -540}}, axis = 'x', dir = -1, limit = 3000},
		},
		qsand = {
			{x = 3050,  y = -1100, w = 200, h = 100},
			{x = 3500,  y = -1200, w = 100, h = 750},
		},
		lasers = {
			{x = 2050, y = -605, w = 3250, h = 10},
		},
		lights ={
			{
				button = {x = 5800, y = -750},
				block = {x = 5700, y = -650, w = 300, h = 100}
			},
			{
				button = {x = 9, y = 80000},
				block = {x = 4450, y = 0, w = 250, h = 250}
			},
		},
		flags = {
			{x = 1900, y = -750, w = 100, h = 125, save_x = 1880, save_y = -770},
		},
		exit = {x = 4525, y = 580, w = 140, h = 180}, 
		next_page = "quit_final",
	}
}

return {
	[1] = sub1
}