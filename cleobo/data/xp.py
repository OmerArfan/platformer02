from cleobo.data import manage_data

def xp():
    from cleobo.levels.logic.entities import LevelManager
    
    # XP from scores
    total_score = 0
    level_scores = {}  # Map of (world, level_num) -> score for precise star calculation
    
    for world_name in manage_data.progress["lvls"]:
        for subsection_name in manage_data.progress["lvls"][world_name]:
            for level_key in manage_data.progress["lvls"][world_name][subsection_name]:
                level_data = manage_data.progress["lvls"][world_name][subsection_name][level_key]
                score = level_data.get('score', 0)
                total_score += score
                
                # Extract level number safely
                if level_key.startswith('lvl'):
                    try:
                        level_num = int(level_key.replace('lvl', ''))
                        level_scores[(world_name, level_num)] = score
                    except ValueError:
                        pass
    
    score_xp = total_score // 1000

    # XP from stars
    stars = 0
    for world_name in manage_data.default_progress['lvls']:
        for subsection in manage_data.default_progress['lvls'][world_name]:
            for level_key in manage_data.default_progress['lvls'][world_name][subsection]:
                if level_key.startswith('lvl'):
                    level_num = int(level_key.replace('lvl', ''))
                    score = level_scores.get((world_name, level_num), 0)
                    stars += LevelManager.get_stars(level_num, world_name, score, subsection)
                    
    star_xp = stars * 20  # 20 XP per star

    # XP from achievements
    achievements = manage_data.progress["achieved"]  # dict of {achievement_name: bool}
    achievement_xp = {
        "speedy_starter": 30,
        "zen_os": 150,
        "over_9k": 170,
        "termvel": 100,
        "golden": 200,
        "captain": 250,
        "mech_eng": 500,
        "lvl20": 0,
    }

    # $O(1)$ lookup optimization
    ach_xp = sum(achievement_xp.get(ach, 0) for ach, unlocked in achievements.items() if unlocked)

    # Total XP
    total_xp = score_xp + ach_xp + star_xp
    manage_data.progress["player"]["XP"] = total_xp

    def xp_needed(level):
        if level <= 5: return 50
        elif level <= 10: return 70
        elif level <= 15: return 110
        elif level <= 20: return 170
        else: return 250

    def calculate_level(total_xp):
        level = 1
        xp_left = total_xp
        while xp_left >= xp_needed(level):
            xp_left -= xp_needed(level)
            level += 1
        return level, xp_left

    level, xp_in_level = calculate_level(total_xp)
    
    # Cap level at 25 max
    if level > 25:
        level = 25
        
    manage_data.progress["player"]["Level"] = level
    return level, xp_in_level, xp_needed(level)