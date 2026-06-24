local lvl1 = {
    player = {
	    x = 600, y = 200,
	    spawn_x = 600, spawn_y = 200,
	},
	blocks = {
	    {x = 400,  y = 450, w = 2000, h = 100},
		{x = 1100,  y = -160, w = 100, h = 410},
		{x = 1750,  y = -660, w = 100, h = 1140},
		{x = 600, y = -160, w = 900, h = 100},
		{x = 2300, y = 550, w = 400, h = 100},
		{x = 2600, y = 450, w = 400, h = 100}
	},
	jump_blocks = {
		{x = 1560, y = 350, w = 100, h = 100}
	},
	spikes = {
	    {{1100, 250}, {1050, 200}, {1100, 150}},
		{{1500, -160}, {1550, -110}, {1500, -60}},
		{{1750, -160}, {1700, -110}, {1750, -60}},
		{{300, -160}, {350, -210}, {400, -160}},
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
	teleporters = {
	    {entry_x = -1800, entry_y = -400, entry_w = 140, entry_h = 180, exit_x = 1900, exit_y = 290, exit_w = 50, exit_h = 50},
	},
	cacti_spikes = {
		{cord = {{2405, 550}, {2450, 500}, {2495, 550}}, axis = 'y', dir = -1, limit = -500},
		{cord = {{2505, 550}, {2550, 500}, {2595, 550}}, axis = 'y', dir = -1, limit = -500}
	},
	flags = {{x = 2050, y = 340, w = 80, h = 50, save_x = 2050, save_y = 300}},
    exit = {x = -900, y = 850, w = 140, h = 180}, 
    next_page = "desert_lvl2",
}