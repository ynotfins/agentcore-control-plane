import json, os, urllib.request, winreg

def vk():
    v=os.environ.get('BIFROST_MCP_VIRTUAL_KEY') or ''
    if v: return v
    with winreg.OpenKey(winreg.HKEY_CURRENT_USER, r'Environment') as k:
        return str(winreg.QueryValueEx(k,'BIFROST_MCP_VIRTUAL_KEY')[0])
URL='http://127.0.0.1:8080/mcp'; session=None
def post(payload, timeout=60):
    global session
    body=json.dumps(payload).encode()
    h={'Content-Type':'application/json','Accept':'application/json, text/event-stream','Authorization':'Bearer '+vk()}
    if session: h['Mcp-Session-Id']=session
    req=urllib.request.Request(URL,data=body,headers=h,method='POST')
    with urllib.request.urlopen(req, timeout=timeout) as r:
        raw=r.read().decode('utf-8','replace'); hdr={k.lower():v for k,v in r.headers.items()}
    if hdr.get('mcp-session-id'): session=hdr['mcp-session-id']
    if raw.strip().startswith('{'): return json.loads(raw)
    data=None
    for line in raw.splitlines():
        if line.startswith('data:'):
            chunk=line[5:].strip()
            if chunk and chunk!='[DONE]':
                try: data=json.loads(chunk)
                except: pass
    return data
def tool(name, args):
    d=post({'jsonrpc':'2.0','id':1,'method':'tools/call','params':{'name':name,'arguments':args}})
    t=((d.get('result') or {}).get('content') or [{}])[0].get('text','')
    try: return json.loads(t)
    except: return {'text':t[:400]}
post({'jsonrpc':'2.0','id':1,'method':'initialize','params':{'protocolVersion':'2025-03-26','capabilities':{},'clientInfo':{'name':'iso','version':'0'}}})
post({'jsonrpc':'2.0','method':'notifications/initialized'})
for pid, root in [('openrouter-wf-fixture-20260720', r'D:\github\openrouter-wf-fixture-20260720'), ('nfa-alerts-enterprise', r'D:\github\nfa-alerts-enterprise'), ('cf-blazewatch', r'D:\github\cf-blazewatch')]:
    print('==', pid)
    act=tool('agentcore_project_router-project_activate', {'id': pid})
    print('activate', str(act)[:160])
    opened=tool('agentcore_memory-session_open', {'project_key': pid, 'project_name': pid, 'canonical_repo_path': root, 'worktree_path': root, 'repo_key': pid, 'branch_name': 'main', 'client_key': 'cherry-studio', 'agent_key': 'cherry-studio-assistant', 'session_key': f'cherry-iso-{pid}', 'context_profile': 'standard-context'})
    print('open', opened)
    ret=tool('agentcore_memory-retrieve_context', {'project_key': pid, 'page_size': 3})
    print('retrieve', str(ret)[:200])
