"""ONE-TIME: guard-railed category H1 repair + read-only topic audit (2026-11-15).
Only /kategorie Description is eligible for write, via existing SEO API v3.
No product, other category, Topic, meta, image, slug, or price edits.
"""
import os, re, json, sys, difflib, html, urllib.parse, urllib.request, urllib.error
from datetime import datetime, timezone
from pathlib import Path

BASE="https://papiernia.net.pl"
API=f"{BASE}/papiernia-seo-api/v3"
KEY=os.environ.get("PAPIERNIA_SEO_API_KEY", "")
REPORT=Path("automation/reports/ahrefs-h1-remediation-20261115.json")
PHRASE="Personalizowane podziękowania dla gości i upominki na każdą okazję"
TOPICS=[
 "poradnik",
 "ile-podziekowan-dla-gosci-zamowic",
 "co-napisać-na-podziekowaniu-dla-gosci",
 "podziekowania-dla-gosci-do-5-zl",
 "jak-wybrac-upominki-dla-gosci-na-chrzest",
 "jak-wybrac-podziekowania-dla-gosci-na-komunie",
 "jak-zaplanowac-podziekowania-na-urodziny",
 "jak-wybrac-upominki-dla-klientow-firmowych",
 "jakie-podziekowania-dla-gosci-weselnych-wybrac",
]
report={"timestamp_utc":datetime.now(timezone.utc).isoformat(),"scope":"/kategorie and 9 informational topics",
 "product_changes":0, "topic_changes":0, "category":{"status":"not_started"},
 "topics":[]}
def request(method,path,payload=None,authenticate=True):
    headers={"Accept":"application/json","User-Agent":"Papiernia-H1-guarded-audit/1.0"}
    if authenticate:
        if not KEY: raise RuntimeError("Missing existing GitHub Actions SEO API secret")
        headers["X-Papiernia-SEO-Key"]=KEY
    data=None
    if payload is not None:
        data=json.dumps(payload,ensure_ascii=False).encode("utf-8")
        headers["Content-Type"]="application/json"
    req=urllib.request.Request(BASE+path, data=data, headers=headers, method=method)
    with urllib.request.urlopen(req,timeout=40) as res: return json.loads(res.read().decode("utf-8"))
def page_html(slug):
    url=BASE+"/"+urllib.parse.quote(slug,safe="/-")
    req=urllib.request.Request(url,headers={"User-Agent":"Mozilla/5.0 (compatible; Papiernia-H1-Audit/1.0)","Cache-Control":"no-cache"})
    with urllib.request.urlopen(req,timeout=35) as res: return res.read().decode("utf-8","replace")
def h1s(markup):
    result=[]
    for m in re.finditer(r"<h1\b[^>]*>(.*?)</h1\s*>",markup or "",re.I|re.S):
        s=html.unescape(re.sub(r"<[^>]+>","",m.group(1)))
        result.append(" ".join(s.split()))
    return result
def pick(obj,key):
    if not isinstance(obj,dict): return None
    for k,v in obj.items():
        if k.casefold()==key.casefold(): return v
    return None
def resolve_category():
    params=urllib.parse.urlencode({"url": BASE+"/kategorie"})
    obj=request("GET","/papiernia-seo-api/v1/Resolve?"+params)
    if not isinstance(obj,dict): raise RuntimeError("Unexpected Resolve payload type")
    report["category"]["resolve_shape"]={k:v for k,v in obj.items() if isinstance(v,(str,int,bool)) and k.lower() not in ("key","token","password","secret")}
    # v1 Resolve implementations may have nested response, but only use a category-specific ID.
    def find(d):
        if isinstance(d,dict):
            for k in ("categoryId","CategoryId"):
                x=d.get(k)
                if isinstance(x,int) and x>0:return x
            kind=" ".join(str(d.get(k,"")) for k in ("entityType","EntityType","type","Type","entityName","EntityName"))
            if "categor" in kind.lower():
                for k in ("id","Id","entityId","EntityId"):
                    x=d.get(k)
                    if isinstance(x,int) and x>0:return x
            for v in d.values():
                z=find(v)
                if z:return z
        if isinstance(d,list):
            for v in d:
                z=find(v)
                if z:return z
        return None
    category_id=find(obj)
    if not category_id:
        # A neutral numeric Resolve result is allowed only after CategorySnapshot verifies SeName.
        for k in ("id","Id","entityId","EntityId"):
            x=obj.get(k)
            if isinstance(x,int) and x>0:category_id=x;break
    if not category_id: raise RuntimeError("No resolvable category ID; not guessing")
    return category_id
