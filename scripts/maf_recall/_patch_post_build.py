from pathlib import Path
p = Path('d:/github/agentcore-control-plane/scripts/maf_recall/post_build_audit.md')
t = p.read_text(encoding='utf-8')
extra = chr(10)+'## MAF host follow-up'+chr(10)+chr(10)+'- import agent_framework 1.15.0 OK'+chr(10)+'- port 8080 refuse bind confirmed'+chr(10)
if 'MAF host follow-up' not in t:
    p.write_text(t.rstrip()+chr(10)+extra, encoding='utf-8', newline=chr(10))
print('POST_OK')
