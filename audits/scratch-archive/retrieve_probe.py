import json, os, urllib.request, urllib.error, winreg, re

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
    try:
        with urllib.request.urlopen(req, timeout=timeout) as r:
            raw=r.read().decode('utf-8','replace'); hdr={k.lower():v for k,v in r.headers.items()}; code=r.status
    except Exception as e:
        return 0, {'exception':str(e)[:200]}
    if hdr.get('mcp-session-id'): session=hdr['mcp-session-id']
    data=None
    if raw.strip().startswith('{'): data=json.loads(raw)
    else:
        for line in raw.splitlines():
            if line.startswith('data:'):
                chunk=line[5:].strip()
                if chunk and chunk!='[DONE]':
                    try: data=json.loads(chunk)
                    except: pass
    return code, data
post({'jsonrpc':'2.0','id':1,'method':'initialize','params':{'protocolVersion':'2025-03-26','capabilities':{},'clientInfo':{'name':'ret','version':'0'}}})
post({'jsonrpc':'2.0','method':'notifications/initialized'})
for args in [
  {'project_key':'agentcore-control-plane','page_size':3},
  {'project_key':'agentcore-control-plane','query':'cherry-alignment','page_size':3},
  {'project_key':'new-api','page_size':3},
  {'project_key':'AI-Project-Manager','page_size':3},
  {'project_key':'alerts-sheets','page_size':3},
]:
  code,data=post({'jsonrpc':'2.0','id':2,'method':'tools/call','params':{'name':'agentcore_memory-retrieve_context','arguments':args}}, timeout=90)
  text=''
  try:
    text=((data.get('result') or {}).get('content') or [{}])[0].get('text','')[:300]
  except Exception:
    text=str(data)[:300]
  print('ARGS', args, 'CODE', code, 'TEXT', text.replace('\n',' ')[:300])
