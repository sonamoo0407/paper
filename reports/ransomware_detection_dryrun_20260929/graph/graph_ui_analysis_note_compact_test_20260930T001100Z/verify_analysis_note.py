import base64, json, os, socket, struct, time
from pathlib import Path
HOST,PORT='127.0.0.1',18739
OUT=Path(__file__).parent
RUN=OUT.parent.parent

def conn():
 s=socket.create_connection((HOST,PORT),timeout=10);k=base64.b64encode(os.urandom(16)).decode()
 s.sendall((f'GET /session HTTP/1.1\r\nHost: {HOST}:{PORT}\r\nUpgrade: websocket\r\nConnection: Upgrade\r\nSec-WebSocket-Key: {k}\r\nSec-WebSocket-Version: 13\r\n\r\n').encode())
 if ' 101 ' not in s.recv(4096).decode('latin1'):raise RuntimeError('WebSocket upgrade failed')
 return s
def send(s,o):
 p=json.dumps(o,separators=(',',':')).encode();m=os.urandom(4);n=len(p);h=bytes([129,128|n]) if n<126 else bytes([129,254])+struct.pack('!H',n);s.sendall(h+m+bytes(v^m[i%4] for i,v in enumerate(p)))
def recv(s):
 a,b=s.recv(2);n=b&127
 if n==126:n=struct.unpack('!H',s.recv(2))[0]
 if n==127:n=struct.unpack('!Q',s.recv(8))[0]
 p=b''
 while len(p)<n:p+=s.recv(n-len(p))
 return json.loads(p.decode())
def call(s,i,m,p):
 send(s,{'id':i,'method':m,'params':p})
 while 1:
  r=recv(s)
  if r.get('id')==i:
   if 'error' in r:raise RuntimeError(r)
   return r['result']
def ev(s,i,c,x):return json.loads(call(s,i,'script.evaluate',{'expression':'JSON.stringify('+x+')','target':{'context':c},'awaitPromise':True,'resultOwnership':'none'})['result']['value'])
s=conn();call(s,1,'session.new',{'capabilities':{}});time.sleep(1);c=call(s,2,'browsingContext.getTree',{})['contexts'][0]['context']
before=ev(s,3,c,"{note:document.querySelector('#detail').innerText.includes('분석 메모'),selected:window.__dryrunGraph.selected,rect:(()=>{let r=document.querySelector('.node[data-id=\\\"R1-02\\\"]').getBoundingClientRect();return {x:Math.round(r.x+r.width/2),y:Math.round(r.y+r.height/2)}})()}" )
call(s,4,'input.performActions',{'context':c,'actions':[{'type':'pointer','id':'mouse','parameters':{'pointerType':'mouse'},'actions':[{'type':'pointerMove','x':before['rect']['x'],'y':before['rect']['y'],'origin':'viewport','duration':100},{'type':'pointerDown','button':0},{'type':'pointerUp','button':0}]}]})
time.sleep(.2)
after=ev(s,5,c,"{selected:window.__dryrunGraph.selected,heads:document.querySelectorAll('.edge-arrowhead').length,note:document.querySelector('#detail').innerText.includes('분석 메모'),metadataOnly:document.querySelector('#detail').innerText.includes('메타데이터 기반 드라이런'),r1Path:document.querySelector('#detail').textContent.includes('r1_candidates.json'),r2Path:document.querySelector('#detail').textContent.includes('r2_citation_ledger.json'),searchPath:document.querySelector('#detail').textContent.includes('search_log.json'),summary:document.querySelector('#detail').innerText.includes('DOI가 있는 R2 2편을 확인했다.')}")
shot=call(s,6,'browsingContext.captureScreenshot',{'context':c,'origin':'viewport','format':{'type':'png'}})
(OUT/'analysis_note_click_firefox.png').write_bytes(base64.b64decode(shot['data']))
ok=(before['selected'] is None and after=={'selected':'R1-02','heads':2,'note':True,'metadataOnly':True,'r1Path':True,'r2Path':True,'searchPath':True,'summary':True})
result={'status':'PASS' if ok else 'FAIL','before':before,'after_actual_pointer_click':after,'screenshot':'analysis_note_click_firefox.png'}
(OUT/'analysis_note_verification.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
print(json.dumps(result,ensure_ascii=False,indent=2))
