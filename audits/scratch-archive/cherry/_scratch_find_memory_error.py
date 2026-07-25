from pathlib import Path

asar = Path.home() / "AppData/Local/Programs/Cherry Studio/resources/app.asar"
data = asar.read_bytes()
needles = [
    b"Failed to update memory config",
    b"globalMemoryEnabled",
    b"updateMemoryConfig",
    b"memory config",
]
for n in needles:
    idxs = []
    start = 0
    while len(idxs) < 5:
        i = data.find(n, start)
        if i < 0:
            break
        idxs.append(i)
        start = i + 1
    print(n.decode("utf-8", "replace"), idxs)
    for i in idxs[:2]:
        frag = data[max(0, i - 80) : i + 180]
        # printable only
        text = "".join(chr(b) if 32 <= b < 127 else "." for b in frag)
        print("  ", text)
