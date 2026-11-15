"""One-off guard-railed repair of three placeholder photo links in Papiernia.
Uses the existing SEO API secret in GitHub Actions. Never edits image src.
"""
import json, os, re, sys, urllib.parse, urllib.request
from pathlib import Path

BASE = 'https://papiernia.net.pl'
SLUG = 'zlota-torebka-z-cukierkami-na-swieta-personalizowana-etykieta'
WHY = 'Wlasciciel zatwierdzil naprawe 3 linkow URL_ZDJECIA1-3 w audycie Ahrefs z 2026-11-15'
REPORT = Path('automation/reports/ahrefs-links-20261115.json')
API_KEY = os.environ.get('PAPIERNIA_SEO_API_KEY', '')
summary = {'product': BASE + '/' + SLUG, 'status': 'not_started', 'changed': 0, 'links': [],
           'poradnik': 'Nie zmieniono: brak endpointu Topic w SEO API v3'}

def req(method, path, payload=None):
    data = json.dumps(payload, ensure_ascii=False).encode('utf-8') if payload is not None else None
    request = urllib.request.Request(BASE + path, data=data, method=method,
        headers={'X-Papiernia-SEO-Key': API_KEY, 'Content-Type': 'application/json',
                 'Accept': 'application/json'})
    with urllib.request.urlopen(request, timeout=35) as response:
        return json.load(response)

def find_id(obj):
    if isinstance(obj, dict):
        for key in ('productId', 'ProductId', 'entityId', 'EntityId', 'id', 'Id'):
            val = obj.get(key)
            if isinstance(val, int) and val > 0: return val
            if isinstance(val, str) and val.isdecimal() and int(val) > 0: return int(val)
        for val in obj.values():
            found = find_id(val)
            if found: return found
    if isinstance(obj, list):
        for val in obj:
            found = find_id(val)
            if found: return found
    return None

def find_field(obj, target):
    if isinstance(obj, dict):
        for key, value in obj.items():
            if key.lower() == target.lower() and isinstance(value, str): return value
        for val in obj.values():
            found = find_field(val, target)
            if found is not None: return found
    if isinstance(obj, list):
        for val in obj:
            found = find_field(val, target)
            if found is not None: return found
    return None

ANCHOR = re.compile(r'(?P<before><a\b[^>]*?\bhref\s*=\s*(?P<quote>["\']))(?P<old>(?:https?://papiernia\.net\.pl)?/?URL_ZDJECIA[123])(?P=quote)(?P<attrs>[^>]*>)(?P<inner>.*?)(?P<end></a\s*>)', re.I | re.S)
IMAGE = re.compile(r'<img\b[^>]*?\bsrc\s*=\s*(["\'])(.*?)\1', re.I | re.S)

def repaired_html(html):
    edits = []
    def fix(match):
        old = match.group('old')
        image = IMAGE.search(match.group('inner'))
        if not image: raise RuntimeError('Brak osadzonego obrazka dla ' + old)
        new = image.group(2).strip()
        url = urllib.parse.urlparse(new)
        if not (new.startswith('/images/') or new.startswith('images/') or
                (url.scheme == 'https' and url.hostname == 'papiernia.net.pl' and url.path.startswith('/images/'))):
            raise RuntimeError('Nieznany adres docelowego obrazka dla ' + old)
        if 'URL_ZDJECIA' in new: raise RuntimeError('Adres docelowy jest placeholderem')
        edits.append({'from': old, 'to': new})
        return (match.group('before') + new + match.group('quote') +
                match.group('attrs') + match.group('inner') + match.group('end'))
    updated = ANCHOR.sub(fix, html)
    names = sorted(re.findall(r'URL_ZDJECIA[123]', html, re.I))
    changed = sorted(re.findall(r'URL_ZDJECIA[123]', '\n'.join(x['from'] for x in edits), re.I))
    if names != ['URL_ZDJECIA1', 'URL_ZDJECIA2', 'URL_ZDJECIA3'] or changed != names:
        raise RuntimeError('Nie potwierdzono dokladnie 3 bezpiecznych linkow. Wykryte: %s, kandydaci: %s' % (names, changed))
    if any(x in updated for x in ('URL_ZDJECIA1', 'URL_ZDJECIA2', 'URL_ZDJECIA3')):
        raise RuntimeError('W opisie pozostaly placeholdery')
    return updated, edits

def main():
    if not API_KEY: raise RuntimeError('Brak sekretu PAPIERNIA_SEO_API_KEY')
    resolved = req('GET', '/papiernia-seo-api/v1/Resolve?' +
                   urllib.parse.urlencode({'url': BASE + '/' + SLUG}))
    product_id = find_id(resolved)
    if not product_id: raise RuntimeError('Resolve nie zwrocil identyfikatora produktu')
    summary['product_id'] = product_id
    before = req('GET', '/papiernia-seo-api/v3/ProductSnapshot/' + str(product_id))
    html = find_field(before, 'fullDescription')
    if not isinstance(html, str) or not html.strip(): raise RuntimeError('Brak pelnego opisu HTML')
    updated, edits = repaired_html(html)
    summary['links'] = edits
    payload = {'fullDescription': updated, 'reason': WHY}
    preview = req('POST', '/papiernia-seo-api/v3/PreviewProductSeo/' + str(product_id), payload)
    token = find_field(preview, 'approvalToken')
    if not token: raise RuntimeError('Preview nie zwrocilo tokenu, brak zapisu')
    req('PUT', '/papiernia-seo-api/v3/CommitProductSeo/' + str(product_id),
        {**payload, 'approvalToken': token})
    after = req('GET', '/papiernia-seo-api/v3/ProductSnapshot/' + str(product_id))
    if find_field(after, 'fullDescription') != updated:
        raise RuntimeError('Nie mozna potwierdzic zapisu; wymaga kontroli')
    summary['changed'] = 3
    summary['status'] = 'verified_applied'

if __name__ == '__main__':
    try: main()
    except Exception as exc:
        summary['status'] = 'failed_or_unverified'
        summary['error'] = str(exc)[:700]
        print('ERROR:', summary['error'], file=sys.stderr)
    finally:
        REPORT.parent.mkdir(parents=True, exist_ok=True)
        REPORT.write_text(json.dumps(summary, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
        print(json.dumps({k: v for k, v in summary.items() if k != 'links'}, ensure_ascii=False))
    if summary['status'] != 'verified_applied': sys.exit(1)