def safely_rewrite(s):
    found=list(re.finditer(r"(<h1\b[^>]*>)(.*?)(</h1\s*>)",s,re.I|re.S))
    if len(found)!=1: raise RuntimeError(f"Expected precisely one H1 inside category.Description, got {len(found)}")
    m=found[0]
    inner=" ".join(html.unescape(re.sub(r"<[^>]+>","",m.group(2))).split())
    if inner != PHRASE: raise RuntimeError("Unexpected H1 in category Description: "+inner[:150])
    replacement=re.sub(r"^<h1\b","<h2",m.group(1),count=1,flags=re.I)+m.group(2)+re.sub(r"^</h1\b","</h2",m.group(3),count=1,flags=re.I)
    out=s[:m.start()]+replacement+s[m.end():]
    if out==s or h1s(out): raise RuntimeError("Rewrite did not leave zero extra H1")
    expected=s[:m.start()]+replacement+s[m.end():]
    if out!=expected: raise RuntimeError("Unexpected HTML difference")
    old_imgs=re.findall(r"<img\b[^>]*\bsrc\s*=\s*(['\"])(.*?)\1",s,re.I|re.S)
    new_imgs=re.findall(r"<img\b[^>]*\bsrc\s*=\s*(['\"])(.*?)\1",out,re.I|re.S)
    if old_imgs!=new_imgs: raise RuntimeError("Image URLs changed unexpectedly")
    return out
def run_category():
    status=report["category"]
    current_public=h1s(page_html("kategorie"))
    status["public_h1_before"]=current_public
    if len(current_public)==1 and current_public[0]=="Podziękowania dla Gości":
        status["status"]="already_fixed"
        return
    if len(current_public)!=2: raise RuntimeError("Public /kategorie has unexpected H1 count; aborting write")
    id=resolve_category()
    status["category_id"]=id
    snapshot=request("GET",f"/papiernia-seo-api/v3/CategorySnapshot/{id}")
    slug=pick(snapshot,"seName")
    if slug is None:
        raise RuntimeError("Snapshot did not include SeName. Refuse category write without ID verification.")
    if str(slug).strip().lower()!="kategorie":raise RuntimeError("Wrong category slug in snapshot: "+str(slug))
    desc=pick(snapshot,"description")
    if not isinstance(desc,str) or not desc:raise RuntimeError("Category snapshot missing full Description")
    rewritten=safely_rewrite(desc)
    reason="Wlasciciel zatwierdzil korekte dodatkowego H1 do H2 na /kategorie (Ahrefs 2026-11-15)"
    payload={"description":rewritten,"reason":reason}
    status["status"]="preview_requested"
    preview=request("POST",f"/papiernia-seo-api/v3/PreviewCategorySeo/{id}",payload)
    token=pick(preview,"approvalToken")
    if not isinstance(token,str) or not token:raise RuntimeError("Preview returned no approvalToken; no write")
    # Guard against inconsistent/unexpected preview.
    before=pick(preview,"before"); after=pick(preview,"after")
    if isinstance(before,dict):
        prevdesc=pick(before,"description")
        if prevdesc is not None and prevdesc!=desc:raise RuntimeError("Preview baseline differed from snapshot")
    if isinstance(after,dict):
        newdesc=pick(after,"description")
        if newdesc is not None and newdesc!=rewritten:raise RuntimeError("Preview update differed from requested description")
    status["status"]="preview_verified"
    # Exact one-tag change with prior user authorization, protected by 15-minute approval token.
    request("PUT",f"/papiernia-seo-api/v3/CommitCategorySeo/{id}",{**payload,"approvalToken":token})
    status["status"]="commit_returned"
    again=request("GET",f"/papiernia-seo-api/v3/CategorySnapshot/{id}")
    if pick(again,"description")!=rewritten:
        raise RuntimeError("Commit returned but API read-back HTML does not match expected. Needs investigation.")
    for field in ("name","metaTitle","metaDescription","metaKeywords","seName"):
        beforeval=pick(snapshot,field);afterval=pick(again,field)
        if beforeval!=afterval:raise RuntimeError("Unexpected collateral change of "+field)
    status["status"]="verified_saved"
    status["public_h1_after"]=h1s(page_html("kategorie"))
    status["only_change"]="h1 to h2 in category.Description"
def run_topics():
    for slug in TOPICS:
        record={"url":BASE+"/"+urllib.parse.quote(slug,safe="/-"),"status":"not_modified_no_topic_endpoint"}
        try:
            h=h1s(page_html(slug))
            record["h1_now"]=h
            record["h1_count"]=len(h)
            if len(h)==1:record["status"]="already_single_h1"
            elif len(h)==2:record["recommended"]="retain first, change H1 tags to H2 only for second H1 in topic body"
            else:record["recommended"]="manual HTML inspection required"
        except Exception as ex:
            record["error"]=str(ex)[:250]
        report["topics"].append(record)
def main():
    try: run_category()
    except Exception as exc:
        report["category"]["error"]=str(exc)[:500]
        if report["category"]["status"] not in ("verified_saved","already_fixed"):
            report["category"]["status"]="failed_or_unverified"
    try: run_topics()
    except Exception as exc:report["topic_error"]=str(exc)[:400]
if __name__=="__main__":
    try:main()
    finally:
        REPORT.parent.mkdir(parents=True,exist_ok=True)
        REPORT.write_text(json.dumps(report,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
        print(json.dumps({"category":report["category"],"topics":len(report["topics"]),"topics_modified":report["topic_changes"]},ensure_ascii=False))
