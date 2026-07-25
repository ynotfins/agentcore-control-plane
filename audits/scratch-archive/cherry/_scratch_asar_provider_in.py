from pathlib import Path

asar = Path.home() / "AppData/Local/Programs/Cherry Studio/resources/app.asar"
data = asar.read_bytes()
# Find getKnowledgeBaseParams definition vicinity
for needle in [
    b"function getKnowledgeBaseParams",
    b"getKnowledgeBaseParams =",
    b"getModel(",
    b"'provider' in",
    b'"provider" in',
]:
    idxs = []
    start = 0
    while len(idxs) < 8:
        i = data.find(needle, start)
        if i < 0:
            break
        idxs.append(i)
        start = i + 1
    print(needle, idxs[:8])

# show context around first 'provider' in near memory setConfig path - search within getKnowledgeBaseParams
i = data.find(b"getKnowledgeBaseParams")
print("first getKnowledgeBaseParams", i)
frag = data[i : i + 1200]
print("".join(chr(b) if 32 <= b < 127 else "." for b in frag))
print("====")
# find toLowerCase near model provider
j = 0
count = 0
while count < 5:
    j = data.find(b".toLowerCase()", j + 1)
    if j < 0:
        break
    frag = data[max(0, j - 60) : j + 40]
    text = "".join(chr(b) if 32 <= b < 127 else "." for b in frag)
    if "provider" in text.lower() or "model" in text.lower():
        print(j, text)
        count += 1
