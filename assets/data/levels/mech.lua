local lvl1 = {
	-- Player init
	player = {
	    x = 100, y = 200,
	    spawn_x = 100, spawn_y = 200,
	},
	blocks = {
	    {x = 0, y = 400, w = 3000, h = 50},
	    {x = 3200, y = 500, w = 500, h = 50},
	    {x = 3900, y = 500, w = 500, h = 50},
	    {x = 4600, y = 500, w = 700, h = 50},
	    {x = 100, y = -1250, w = 300, h = 50},
	    {x = 600, y = -1000, w = 700, h = 50},
	    {x = 1450, y = -1125, w = 650, h = 50},
	},
	spikes = {
	    {{3400, 500}, {3450, 450}, {3500, 500}},
	    {{4100, 500}, {4150, 450}, {4200, 500}},
	},
	saws = {
	    {x = 5000, y = 550, radius = 100, type = 'static'},
        {radius = 80, speed = 9, x = 3800, y = 200, max = 700, min = 200, type = 'moving_y'},
	    {radius = 80, speed = 9, x = 4500, y = 600, max = 700, min = 200, type = 'moving_y'},
        {radius = 100, speed = 11, x = 700, y = -975, max = 1200, min = 700, type = 'moving_x'},
	    {radius = 100, speed = 7, x = 1550, y = -1100, max = 2000, min = 1550, type = 'moving_x'},
        {radius = 40, orbit_radius = 230, angle = 0, speed = 3, block = 0, type = 'rotating'},
	    {radius = 40, orbit_radius = 230, angle = 120, speed = 3, block = 0, type = 'rotating'},
	    {radius = 40, orbit_radius = 230, angle = 240, speed = 3, block = 0, type = 'rotating'},
	    {radius = 60, orbit_radius = 500, angle = 60, speed = 2, block = 0, type = 'rotating'},
	    {radius = 60, orbit_radius = 500, angle = 180, speed = 2, block = 0, type = 'rotating'},
	    {radius = 60, orbit_radius = 500, angle = 300, speed = 2, block = 0, type = 'rotating'},
	    {radius = 80, orbit_radius = 900, angle = 0, speed = 1, block = 0, type = 'rotating'},
	    {radius = 80, orbit_radius = 900, angle = 120, speed = 1, block = 0, type = 'rotating'},
	    {radius = 80, orbit_radius = 900, angle = 240, speed = 1, block = 0, type = 'rotating'},
    },
	flags = {
            {x = 2600, y = 300, w = 100, h = 125, save_x = 2600, save_y = 300},
            {x = 240, y = -1360, w = 100, h = 125, save_x = 240, save_y = -1360}
        },
	teleporters = {
	    {entry_x = 5150, entry_y = 300, entry_w = 140, entry_h = 180, exit_x = 100, exit_y = -1400, exit_w = 50, exit_h = 50},
	},
	text = {
		saws = {name = "portal_message", fallback = "These blue portals teleport you! But to good places... mostly!", color = {0, 170, 255}, x = 4400, y = 300},
	},
	exit = {x = 1960, y = -1320, w = 140, h = 180},
	next_page = "mech_lvl2",
}

