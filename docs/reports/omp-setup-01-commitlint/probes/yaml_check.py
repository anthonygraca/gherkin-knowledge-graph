import pathlib, yaml
doc = yaml.safe_load(pathlib.Path(".github/workflows/ci.yml").read_text(encoding="utf-8"))
trig = doc.get("on", doc.get(True))
print("triggers:", trig)
assert trig["push"]["branches"] == ["main"], trig
assert trig["pull_request"]["types"] == ["opened", "synchronize", "reopened", "edited"], trig
print("YAML structure OK: pull_request types include edited")
