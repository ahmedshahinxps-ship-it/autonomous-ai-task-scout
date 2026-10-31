#!/usr/bin/env python3
"""Read-only task discovery. No submissions, claims, credentials, or payouts."""
import argparse
import datetime as dt
import html
import json
import sys
from pathlib import Path
from urllib.parse import urlencode, urlparse
from urllib.request import Request, urlopen

FEED = "https://jobbi.org/gigs.json"
TERMS = {
 "documentation": ("documentation", "readme", "docs", "guide", "tutorial"),
 "data": ("csv", "json", "dataset", "schema", "data cleaning", "duplicate"),
 "testing": ("unit test", "regression", "testing", "validation"),
 "simple_code": ("small bug", "bug fix", "python", "refactor"),
}
RISK = ("wallet", "smart contract", "security exploit", "hardware", "staking")
COMPLEX_TITLES = ("integration", "dashboard", "kubernetes", "oauth", "anti-cheat", "security", "deployment", "architecture", "refactor", "migrate", "full-stack")
TRUSTED_CASH_SOURCES = ("algora", "bountyhub")

def load_items(payload):
    if isinstance(payload, dict) and isinstance(payload.get("items"), list):
        return payload["items"]
    if isinstance(payload, list):
        return payload
    raise ValueError("Expected JSON Feed items array")

def fetch_live(min_reward):
    params = urlencode({"lane":"agent","currency":"USD","min_reward":min_reward,"limit":500})
    req = Request(FEED+"?"+params, headers={"User-Agent":"ReadOnlyTaskScout/0.1","Accept":"application/json, application/feed+json"})
    with urlopen(req,timeout=25) as response:
        body = response.read(8_000_001)
    if len(body)>8_000_000:
        raise ValueError("Feed over size limit")
    return load_items(json.loads(body))

def inspect(item, min_reward=20, now=None):
    if not isinstance(item,dict): return None
    meta = item.get("_jobbi")
    if not isinstance(meta,dict): return None
    reward = meta.get("reward")
    if not isinstance(reward,dict): return None
    if str(meta.get("lane","")).lower() != "agent" or meta.get("claims_open") is False: return None
    if str(reward.get("currency","")).upper() != "USD": return None
    try: amount = float(reward.get("amount",0))
    except (ValueError,TypeError): return None
    if not (min_reward <= amount <= 100000000): return None
    expiry = str(meta.get("expires") or "")
    if expiry:
        try:
            end = dt.datetime.fromisoformat(expiry.replace("Z","+00:00"))
            if end.tzinfo is None: end=end.replace(tzinfo=dt.timezone.utc)
            if end < (now or dt.datetime.now(dt.timezone.utc)): return None
        except ValueError: pass
    url = str(item.get("url") or "")
    parsed = urlparse(url)
    if parsed.scheme != "https" or not parsed.hostname: return None
    title = str(item.get("title") or "Untitled")[:180]
    description = str(item.get("content_text") or "")[:1600]
    tags = item.get("tags") or []
    if not isinstance(tags,list): tags=[]
    corpus = (title+" "+description+" "+" ".join(str(t) for t in tags)).lower()
    scores = {name:sum(term in corpus for term in terms) for name,terms in TERMS.items()}
    category = max(scores,key=scores.get)
    hits = scores[category]
    if not hits: category="other"
    risky = any(term in corpus for term in RISK)
    source = str(meta.get("source") or "unknown").lower()[:80]
    published = str(item.get("date_published") or "")
    age_days = None
    if published:
        try:
            pub = dt.datetime.fromisoformat(published.replace("Z","+00:00"))
            if pub.tzinfo is None: pub = pub.replace(tzinfo=dt.timezone.utc)
            age_days = max(0, ((now or dt.datetime.now(dt.timezone.utc)) - pub).days)
        except ValueError:
            pass
    title_lower = title.lower()
    title_hits = sum(term in title_lower for group in TERMS.values() for term in group)
    title_complex = any(term in title_lower for term in COMPLEX_TITLES)
    state = str(meta.get("payment_state") or "unknown").lower()
    acceptance = str(meta.get("acceptance_type") or "unknown").lower()
    score = min(25, hits*7) + (10 if state=="escrowed" else -8)
    score += 8 if category in ("documentation","data","testing") else 0
    score += 8 if "machine" in acceptance or "automatic" in acceptance else 0
    score -= 30 if risky else 0
    score -= 20 if category=="other" else 0
    score += min(16, title_hits * 8)
    score += 10 if source in TRUSTED_CASH_SOURCES else 0
    score -= 15 if source == "issuehunt" else 0
    score -= 28 if title_complex else 0
    if age_days is not None:
        score += 14 if age_days <= 14 else 7 if age_days <= 60 else -18 if age_days > 365 else 0
    # These weights identify leads to investigate, never prove funding or payout.
    return {"title":title,"url":url,"source":source,
      "published":published, "age_days":age_days,
      "payment_rail":str(reward.get("rail") or "unknown")[:40],
      "payout_grade":str(meta.get("payout_grade") or "unknown")[:8],
      "reward_usd":amount,"category":category,"score":max(0,min(100,score)),
      "payment_state":state,"acceptance_type":acceptance,"risk_flag":risky,
      "automated_submission_permitted":"NOT VERIFIED","egypt_payout":"NOT VERIFIED"}

