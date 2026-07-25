from pathlib import Path

asar = Path.home() / "AppData/Local/Programs/Cherry Studio/resources/app.asar"
data = asar.read_bytes()
needle = b'Store not available, skipping memory config update'
i = data.find(needle)
print("idx", i)
frag = data[i : i + 900]
text = "".join(chr(b) if 32 <= b < 127 else "." for b in frag)
print(text)
print("---")
needle2 = b"embeddingModel.provider"
# find 'provider' in near MemoryProcessor
j = data.find(b"MemoryProcessor")
print("MemoryProcessor", j)
# search for pattern around Failed to update
k = data.find(b'Failed to update memory config:')
frag2 = data[k - 500 : k + 100]
text2 = "".join(chr(b) if 32 <= b < 127 else "." for b in frag2)
print(text2)
