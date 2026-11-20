extends SceneTree
## Release R3 (2026-11-20): stills of the credits roll, one page at a time (CreditsRoll.freeze_at), so every
## line can be read on a capture. Windowed only (a headless run has no picture):
##   tools/godot_bg --path projects/games/last_light/godot -s res://tests/credits_shots.gd -- --capture=NAME
## Writes renders/last_light/NAME_pNN.png; prints CREDITS_SHOTS_RESULT. Not exported (tests/*).

func _initialize() -> void:
	_run.call_deferred()


func _run() -> void:
	var name_ := "credits"
	for a in OS.get_cmdline_user_args():
		if a.begins_with("--capture="):
			name_ = a.substr(10)
	var out_dir := ProjectSettings.globalize_path("res://").path_join("../../../../renders/last_light").simplify_path()
	DirAccess.make_dir_recursive_absolute(out_dir)
	var roll := CreditsRoll.new().setup(false)          # menu mode: no music, nothing moves it but freeze_at
	root.add_child(roll)
	for i in 10:
		await process_frame
	var h: float = roll.size.y
	var files := []
	var px := h * 0.75                                  # the first page: the top of the text in the lower quarter
	var n := 0
	while px <= roll.end_scroll() and n < 20:
		roll.freeze_at(px)
		for i in 4:
			await process_frame
		var f := out_dir.path_join("%s_p%02d.png" % [name_, n])
		root.get_texture().get_image().save_png(f)
		files.append(f)
		px += h * 0.7                                   # 30 % overlap, so no line is cut on both pages
		n += 1
	print("CREDITS_SHOTS_RESULT %s" % JSON.stringify({"files": files, "content_px": roll.text.get_content_height(),
		"window": [roll.size.x, h]}))
	quit(0)
