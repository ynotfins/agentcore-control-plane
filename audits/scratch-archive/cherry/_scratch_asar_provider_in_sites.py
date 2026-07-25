from pathlib import Path

asar = Path.home() / "AppData/Local/Programs/Cherry Studio/resources/app.asar"
data = asar.read_bytes()
for i in [169434999, 169693000, 169693311, 169778746, 176990725]:
    frag = data[i - 120 : i + 160]
    text = "".join(chr(b) if 32 <= b < 127 else "." for b in frag)
    print("====", i)
    print(text)
    print()
