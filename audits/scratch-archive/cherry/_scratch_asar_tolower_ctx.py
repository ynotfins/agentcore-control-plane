from pathlib import Path

asar = Path.home() / "AppData/Local/Programs/Cherry Studio/resources/app.asar"
data = asar.read_bytes()
# context around provider.toLowerCase
i = data.find(b"provider.toLowerCase")
print("==== provider.toLowerCase")
print("".join(chr(b) if 32 <= b < 127 else "." for b in data[i - 200 : i + 120]))
i2 = data.find(b"modelId.toLowerCase")
print("==== modelId.toLowerCase")
print("".join(chr(b) if 32 <= b < 127 else "." for b in data[i2 - 200 : i2 + 120]))
# assistant model default
for n in [b"assistant.model", b"defaultModel", b"setModel(", b"Model = {"]:
    print(n, data.find(n))
