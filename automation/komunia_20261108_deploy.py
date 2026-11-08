"""Guarded one-time production deployment; based on 2026-11-08 owner-approved SEO plan.
All 3 sources preflighted before any COMMIT; each uses v3 Preview -> Commit, checks readback.
Never changes URL, prices, stock, image metadata or media order.
"""
import runpy,hashlib,json,pathlib,re,sys,time
a=runpy.run_path("automation/komunia_20261108_preview.py")
session=a["session"]; ROOT=a["ROOT"]; TARGETS=a["TARGETS"]
snap=a["snapshot"]; guard=a["guarded_new"]; field=a["field"]
EXPECTED={
 17:{"name":"5bbb779c4365213a13ab","metaTitle":"6972f66bf5723e17c4f4","metaDescription":"c1cb563166b7a7f89411"},
 4897:{"name":"32c94d4783e100ce5a39","metaTitle":"32c94d4783e100ce5a39","metaDescription":"e516014e768bb1b9f155"},
 4912:{"name":"ffb99202fc6cb6c0e32f","metaTitle":"01b507ff74da64634458","metaDescription":"e391f0ab7c41c9622ade"}
}
out=pathlib.Path("audit/komunia-20261108/deploy");out.mkdir(parents=True,exist_ok=True)
report=[]
def save(): (out/"verification.json").write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding="utf-8")
def expected_before(t,now):
 for k,h in EXPECTED[t["id"]].items():
  value=str(field(now,k))
  assert hashlib.sha256(value.encode()).hexdigest().startswith(h),f"Concurrent field change for {t['id']}, {k}; refusing overwrite"
def call(method,path,payload):
 r=getattr(session,method)(f"{ROOT}/{path}",json=payload,timeout=55)
 r.raise_for_status()
 data=r.json()
 if data.get("ok") is False or data.get("success") is False:raise RuntimeError("API returned failed result for "+path)
 return data
def main():
 preflights=[]
 # ALL previews must succeed before any write.
 for t in TARGETS:
  now=snap(t);expected_before(t,now)
  payload,old,new=guard(t,now)
  preview=call("post",f"Preview{t['type']}Seo/{t['id']}",payload)
  assert preview.get("dryRun") is True,"Preview not marked as dry-run"
  token=preview.get("approvalToken",preview.get("ApprovalToken"))
  assert token,"Missing approvalToken; abort all writes"
  preflights.append((t,now,payload,old,new,token))
  print(json.dumps({"id":t["id"],"step":"PREFLIGHT_OK","changedFields":list(payload)},ensure_ascii=False))
 # Commit category first (category API had no prior live-commit test); stop on error.
 for t,now,payload,old,new,token in preflights:
  record={"id":t["id"],"entity":t["type"],"step":"COMMIT_ATTEMPTED"}
  report.append(record);save()
  commit=call("put",f"Commit{t['type']}Seo/{t['id']}",{**payload,"approvalToken":token})
  after=snap(t)
  for name in payload:
   if name in ("reason",):continue
   assert field(after,name)==payload[name],f"Readback mismatch: {t['id']} {name}"
  k="description" if t["type"]=="Category" else "fullDescription"
  after_html=field(after,k) or ""
  assert after_html==new,"Full HTML changed unexpectedly"
  assert re.findall("<img[^>]*>",old,re.I)==re.findall("<img[^>]*>",after_html,re.I)
  assert re.findall("<a[^>]*>",old,re.I)==re.findall("<a[^>]*>",after_html,re.I)
  for key in ("metaKeywords","seName"):
   assert field(after,key)==field(now,key),f"Protected field changed: {t['id']} {key}"
  record.update({"step":"APPLIED_VERIFIED","changedFields":[x for x in payload if x!="reason"],
    "before":{k:field(now,k) for k in ("name","metaTitle","metaDescription")},
    "after":{k:field(after,k) for k in ("name","metaTitle","metaDescription")},
    "beforeHtmlSha256":hashlib.sha256(old.encode()).hexdigest(),
    "afterHtmlSha256":hashlib.sha256(after_html.encode()).hexdigest(),
    "imgTagsIdentical":len(re.findall("<img[^>]*>",old,re.I)),
    "anchorTagsIdentical":len(re.findall("<a[^>]*>",old,re.I))})
  save()
  print(json.dumps({"id":t["id"],"status":"APPLIED_VERIFIED","images":record["imgTagsIdentical"],"anchors":record["anchorTagsIdentical"]},ensure_ascii=False))
if __name__=="__main__":
 try:main()
 except Exception as e:
  report.append({"step":"ERROR","error":str(e)[:400]});save()
  print(str(e)[:400],file=sys.stderr)
  raise
