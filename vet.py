#!/usr/bin/env python3
"""Read-only vetting of GitHub issues. No claims, submissions, or payouts."""
import argparse
import datetime as dt
import html
import json
import re
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.parse import urlparse
from urllib.request import Request, urlopen

DOC = re.compile(r'\b(readme|docs?|documentation|documenting|guide|tutorial|typo|spelling)\b', re.I)
DATA = re.compile(r'\b(csv|dataset|data cleaning|data quality|deduplicat\w*|schema|json parsing|data validation)\b', re.I)
TEST = re.compile(r'\b(unit tests?|test coverage|regression tests?)\b', re.I)
HARD = re.compile(r'\b(integration|integrate|dashboard|security|exploit|migration|migrate|refactor|architecture|port component|implement|oauth|hardware)\b', re.I)
SLUG = re.compile(r'^[A-Za-z0-9_.-]{1,100}$')

def issue_key(url):
    """Parse supported issue links, never use their hosts as HTTP destinations."""
    parsed = urlparse(str(url))
    if parsed.scheme != 'https':
        return None
    host = (parsed.hostname or '').lower()
    parts = [p for p in parsed.path.split('/') if p]
    if host in ('github.com','www.github.com') and len(parts)==4 and parts[2]=='issues':
        owner, repo, _, number = parts
    elif host=='oss.issuehunt.io' and len(parts)==5 and parts[0]=='r' and parts[3]=='issues':
        _,owner,repo,_,number = parts
    else:
        return None
    if owner in ('.','..') or repo in ('.','..') or not SLUG.fullmatch(owner) or not SLUG.fullmatch(repo):
        return None
    if not number.isascii() or not number.isdigit() or not 0<int(number)<=999999999:
        return None
    return owner,repo,int(number)

def classification(title):
    title = str(title)
    if HARD.search(title): return 'complex'
    for label,rx in (('documentation',DOC),('data',DATA),('testing',TEST)):
        if rx.search(title): return label
    return 'unclear'

def github_issue(owner,repo,number):
    # issue_key validates all arguments and this request uses only a fixed host.
    url=f'https://api.github.com/repos/{owner}/{repo}/issues/{number}'
    req=Request(url,headers={'User-Agent':'ReadOnlyTaskScoutVetting/0.2',
                             'Accept':'application/vnd.github+json'})
    with urlopen(req,timeout=12) as response: body=response.read(128001)
    if len(body)>128000: raise ValueError('Oversized issue metadata')
    return json.loads(body)

def vet_one(lead,fetcher=github_issue,now=None):
    now=now or dt.datetime.now(dt.timezone.utc)
    title=str(lead.get('title') or '')
    shape=classification(title)
    result={'title':title[:180],'url':str(lead.get('url') or ''),
            'reward_usd':lead.get('reward_usd'),'task_type':shape,
            'state':'unverified','reasons':[],'payment':'NOT VERIFIED',
            'ai_submissions':'NOT VERIFIED','egypt_payout':'NOT VERIFIED'}
    key=issue_key(result['url'])
    if not key:
        result['reasons'].append('Original listing is not a supported GitHub issue URL')
        return result
    if shape in ('complex','unclear'):
        result['reasons'].append('Title does not indicate narrow docs/data/testing work')
        return result
    try:
        issue=fetcher(*key)
        if not isinstance(issue,dict): raise ValueError('Unexpected GitHub response')
    except (HTTPError,URLError,TimeoutError,ValueError,OSError) as exc:
        result['reasons'].append('Could not verify GitHub issue: '+type(exc).__name__)
        return result
    result['state']='review'
    if issue.get('state')!='open': result['reasons'].append('Issue is not open')
    if issue.get('locked'): result['reasons'].append('Issue is locked')
    if issue.get('assignees'): result['reasons'].append('Issue is assigned')
    if int(issue.get('comments') or 0)>20:
        result['reasons'].append('More than 20 comments: potentially crowded')
    for field,cutoff,label in (('created_at',365,'Issue is over one year old'),
                               ('updated_at',180,'No activity in six months')):
        raw=issue.get(field)
        if not raw:
            result['reasons'].append('Missing GitHub '+field)
            continue
        try:
            stamp=dt.datetime.fromisoformat(str(raw).replace('Z','+00:00'))
            if stamp.tzinfo is None: stamp=stamp.replace(tzinfo=dt.timezone.utc)
            if (now-stamp).days>cutoff: result['reasons'].append(label)
        except ValueError: result['reasons'].append('Invalid GitHub '+field)
    result['state']='preliminary-review' if not result['reasons'] else 'skip'
    if not result['reasons']:
        result['reasons'].append('Basic checks passed; funding, AI permission and payout still unverified')
    return result