local lvl2 = {
	-- Player init
	player = {
	    x = 0, y = 260,
	    spawn_x = 0, spawn_y = 260,
	},
	blocks = {
	    {x = 0, y = 400, w = 100, h = 100},
	    {x = 460, y = 650, w = 540, h = 50},
	    {x = 1200, y = 200, w = 1050, h = 50},
	    {x = 8200, y = 700, w = 6000, h = 400},
	    {x = 9000, y = 150, w = 50, h = 600},
	    {x = 9600, y = 150, w = 50, h = 600},
	    {x = 10000, y = -750, w = 2000, h = 500},
	    {x = 10000, y = -750, w = 100, h = 1220},
	    {x = 10750, y = 540, w = 600, h = 170},
	},
	jump_blocks = {
	    {x = 1100, y = 600, w = 100, h = 100},
	    {x = 11000, y = 440, w = 100, h = 100},
	},
	spikes = {
	    {{700, 650}, {750, 600}, {800, 650}},
	    {{1400, 200}, {1475, 120}, {1550, 200}},
	    {{9000, 150}, {9025, 100}, {9050, 150}},
	    {{9600, 150}, {9625, 100}, {9650, 150}},
	},
	saws = {
        {radius = 60, speed = 11, x = 350, y = 200, max = 800, min = 0, type = 'moving_y'},
        {radius = 130, speed = 19, x = 11000, y = -50, max = 11300, min = 10700, type = 'moving_x'},
		{x = 1850, y = 200, radius = 80, type = 'static'},
	    {x = 9025, y = 725, radius = 150, type = 'static'},
	    {x = 9625, y = 725, radius = 150, type = 'static'},
    },
	flags = {
		{x = 8700, y = 580, w = 100, h = 125, save_x = 8700, save_y = -320},
		{x = 10000, y = 580, w = 100, h = 125, save_x = 10000, save_y = -320},
	},
	grav_weak = {
		{x = 8700, y = 550}
	},
	teleporters = {
	    {entry_x = 2090, entry_y = 0, entry_w = 140, entry_h = 180, exit_x = 8300, exit_y = 500, exit_w = 50, exit_h = 50},
	},
	text = {
		button_1 = {name = "button1_message", fallback = "Blue buttons, upon activation, will make you jump higher!", color = {51, 153, 255}, x = 8400, y = 750},
		clarify = {name = "clarify_message", fallback = "Until you reach a checkpoint, of course!", color = {51, 153, 255}, x = 9800, y = 750},
		mock = {name = "mock_message", fallback = "Wrong way my guy nothing to see here...", color = {255, 0, 0}, x = 13200, y = 550}
	},
	exit = {x = 10980, y = -150, w = 140, h = 180},
	next_page = "mech_lvl3",
}

local lvl3 = {
	-- Player init
	player = {
	    x = 50, y = -50,
	    spawn_x = 50, spawn_y = -50,
	},
	blocks = {
	    {x = 0, y = 100, w = 1000, h = 50},
	    {x = 500, y = 60, w = 500, h = 80},
	    {x = 0, y = -300, w = 1000, h = 100},
	    {x = 1600, y = 600, w = 300, h = 100},
	    {x = 2050, y = 500, w = 100, h = 100},
	    {x = 2300, y = 400, w = 600, h = 100},
	    {x = 2800, y = -340, w = 100, h = 540},
	    {x = 3200, y = 200, w = 100, h = 530},
	    {x = 2900, y = -600, w = 1100, h = 100},
	    {x = 3500, y = 200, w = 2030, h = 100},
		{x = 4770, y = 0, w = 100, h = 200},
	    {x = 3200, y = 650, w = 2630, h = 100},
	},
	lasers = {
		{x = 3545, y = 300, w = 15, h = 350},
	},
	jump_blocks = {
	    {x = 1250, y = 600, w = 100, h = 100},
	    {x = 2970, y = 420, w = 100, h = 100},
	    {x = 5730, y = 550, w = 100, h = 100},
	},
	spikes = {
	    {{0, -200}, {50, -150}, {100, -200}},
	    {{110, -200}, {160, -150}, {210, -200}},
	    {{220, -200}, {270, -150}, {320, -200}},
	    {{330, -200}, {380, -150}, {430, -200}},
	    {{440, -200}, {490, -150}, {540, -200}},
	    {{550, -200}, {600, -150}, {650, -200}},
	    {{660, -200}, {710, -150}, {760, -200}},
	    {{770, -200}, {820, -150}, {870, -200}},
	    {{880, -200}, {930, -150}, {980, -200}},
	    {{2900, 200}, {2950, 150}, {2900, 100}},
	    {{2900, 90}, {2950, 40}, {2900, -10}},
	    {{2900, -20}, {2950, -70}, {2900, -120}},
	    {{2900, -130}, {2950, -180}, {2900, -230}},
	    {{2900, -240}, {2950, -290}, {2900, -340}},
	    {{3200, 220}, {3150, 270}, {3200, 320}},
	    {{3200, 330}, {3150, 380}, {3200, 430}},
	    {{4000, 200}, {4050, 150}, {4100, 200}},
	    {{4110, 200}, {4160, 150}, {4210, 200}},
	    {{4220, 200}, {4270, 150}, {4320, 200}},
	    {{4330, 200}, {4380, 150}, {4430, 200}},
	    {{4440, 200}, {4490, 150}, {4540, 200}},
	    {{4550, 200}, {4600, 150}, {4650, 200}},
	    {{4660, 200}, {4710, 150}, {4760, 200}},
	    {{4770, 0}, {4820, -50}, {4870, 0}},
	    {{4880, 200}, {4930, 150}, {4980, 200}},
	    {{4990, 200}, {5040, 150}, {5090, 200}},
	    {{5100, 200}, {5150, 150}, {5200, 200}},
	    {{5210, 200}, {5260, 150}, {5310, 200}},
	    {{5320, 200}, {5370, 150}, {5420, 200}},
	    {{5430, 200}, {5480, 150}, {5530, 200}},
	    {{4950, 300}, {5000, 350}, {5050, 300}},
	    {{4350, 300}, {4400, 350}, {4450, 300}},
	},
	saws = {
		{radius = 70, speed = 5, x = 3700, y = 500, max = 900, min = 300, type = 'moving_y'},	
	    {radius = 70, speed = 10, x = 4500, y = 600, max = 1000, min = 100, type = 'moving_y'},
		{radius = 100, speed = 14, x = 3800, y = 700, max = 5400, min = 3700, type = 'moving_x'},
	},
	flags = {
		{x = 2350, y = 300, w = 100, h = 125, save_x = 2350, save_y = 300}, 
		{x = 5600, y = 550, w = 100, h = 125, save_x = 5600, save_y = 550}
	},
	grav_strong = {
		{x = 300, y = 0}
	},
	grav_weak = {
		{x = 2550, y = 300}
	},
	key_block_pairs = {
		{
	    key = {x = 3700, y = 550, radius = 30, color = {255, 255, 0}},
		block = {x = 3300, y = 200, w = 200, h = 100},
		collected = false
		},
	},
	moving_block = {
        {x = 4450, y = 30, w = 100, h = 50, axis = "x", direction = 1, speed = 8, limit_x = 4050, limit_y = 5600},
    },
	exit = {x = 3340, y = 420, w = 140, h = 180},
	next_page = "mech_lvl4",
}

