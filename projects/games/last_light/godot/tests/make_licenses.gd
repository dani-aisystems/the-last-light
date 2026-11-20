extends SceneTree
## Release R3 (2026-11-20): writes THIRD_PARTY_LICENSES.txt for the build zip (Daniel chose the file next to
## the .app over the full texts in the credits roll). Godot's own licence, its components' copyright notices and
## licence texts come from the engine itself (Engine.get_license_text / get_copyright_info / get_license_info),
## so they always match the engine that exports the build; the four typefaces' OFL texts are read from
## assets/fonts/*/OFL.txt. Not exported (tests/* is excluded in export_presets.cfg).
##   tools/godot --headless --path projects/games/last_light/godot -s res://tests/make_licenses.gd -- --out=<file>
## Default output: projects/games/last_light/build/THIRD_PARTY_LICENSES.txt (gitignored, reproducible).

const FONTS := [
	["Libre Baskerville", "res://assets/fonts/libre_baskerville/OFL.txt"],
	["Source Sans 3", "res://assets/fonts/source_sans_3/OFL.txt"],
	["Courier Prime", "res://assets/fonts/courier_prime/OFL.txt"],
	["Cedarville Cursive", "res://assets/fonts/cedarville_cursive/OFL.txt"],
]
const RULE := "\n\n================================================================================\n\n"


func _init() -> void:
	var out := ProjectSettings.globalize_path("res://").path_join("../build/THIRD_PARTY_LICENSES.txt").simplify_path()
	for a in OS.get_cmdline_user_args():
		if a.begins_with("--out="):
			out = a.substr(6)
	var t := "THE LAST LIGHT: third-party licences\n"
	t += "\nThis game is made with Godot Engine (godotengine.org), used under the MIT licence below,"
	t += "\nand bundles the typefaces listed at the end under the SIL Open Font License 1.1."
	t += "\nThe CC0 1.0 textures, meshes and sounds credited in the game need no licence text."
	t += RULE + "GODOT ENGINE\n\n" + Engine.get_license_text()
	t += RULE + "GODOT ENGINE: THIRD-PARTY COMPONENTS\n"
	for c in Engine.get_copyright_info():
		t += "\n" + String(c["name"]) + "\n"
		for p in c["parts"]:
			for line in p["copyright"]:
				t += "    Copyright " + String(line) + "\n"
			t += "    Licence: " + String(p["license"]) + "\n"
	var lic: Dictionary = Engine.get_license_info()
	var names := lic.keys()
	names.sort()
	t += RULE + "LICENCE TEXTS USED BY THE COMPONENTS ABOVE\n"
	for n in names:
		t += "\n----- " + String(n) + " -----\n\n" + String(lic[n]) + "\n"
	var missing := []
	for f in FONTS:
		if not FileAccess.file_exists(f[1]):
			missing.append(f[1])
			continue
		t += RULE + "TYPEFACE: " + String(f[0]) + " (SIL Open Font License 1.1)\n\n" + FileAccess.get_file_as_string(f[1])
	DirAccess.make_dir_recursive_absolute(out.get_base_dir())
	var fa := FileAccess.open(out, FileAccess.WRITE)
	if fa == null or not missing.is_empty():
		print("LICENSES_RESULT %s" % JSON.stringify({"ok": false, "out": out, "missing": missing}))
		quit(1)
		return
	fa.store_string(t)
	fa.close()
	print("LICENSES_RESULT %s" % JSON.stringify({"ok": true, "out": out, "bytes": t.length(),
		"components": Engine.get_copyright_info().size(), "licences": names.size(), "fonts": FONTS.size()}))
	quit(0)
