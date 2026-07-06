import cleobo.data.manage_data as manage_data
import cleobo.ui.menu_ui as menu_ui
import time

def get_notif_text(ach_key, default_name, color):
    # Helper to build the 'Achievement Unlocked: Name' string
    lang = manage_data.change_language(manage_data.lang_code, manage_data.manifest, manage_data.progress)
    ach_data = lang.get("achieve", {})
    
    # Get "Achievement Unlocked:" prefix
    prefix = ach_data.get("unlock", "Achievement unlocked:")
    # Get the specific name (e.g., "Speedy Starter!")
    name = ach_data.get(ach_key, default_name)
    
    # Combine them and render
    full_string = f"{prefix} {name}"
    return menu_ui.render_text(full_string, True, color)

def lvl1speed():
    unlock = manage_data.progress["achieved"].get("speedy_starter", False)
    if not unlock:
     lv_time = manage_data.progress['lvls']['green']['1']['lvl1'].get('time', 0)
     if lv_time != 0 and lv_time <= 4.5:
        manage_data.progress["char"]["sunnyrobo"] = True
        manage_data.progress["achieved"]["speedy_starter"] = True  
        # LOCALIZED HERE
        menu_ui.notification_text = get_notif_text("speedy_starter", "Speedy Starter", (0, 249, 41))
        if not manage_data.is_mute:
            manage_data.sounds['notify'].play()
        if menu_ui.notification_time is None:
            menu_ui.notif = True
            menu_ui.notification_time = time.time()
    else:
       if not manage_data.progress["char"]["sunnyrobo"]:
          manage_data.progress["char"]["sunnyrobo"] = True

def perfect6():
    unlock = manage_data.progress["achieved"].get("zen_os", False)
    lv = manage_data.progress['lvls']['ship']['1']['lvl4']
    if lv['time'] <= 30 and lv['medal'] == "Diamond" and not unlock:
        manage_data.progress["achieved"]["zen_os"] = True
        manage_data.progress["char"]["ironrobo"] = True
        manage_data.save_progress(manage_data.progress, manage_data.manifest)
        # LOCALIZED HERE
        menu_ui.notification_text = get_notif_text("zen_os", "Zenith of Six", (102, 0, 255))
        if not manage_data.is_mute:
            manage_data.sounds['notify'].play()
        if menu_ui.notification_time is None:
            menu_ui.notif = True
            menu_ui.notification_time = time.time()

def lvl90000():
    unlock = manage_data.progress["achieved"].get("over_9k", False)
    if manage_data.progress['lvls']['mech']['1']['lvl3']['score'] >= 103500 and not unlock:
        manage_data.progress["achieved"]["over_9k"] = True          
        # LOCALIZED HERE
        menu_ui.notification_text = get_notif_text("over_9k", "It's over 9000!!", (255, 128, 0))
        if not manage_data.is_mute:
            manage_data.sounds['notify'].play()
        if menu_ui.notification_time is None:
            menu_ui.notif = True
            menu_ui.notification_time = time.time()

def termvel():
    unlock = manage_data.progress["achieved"].get("termvel", False)
    if not unlock:
      lv_time = manage_data.progress["lvls"]["mech"]["1"]["lvl5"].get("time", 0)
      if lv_time != 0 and lv_time < 15:
        manage_data.progress["achieved"]["termvel"] = True
        manage_data.progress["char"]["evilrobo"] = True
        manage_data.save_progress(manage_data.progress, manage_data.manifest)
        # LOCALIZED HERE
        menu_ui.notification_text = get_notif_text("termvel", "Terminal Velocity!", (0, 196, 255))
        if not manage_data.is_mute:
            manage_data.sounds['notify'].play()
        if menu_ui.notification_time is None:
            menu_ui.notif = True
            menu_ui.notification_time = time.time()

def check_green_gold():
    unlock = manage_data.progress["achieved"].get("golden", False)
    if not unlock: 
      all_gold = all(manage_data.progress["lvls"]["green"]["1"][f"lvl{i}"].get("medal", "None") in ["Gold", "Diamond"] for i in range(1, 5))
      if all_gold:
        manage_data.progress["achieved"]["golden"] = True
        manage_data.progress["char"]["greenrobo"] = True
        manage_data.save_progress(manage_data.progress, manage_data.manifest)
        # LOCALIZED HERE
        menu_ui.notification_text = get_notif_text("golden", "Golden!", (0, 196, 255))
        if not manage_data.is_mute:
            manage_data.sounds['notify'].play()
        if menu_ui.notification_time is None:
            menu_ui.notif = True
            menu_ui.notification_time = time.time()

def check_the_captain():
    unlock = manage_data.progress["achieved"].get("captain", False)
    if not unlock: 
      all_dia = all(manage_data.progress["lvls"]["ship"]["1"][f"lvl{i}"].get("medal", "None") in ["Gold", "Diamond"] for i in range(1, 5))
      if all_dia:
        manage_data.progress["achieved"]["captain"] = True
        manage_data.progress["char"]["piratebot"] = True
        manage_data.save_progress(manage_data.progress, manage_data.manifest)
        # LOCALIZED HERE
        menu_ui.notification_text = get_notif_text("captain", "Captain of the Ship!", (0, 196, 255))
        if not manage_data.is_mute:
            manage_data.sounds['notify'].play()
        if menu_ui.notification_time is None:
            menu_ui.notif = True
            menu_ui.notification_time = time.time()

def check_mech_eng():
    unlock = manage_data.progress["achieved"].get("mech_eng", False)
    if not unlock: 
      all_dia = all(manage_data.progress["lvls"]["mech"]["1"][f"lvl{i}"].get("medal", "None") in ["Diamond"] for i in range(1, 7))
      if all_dia:
        manage_data.progress["achieved"]["mech_eng"] = True
        manage_data.progress["char"]["vectorbot"] = True
        manage_data.save_progress(manage_data.progress, manage_data.manifest)
        # LOCALIZED HERE
        menu_ui.notification_text = get_notif_text("mech_eng", "Mechanical Engineer!", (255, 154, 0))
        if not manage_data.is_mute:
            manage_data.sounds['notify'].play()
        if menu_ui.notification_time is None:
            menu_ui.notif = True
            menu_ui.notification_time = time.time()

def check_xplvl20():
    unlock = manage_data.progress["achieved"].get("lv20", False)
    if manage_data.progress['player']['Level'] >= 20 and not unlock:
        manage_data.progress["achieved"]["lv20"] = True
        manage_data.progress["char"]["cashrobo"] = True
        manage_data.save_progress(manage_data.progress, manage_data.manifest)
        # LOCALIZED HERE
        menu_ui.notification_text = get_notif_text("lv20", "XP Collector!", (0, 196, 255))
        if not manage_data.is_mute:
            manage_data.sounds['notify'].play()
        if menu_ui.notification_time is None:
            menu_ui.notif = True
            menu_ui.notification_time = time.time()
    else:
       if not manage_data.progress["char"]["cashrobo"] and unlock:
          manage_data.progress["char"]["cashrobo"] = True

def check_achievements():
    check_xplvl20()
    check_green_gold()
    check_mech_eng()
    check_the_captain()
    termvel()
    lvl90000()
    perfect6()
    lvl1speed()