local lvl4 = {
	-- Player init
	player = {
	    x = 0, y = 250,
	    spawn_x = 0, spawn_y = 250,
	},
	blocks = {
	    {x = -100, y = 500, w = 1200, h = 50},
	    {x = 1300, y = 400, w = 200, h = 50},
	    {x = 1625, y = 500, w = 200, h = 50},
	    {x = 1920, y = 400, w = 100, h = 100},
	    {x = 3000, y = 480, w = 300, h = 50},
	    {x = 3500, y = 480, w = 100, h = 300},
	    {x = 3800, y = 280, w = 100, h = 500},
	    {x = 4100, y = 80, w = 100, h = 700},
	    {x = 4400, y = 280, w = 100, h = 500},
	    {x = 4700, y = 480, w = 100, h = 300},
	    {x = 4950, y = 480, w = 1200, h = 100},
	},
	saws = {
        {radius = 40, orbit_radius = 300, angle = 0, speed = 4, block = 0, type = 'rotating'},
		{radius = 70, speed = 7, x = 5900, y = 400, max = 600, min = 100, type = 'moving_y'},
		{radius = 100, speed = 4, x = 600, y = 500, max = 1000, min = 600, type = 'moving_x'},
		{radius = 50, speed = 14, x = 3550, y = 430, max = 4750, min = 3550, type = 'moving_x'},
        {radius = 50, speed = 14, x = 3550, y = 30, max = 4750, min = 3550, type = 'moving_x'},
        {radius = 50, speed = 9, x = 5200, y = 480, max = 6000, min = 5200, type = 'moving_x'},
        {radius = 50, speed = 9, x = 5200, y = 180, max = 6000, min = 5200, type = 'moving_x'},
		{x = 1825, y = 525, radius = 80, type = 'static'},
		{x = 1500, y = 425, radius = 80, type = 'static'},
		{x = 2500, y = 310, radius = 50, type = 'static'},
	},
	flags = {
		{x = 3100, y = 370, w = 100, h = 125, save_x = 3100, save_y = 370},
	},
	grav_strong = {
		{x = 5050, y = 360}
	},
	lights ={
		{
            button = {x = 350, y = 350},
		    block = {x = 1300, y = 0, w = 200, h = 400}
		}
	},
	moving_block = {
        {x = 2200, y = 300, w = 100, h = 50, axis = "x", direction = 1, speed = 5, limit_x = 2200, limit_y = 2800},
    },
	exit = {x = 5960, y = 280, w = 140, h = 180},
	next_page = "mech_lvl5",
}

