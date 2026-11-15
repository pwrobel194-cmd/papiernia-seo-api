"""Read-only diagnosis of actual markup around the second H1 on public pages."""
import json, re, urllib.request
from pathlib import Path
urls=[
 'https://papiernia.net.pl/tani-upominek-dla-klientow-na-swieta',
 'https://papiernia.net.pl/cukierki-dla-gosci-weselnych',
 'https://papiernia.net.pl/poradnik',
 'https://papiernia.net.pl/kategorie'
]
rows=[]
for u in urls:
    row={'url':u}
    try:
        req=urllib.request.Request(u,headers={'User-Agent':'Mozilla/5.0 (compatible; Papiernia-H1-Diagnostic/1.0)'})
        with urllib.request.urlopen(req,timeout=35) as r: source=r.read().decode('utf-8','replace')
        h1=list(re.finditer(r'<h1\b[^>]*>.*?</h1\s*>',source,re.I|re.S))
        row['count']=len(h1)
        row['context']=[]
        for m in h1:
            left=source[max(0,m.start()-1100):m.start()]
            right=source[m.end():m.end()+350]
            row['context'].append({
                'h1_markup':source[m.start():m.end()][:500],
                'previous_markup':left[-1100:],
                'next_markup':right[:350]
            })
    except Exception as exc: row['error']=str(exc)
    rows.append(row)
p=Path('automation/reports/ahrefs-h1-dom-20261115.json')
p.parent.mkdir(parents=True,exist_ok=True)
p.write_text(json.dumps({'mode':'read_only','pages':rows},ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