def report(items, min_reward=20):
    candidates=[x for item in items if (x:=inspect(item,min_reward)) is not None]
    candidates.sort(key=lambda x:(x["score"],x["reward_usd"]),reverse=True)
    return {"generated_utc":dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds"),
      "feed":FEED,"scanned":len(items),"candidate_count":len(candidates),
      "submissions_enabled":False,"payments_enabled":False,
      "notice":"Unverified leads, not accepted jobs or guaranteed earnings.",
      "candidates":candidates[:150]}

def html_report(data,demo=False):
    e=lambda s:html.escape(str(s),quote=True)
    cards=[]
    for x in data["candidates"][:75]:
        search=e((x["title"]+" "+x["category"]+" "+x["source"]).lower())
        cards.append('<article class="card" data-search="'+search+'"><div class="row"><span>'+
          e(x["category"])+'</span><b>$'+format(x["reward_usd"],",.2f")+'</b></div><h3>'+
          e(x["title"])+'</h3><p>Source: '+e(x["source"])+' · Heuristic fit '+str(x["score"])+
          '/100 · Funding: '+e(x["payment_state"])+'</p><p>AI permission, task availability and bank payout unverified.</p>'+
          '<a href="'+e(x["url"])+'" target="_blank" rel="noopener noreferrer">View original listing</a></article>')
    banner="DEMO DATA — NOT REAL TASKS" if demo else "LIVE FEED — ALL LEADS UNVERIFIED"
    return """<!doctype html><html lang="en"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>AI Task Scout</title><style>body{font-family:system-ui,sans-serif;background:#f5f7fb;color:#182333}
main{max-width:900px;margin:35px auto;padding:0 20px}.banner{padding:14px;background:#fff2d3;border-radius:10px;font-weight:bold}
.card{background:white;border:1px solid #dce2ec;border-radius:12px;padding:18px;margin:12px 0}
.row{display:flex;justify-content:space-between}.card p,small{color:#586477;font-size:13px}
input{font:inherit;padding:13px;width:100%;box-sizing:border-box;border:1px solid #dce2ec;border-radius:10px}
a{color:#2858b5}</style><main><div class="banner">"""+e(banner)+""" — Submission and payouts OFF.</div><h1>Autonomous AI Task Scout</h1><p>Scanned """+str(data["scanned"])+""" records. Found """+str(data["candidate_count"])+""" candidate leads. No revenue has been earned.</p><input id="q" placeholder="Search tasks and categories"><section>"""+("".join(cards) or "<p>No matching opportunities.</p>")+"""</section><small>Generated """+e(data["generated_utc"])+""" UTC. Jobbi is an index; verify conditions with the original marketplace.</small></main><script>
document.getElementById('q').addEventListener('input',e=>{const q=e.target.value.toLowerCase();document.querySelectorAll('.card').forEach(el=>el.hidden=!el.dataset.search.includes(q))})
</script></html>"""

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--fixture")
    p.add_argument("--output",default="output")
    p.add_argument("--min-reward",type=float,default=20)
    a=p.parse_args()
    if not 0<=a.min_reward<=100000000: p.error("Invalid min-reward")
    try:
        items=load_items(json.loads(Path(a.fixture).read_text("utf-8"))) if a.fixture else fetch_live(a.min_reward)
        data=report(items,a.min_reward)
        path=Path(a.output);path.mkdir(parents=True,exist_ok=True)
        (path/"opportunities.json").write_text(json.dumps(data,indent=2),encoding="utf-8")
        (path/"index.html").write_text(html_report(data,bool(a.fixture)),encoding="utf-8")
        print("Scanned",len(items),"found",data["candidate_count"],"read-only candidate leads")
        return 0
    except Exception as exc:
        print("Scout failure:",exc,file=sys.stderr);return 1

if __name__=="__main__": sys.exit(main())