local lvl5 = {
	-- Player init
	player = {
	    x = -400, y = 300,
	    spawn_x = -400, spawn_y = 300,
	},
	blocks = {
	    {x = -600, y = 525, w = 2850, h = 50},
	    {x = 1065, y = 200, w = 70, h = 375},
	    {x = 1625, y = -200, w = 100, h = 590},
	    {x = 1625, y = 50, w = 150, h = 50},
	    {x = 2200, y = 400, w = 150, h = 50},
	    {x = 2250, y = -300, w = 600, h = 2200},
	    {x = 2300, y = 200, w = 3000, h = 100},
	    {x = 3100, y = -300, w = 2600, h = 100},
	    {x = 3050, y = -500, w = 120, h = 300},
	    {x = 5180, y = 250, w = 120, h = 300},
	    {x = 5250, y = 450, w = 1500, h = 100},
	    {x = 5600, y = -1400, w = 520, h = 1700},
	}, 
	jump_blocks = {
	    {x = 630, y = 425, w = 100, h = 100},
	},
	spikes = {
	    {{0, 525}, {100, 475}, {200, 525}},
	    {{210, 525}, {310, 475}, {410, 525}},
	    {{420, 525}, {520, 475}, {620, 525}},
	    {{1625, -50}, {1575, 0}, {1625, 50}},
	    {{1625, 60}, {1575, 110}, {1625, 160}},
	    {{1625, 170}, {1575, 220}, {1625, 270}},
	    {{1625, 280}, {1575, 330}, {1625, 380}},
	},
	flags = {
		{x = 1400, y = 420, w = 100, h = 125, save_x = 1400, save_y = 420},
		{x = 5600, y = 330, w = 100, h = 125, save_x = 5600, save_y = 330},
	},
	speedster = {
		{x = -100, y = 400},
		{x = 2450, y = -400}
	},
	exit = {x = 6600, y = 250, w = 140, h = 180},
	next_page = "mech_lvl6",
}

local lvl6 = {
	-- Player init
	player = {
	    x = 100, y = 0,
	    spawn_x = 100, spawn_y = 0,
	},
	blocks = {
	    {x = 0, y = 200, w = 2000, h = 100},
	    {x = 1900, y = -1000, w = 100, h = 1000},
	    {x = 3200, y = -50, w = 800, h = 100},
	    {x = 3600, y = 300, w = 500, h = 100},
	    {x = 4100, y = -700, w = 101, h = 1100},
	    {x = 3450, y = 650, w = 1000, h = 100},
	    {x = 3350, y = 0, w = 100, h = 750},
	    {x = 2300, y = 200, w = 150, h = 100},
	    {x = 2600, y = 20, w = 200, h = 100},
	    {x = 4500, y = 750, w = 600, h = 200},
	},
	jump_blocks = {
	    {x = 3000, y = 250, w = 100, h = 100},
	    {x = 4300, y = 550, w = 100, h = 100},
	},
	spikes = {
	    {{1000, 200}, {1050, 150}, {1100, 200}},
	    {{2710, 20}, {2755, -30}, {2800, 20}},
	    {{3600, 300}, {3650, 250}, {3700, 300}},
	    {{3650, 650}, {3700, 600}, {3750, 650}},
	    {{3900, 650}, {3950, 600}, {4000, 650}},
	},
	flags = {x = 3900, y = 200, w = 100, h = 125, save_x = 3900, save_y = 200},
	exit = {x = 4080, y = -910, w = 140, h = 180},
	next_page = "quit",
}