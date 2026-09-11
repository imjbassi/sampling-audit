import io, re, json, sys

tex = io.open(sys.argv[1], encoding="utf-8").read()
keys = set(json.load(io.open(sys.argv[2], encoding="utf-8")).values())

sites = re.findall(r"\\cite\{([^}]*)\}", tex)
used = set()
for s in sites:
    used.update(x.strip() for x in s.split(","))

print("cite sites       :", len(sites))
print("distinct keys    :", len(used))
print("keys not in bib  :", sorted(used - keys) or "none")
print("bib keys unused  :", sorted(keys - used) or "none")
stray = re.findall(r"(?<![\w\\])\[\s*\d+(?:\s*,\s*\d+)*\s*\]", tex)
print("stray [n] markers:", len(stray), stray[:5])
print("sample site      :", sites[0] if sites else "NONE")