def vet_report(payload,max_checks=12,fetcher=github_issue,now=None):
    leads=payload.get('candidates',[])
    if not isinstance(leads,list): raise ValueError('Expected candidates list')
    reviewed=[]
    for lead in leads:
        if len(reviewed)>=max_checks: break
        if not isinstance(lead,dict): continue
        if classification(lead.get('title')) in ('complex','unclear'): continue
        if not issue_key(lead.get('url')): continue
        reviewed.append(vet_one(lead,fetcher=fetcher,now=now))
    states=('preliminary-review','skip','unverified')
    return {'generated_utc':dt.datetime.now(dt.timezone.utc).isoformat(timespec='seconds'),
            'input_candidate_count':len(leads),'issues_checked':len(reviewed),
            'counts':{s:sum(x['state']==s for x in reviewed) for s in states},
            'reviewed':reviewed,'notice':'Basic issue checks only. NO tasks are approved or paid. AI submissions are not authorised.'}

def make_html(data):
    e=lambda s:html.escape(str(s),quote=True)
    cards=[]
    for row in data['reviewed']:
        reasons='; '.join(row['reasons'])
        cards.append('<article><h3>'+e(row['title'])+'</h3><p><b>'+e(row['state'])+
          '</b> · '+e(row['task_type'])+' · $'+e(row['reward_usd'])+
          '</p><p>'+e(reasons)+'</p><a href="'+e(row['url'])+
          '" target="_blank" rel="noopener noreferrer">Original issue</a></article>')
    return ('<!doctype html><html lang="en"><meta charset="utf-8"><title>Vetted Task Leads</title>'
      '<meta name="viewport" content="width=device-width,initial-scale=1">'
      '<style>body{font:16px system-ui;background:#f7f8fc;color:#182333}'
      'main{max-width:850px;margin:30px auto;padding:0 20px}'
      'article{background:white;border:1px solid #ddd;border-radius:12px;padding:16px;margin:12px 0}'
      'p{color:#4c5869}a{color:#2254ad}</style><main><h1>Preliminary Task Vetting</h1>'
      '<p>Issues checked: '+str(data['issues_checked'])+' · Basic checks passed: '+
      str(data['counts']['preliminary-review'])+'</p>'
      '<p><b>Not approved for autonomous work or payment.</b> '
      'AI participation and Egyptian banking eligibility are still unverified.</p>'+
      ''.join(cards)+'</main></html>')

def main():
    p=argparse.ArgumentParser()
    p.add_argument('--input',default='output/opportunities.json')
    p.add_argument('--output',default='output')
    p.add_argument('--max-checks',type=int,default=12)
    args=p.parse_args()
    if args.max_checks<0 or args.max_checks>30:
        p.error('max-checks must be 0–30 for public GitHub API rate limits')
    payload=json.loads(Path(args.input).read_text(encoding='utf-8'))
    vetted=vet_report(payload,max_checks=args.max_checks)
    out=Path(args.output);out.mkdir(parents=True,exist_ok=True)
    (out/'vetting.json').write_text(json.dumps(vetted,indent=2),encoding='utf-8')
    (out/'vetting.html').write_text(make_html(vetted),encoding='utf-8')
    print(f"Checked {vetted['issues_checked']} issues; {vetted['counts']['preliminary-review']} passed basic checks")

if __name__=='__main__':
    main()
