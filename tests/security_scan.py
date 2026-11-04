"""Read-only heuristic repository/history scan; outputs locations and hashes only.

Run from the repository root. This is not a replacement for a maintained secret
scanner. It never opens credential files outside this repository or uses network.
"""
import subprocess, pathlib, re, json, hashlib, shutil
root=pathlib.Path.cwd()
def git(*args): return subprocess.check_output(['git',*args])
patterns={
 'private-key':rb'-----BEGIN (?:OPENSSH |RSA |EC |DSA |ENCRYPTED )?PRIVATE KEY-----',
 'provider-token':rb'(?:gh[pousr]_[A-Za-z0-9]{20,}|github_pat_[A-Za-z0-9_]{30,}|AKIA[A-Z0-9]{16}|sk-[A-Za-z0-9_-]{24,})',
 'credential-url':rb'[a-zA-Z]+://[^\s/:]+:[^\s/@]+@',
 'literal-secret':rb'(?i)(?:password|passwd|api_key|api-key|secret|token)\s*[=:]\s*[\x22\x27]([^\x22\x27\r\n]{12,})[\x22\x27]',
 'private-infrastructure':rb'(?:/home/[A-Za-z0-9_-]+|192\.168\.\d+\.\d+|10\.\d+\.\d+\.\d+|gx10-[a-z0-9]+)'}
findings=[]; objects={}; sizes=[]
def scan(label,data):
 for typ,p in patterns.items():
  for m in re.finditer(p,data):
   findings.append({'location':label,'line':data[:m.start()].count(b'\n')+1,'type':typ,'fingerprint':'sha256:'+hashlib.sha256(m.group()).hexdigest()[:12]})
for path in root.rglob('*'):
 if '.git' in path.parts or '__pycache__' in path.parts or path.is_symlink() or not path.is_file(): continue
 scan('worktree:'+str(path.relative_to(root)),path.read_bytes())
for line in git('rev-list','--objects','--all','--reflog').decode().splitlines():
 sha,_,name=line.partition(' '); objects[sha]=name
# Include all locally stored objects, even unreachable ones.
allobjs=git('cat-file','--batch-all-objects','--batch-check=%(objectname) %(objecttype) %(objectsize)').decode().splitlines()
counts={}
for line in allobjs:
 sha,typ,size=line.split();counts[typ]=counts.get(typ,0)+1;sizes.append((int(size),typ,sha,objects.get(sha,'')))
 if typ in ('blob','commit','tag'): scan('git:'+sha+':'+objects.get(sha,''),git('cat-file',typ,sha))
for name in ('config','packed-refs','HEAD','FETCH_HEAD','ORIG_HEAD'):
 p=root/'.git'/name
 if p.is_file(): scan('git-metadata:'+name,p.read_bytes())
for folder in ('logs','refs'):
 for p in (root/'.git'/folder).rglob('*'):
  if p.is_file() and not p.is_symlink(): scan('git-metadata:'+str(p.relative_to(root/'.git')),p.read_bytes())
print(json.dumps({'tools':{x:shutil.which(x) for x in ('gitleaks','trufflehog','detect-secrets','bandit','pip-audit','gh')},'object_counts':counts,'commits_reachable':len(git('rev-list','--all').splitlines()),'shallow':git('rev-parse','--is-shallow-repository').decode().strip(),'refs':git('for-each-ref','--format=%(refname) %(objectname)').decode().splitlines(),'largest_objects':sorted(sizes,reverse=True)[:8],'findings':findings},indent=2))
