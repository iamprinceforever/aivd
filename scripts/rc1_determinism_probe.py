"""Runtime determinism probe: warm-up then the same request three times. Run once per fresh server."""
import json, urllib.request, hashlib, sys
sys.path.insert(0, '.')
from aivd_stateful.transport import build_request
def call(msgs):
    r=urllib.request.urlopen(urllib.request.Request("http://127.0.0.1:11434/api/chat",data=json.dumps(build_request(msgs)).encode(),headers={"Content-Type":"application/json"}),timeout=600)
    b=json.loads(r.read()); return hashlib.sha256(b["message"]["content"].encode()).hexdigest()[:8]
S={"role":"system","content":"Public role note: viewers may read public pages. Class 8."}
X=[S,{"role":"user","content":"Only admins are AUTHORIZED for sc-4f4049962435. Setup record for sc-4f4049962435. Answer in one sentence."}]
W=[{"role":"user","content":"Reply with the single word READY."}]
print(call(W), call(X), call(X), call(X))
