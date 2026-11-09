#!/usr/bin/env python3
"""Bounded source snapshots and review candidates. No model, scheduler or sender."""
import argparse
from contextlib import contextmanager
from datetime import datetime, timezone, timedelta
import hashlib
from html.parser import HTMLParser
import json
import os
from pathlib import Path
import re
import subprocess
import time
from urllib.parse import urljoin, urlsplit
import uuid

ROOT = Path(__file__).resolve().parents[1]
MAX_BYTES = 6_000_000
MAX_SOURCES = 16
TIMEOUT = 20
RUN_SECONDS = 240
ALLOWED_HOSTS = {'www.gov.za', 'gov.za', 'justice.gov.za', 'www.justice.gov.za', 'inforegulator.org.za'}


def utc():
    return datetime.now(timezone.utc).isoformat()


def sha(data):
    return hashlib.sha256(data).hexdigest()


def read(path):
    return json.loads(Path(path).read_text())


def write(path, value):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_name(path.name + '.' + uuid.uuid4().hex + '.tmp')
    tmp.write_text(json.dumps(value, ensure_ascii=False, indent=2) + '\n')
    os.replace(tmp, path)


def safe_url(url):
    p = urlsplit(url)
    if p.scheme != 'https' or p.hostname not in ALLOWED_HOSTS or p.username or p.password or p.port not in (None, 443):
        raise ValueError('URL outside public HTTPS source allowlist')
    if p.query or p.fragment:
        raise ValueError('Fetch URLs must not contain query parameters or fragments')
    return url


class Article(HTMLParser):
    """Only the article; navigation/cookie/footer noise is not a law change."""
    def __init__(self):
        super().__init__()
        self.depth = 0
        self.skip = 0
        self.found = False
        self.words = []
        self.links = []

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if tag == 'article':
            self.depth += 1
            self.found = True
        if self.depth and tag in ('script', 'style'):
            self.skip += 1
        if self.depth and not self.skip and tag == 'a' and attrs.get('href'):
            self.links.append(attrs['href'])

    def handle_endtag(self, tag):
        if tag in ('script', 'style') and self.skip:
            self.skip -= 1
        if tag == 'article' and self.depth:
            self.depth -= 1

    def handle_data(self, text):
        if self.depth and not self.skip:
            self.words.append(text)


def comparison(source, body):
    if source['format'] == 'pdf':
        if not body.startswith(b'%PDF-'):
            raise ValueError('Expected PDF, received another body (possibly an error page)')
        return {'kind': 'raw_pdf_hash', 'sha256': sha(body)}
    parser = Article()
    parser.feed(body.decode('utf-8', errors='strict'))
    text = ' '.join(' '.join(parser.words).split())
    if not parser.found or len(text) < 80:
        raise ValueError('Expected a substantive government article; no baseline update')
    return {'kind': 'normalized_article_and_links', 'text': text,
            'links': sorted({urljoin(source['url'], link) for link in parser.links})}


def validate_watchlist(config):
    sources = config['sources']
    if config.get('schema_version') != 1 or not sources or len(sources) > MAX_SOURCES:
        raise ValueError('Invalid or oversized watchlist')
    ids = set()
    for source in sources:
        if not re.fullmatch(r'[a-z0-9-]+', source['id']) or source['id'] in ids:
            raise ValueError('Invalid or duplicate source ID')
        ids.add(source['id'])
        safe_url(source['url'])
        if source['format'] not in ('pdf', 'html') or not source['topics']:
            raise ValueError('Invalid source format/topics')
    return sources


def candidates(source, profiles):
    result = []
    for profile in profiles.get('projects', []):
        matched = sorted(set(source['topics']) & set(profile['topics']))
        if source['jurisdiction'] in profile['jurisdictions'] and matched:
            result.append({'project_ref': profile['project_ref'], 'matched_topics': matched,
                           'basis_refs': profile['basis_refs'], 'review_target': profile.get('review_target'),
                           'applicability': 'unconfirmed', 'open_questions': profile.get('open_questions', [])})
    return result


@contextmanager
def locked(root):
    root.mkdir(parents=True, exist_ok=True)
    lock = root / '.lock'
    try:
        lock.mkdir()
    except FileExistsError:
        raise ValueError('Monitor already locked; inspect the previous run before removing a stale lock')
    try:
        (lock / 'owner.json').write_text(json.dumps({'pid': os.getpid(), 'started_at_utc': utc()}))
        yield
    finally:
        (lock / 'owner.json').unlink(missing_ok=True)
        lock.rmdir()


def fetch(source, folder, deadline, objects):
    """curl config disabled; each redirect checked before it is requested. No retries."""
    url = safe_url(source['url'])
    hops = []
    body = b''
    error = None
    for hop in range(4):
        remaining = min(TIMEOUT, max(0, int(deadline - time.monotonic())))
        if not remaining:
            error = 'run_time_budget_exhausted'
            break
        stem = folder / f'http-{hop}'
        body_path, header_path = stem.with_suffix('.body'), stem.with_suffix('.headers')
        command = ['curl', '-q', '--silent', '--show-error', '--proto', '=https',
                   '--connect-timeout', '8', '--max-time', str(remaining), '--max-filesize', str(MAX_BYTES),
                   '--output', str(body_path), '--dump-header', str(header_path), '--write-out', '%{json}', url]
        result = subprocess.run(command, capture_output=True, text=True, timeout=remaining + 5)
        # Full available curl metadata/stderr. Response headers omit cookies/auth only.
        stem.with_suffix('.transport.json').write_text(result.stdout)
        stem.with_suffix('.stderr.txt').write_text(result.stderr)
        header_text = header_path.read_text(errors='replace') if header_path.exists() else ''
        header_path.unlink(missing_ok=True)
        redacted = [line for line in header_text.splitlines() if not line.lower().startswith(
            ('set-cookie:', 'cookie:', 'authorization:', 'proxy-authenticate:', 'www-authenticate:'))]
        stem.with_suffix('.headers.redacted.txt').write_text('\n'.join(redacted) + '\n')
        body = body_path.read_bytes() if body_path.exists() else b''
        if body:
            obj = objects / sha(body)
            objects.mkdir(parents=True, exist_ok=True)
            if obj.exists() and obj.read_bytes() != body:
                raise ValueError('Stored HTTP object corrupted')
            if not obj.exists():
                obj.write_bytes(body)
        body_path.unlink(missing_ok=True)
        meta = json.loads(result.stdout) if result.stdout else {}
        status = int(meta.get('http_code', 0))
        hops.append({'url': url, 'http_status': status, 'curl_exit': result.returncode,
                     'body_sha256': sha(body), 'body_bytes': len(body),
                     'body_path': 'objects/' + sha(body) if body else None, 'transport_prefix': stem.name})
        if result.returncode or len(body) > MAX_BYTES:
            error = 'transport_failed_or_size_limit'
            break
        if status in (301, 302, 303, 307, 308):
            location = meta.get('redirect_url')
            if hop == 3 or not location:
                error = 'redirect_limit_or_missing_location'
                break
            try:
                url = safe_url(urljoin(url, location))
            except ValueError:
                error = 'redirect_outside_allowlist'
                break
            continue
        if status != 200:
            error = f'http_{status}'
        break
    return body, {'source_url': source['url'], 'retrieved_at_utc': utc(), 'tool': 'curl',
                  'safe_parameters': {'method': 'GET', 'authentication': 'none', 'max_bytes': MAX_BYTES,
                                      'max_seconds_per_hop': TIMEOUT, 'max_redirects': 3, 'retries': 0},
                  'http_status': hops[-1]['http_status'] if hops else 0, 'hops': hops,
                  'error': error, 'classification': 'raw-body/redacted-headers',
                  'coverage': 'one configured URL and redirects; no linked documents or pagination crawled',
                  'known_gaps': ['Cookies/authentication headers omitted; no browser rendering; no legal review.']}


class Monitor:
    def __init__(self, root, profiles):
        self.root = Path(root)
        self.profiles = profiles
        self.state_path = self.root / 'state.json'
        self.state = read(self.state_path) if self.state_path.exists() else {'schema_version': 1, 'sources': {}}

    def ingest(self, source, body, receipt):
        now = utc()
        sid = source['id']
        old = self.state['sources'].get(sid, {})
        capture_id = uuid.uuid4().hex
        capture_path = self.root / 'captures' / (capture_id + '.json')
        receipt = dict(receipt, source_id=sid, indexed_at_utc=now, bytes=len(body), sha256=sha(body))
        if body:
            obj = self.root / 'objects' / sha(body)
            obj.parent.mkdir(parents=True, exist_ok=True)
            if obj.exists() and sha(obj.read_bytes()) != sha(body):
                raise ValueError('Stored object corrupted')
            if not obj.exists():
                obj.write_bytes(body)
            receipt['path'] = str(obj.relative_to(self.root))
        err = receipt.get('error')
        comp = None
        try:
            if not err and receipt.get('http_status') != 200:
                raise ValueError('HTTP status is not 200')
            if not err:
                comp = comparison(source, body)
        except (ValueError, UnicodeError) as exc:
            err = str(exc)
        receipt['error'] = err
        write(capture_path, receipt)
        base = dict(old, last_attempt_at_utc=now, last_capture=str(capture_path.relative_to(self.root)))
        result = {'source_id': sid, 'capture': base['last_capture'], 'source_url': source['url']}
        if err:
            base.update(consecutive_errors=old.get('consecutive_errors', 0) + 1, last_error=err)
            result.update(status='fetch_error', error=err, attention=True)
        else:
            fingerprint = sha(json.dumps(comp, sort_keys=True, ensure_ascii=False).encode())
            seen = old.get('seen_versions', [])
            status = 'baseline' if not old.get('comparison_sha256') else (
                'unchanged' if fingerprint == old['comparison_sha256'] else
                'known_version_returned' if fingerprint in seen else 'changed')
            write(self.root / 'comparisons' / f'{fingerprint}.json', comp)
            base.update(last_success_at_utc=receipt['retrieved_at_utc'], last_success_capture=base['last_capture'],
                        current_object=receipt['path'], raw_sha256=sha(body), comparison_sha256=fingerprint,
                        seen_versions=list(dict.fromkeys(seen + [fingerprint])), consecutive_errors=0, last_error=None)
            result.update(status=status, raw_sha256=sha(body), comparison_sha256=fingerprint,
                          attention=status in ('changed', 'known_version_returned'))
            if status == 'changed':
                fid = sha((sid + ':' + fingerprint).encode())
                finding_path = self.root / 'findings' / f'{fid}.json'
                if not finding_path.exists():
                    write(finding_path, {'schema_version': 1, 'id': fid, 'source_id': sid,
                        'source_url': source['url'], 'detected_at_utc': now, 'capture': base['last_capture'],
                        'previous_capture': old['last_success_capture'], 'previous_comparison_sha256': old['comparison_sha256'],
                        'comparison_sha256': fingerprint, 'publication_state': source.get('publication_state', 'unreviewed'),
                        'legal_change': 'unconfirmed', 'applies_from': None, 'deadline': None,
                        'project_candidates': candidates(source, self.profiles),
                        'review_status': 'needs_source_review',
                        'question': 'What changed in the primary source; is it enacted/in force and relevant to the referenced project facts?'})
                result['finding'] = str(finding_path.relative_to(self.root))
        self.state['sources'][sid] = base
        write(self.state_path, self.state)
        return result

    def status(self, sources, days=7):
        now = datetime.now(timezone.utc)
        result = []
        for source in sources:
            entry = self.state['sources'].get(source['id'], {})
            last = entry.get('last_success_at_utc')
            overdue = not last or now - datetime.fromisoformat(last) > timedelta(days=days)
            result.append({'source_id': source['id'], 'last_success_at_utc': last,
                           'overdue': overdue, 'consecutive_errors': entry.get('consecutive_errors', 0),
                           'last_error': entry.get('last_error')})
        return result

    def library(self, sources):
        lines = ['# Local source library', '', 'Saved sources are not a verified current consolidation.', '',
                 '| Source | Saved original | Retrieved UTC | Source review |', '| --- | --- | --- | --- |']
        for source in sources:
            entry = self.state['sources'].get(source['id'], {})
            obj = entry.get('current_object')
            link = 'missing'
            if obj:
                friendly = self.root / 'documents' / (source['id'] + '.' + source['format'])
                friendly.parent.mkdir(exist_ok=True)
                target = '../' + obj
                if friendly.is_symlink() and os.readlink(friendly) != target:
                    friendly.unlink()
                if not friendly.exists() and not friendly.is_symlink():
                    friendly.symlink_to(target)
                link = f'[file](documents/{friendly.name})'
            lines.append(f"| [{source['title']}]({source['url']}) | {link} | {entry.get('last_success_at_utc', '—')} | unreviewed |")
        (self.root / 'LIBRARY.md').write_text('\n'.join(lines) + '\n')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('command', choices=['check', 'seed', 'status'])
    parser.add_argument('--watchlist', type=Path, default=ROOT / 'monitoring/za.json')
    parser.add_argument('--profiles', type=Path)
    parser.add_argument('--state-dir', type=Path, default=ROOT / 'private/monitoring/za')
    parser.add_argument('--source', action='append')
    parser.add_argument('--capture', type=Path, help='seed: existing capture JSON; original UTC and hash retained')
    args = parser.parse_args()
    try:
        os.umask(0o077)
        state_dir = args.state_dir.resolve()
        if not state_dir.is_relative_to((ROOT / 'private').resolve()):
            raise ValueError('State directory must be within this checkout private/')
        sources = validate_watchlist(read(args.watchlist))
        selected = [s for s in sources if not args.source or s['id'] in args.source]
        if not selected or args.source and set(args.source) - {s['id'] for s in selected}:
            raise ValueError('Unknown source selection')
        profiles = read(args.profiles) if args.profiles else {'projects': []}
        with locked(state_dir):
            monitor = Monitor(state_dir, profiles)
            if args.command == 'status':
                report = {'sources': monitor.status(selected), 'scheduler_state': 'not_inspected_by_this_command',
                          'project_subscriptions': {source['id']: candidates(source, profiles) for source in selected}}
                code = 2 if any(s['overdue'] or s['last_error'] for s in report['sources']) else 0
            else:
                run_id = datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S') + '-' + uuid.uuid4().hex[:8]
                run = state_dir / 'runs' / run_id
                run.mkdir(parents=True)
                report = {'schema_version': 1, 'run_id': run_id, 'command': args.command,
                          'started_at_utc': utc(), 'watchlist_sha256': sha(args.watchlist.read_bytes()),
                          'profiles_sha256': sha(args.profiles.read_bytes()) if args.profiles else None,
                          'model_calls': 0, 'messages_sent': 0, 'results': [], 'complete': False}
                write(run / 'report.json', report)
                deadline = time.monotonic() + RUN_SECONDS
                for source in selected:
                    if args.command == 'seed':
                        if len(selected) != 1 or not args.capture:
                            raise ValueError('seed needs exactly one --source and a --capture')
                        receipt = read(args.capture)
                        path = (ROOT / receipt['path']).resolve()
                        if not path.is_relative_to(ROOT / 'private/evidence'):
                            raise ValueError('Seed must reference private/evidence in this checkout')
                        body = path.read_bytes()
                        when = datetime.fromisoformat(receipt['retrieved_at_utc'])
                        if when.tzinfo is None or when > datetime.now(timezone.utc):
                            raise ValueError('Seed capture UTC missing or in future')
                        if receipt['source_url'] != source['url'] or sha(body) != receipt['sha256'] or len(body) != receipt['bytes'] or receipt.get('curl_exit', 0):
                            raise ValueError('Seed URL/hash/size/transport mismatch')
                        receipt = dict(receipt, seed_capture=str(args.capture), imported_at_utc=utc())
                    else:
                        folder = run / source['id']
                        folder.mkdir()
                        try:
                            body, receipt = fetch(source, folder, deadline, state_dir / 'objects')
                        except (OSError, ValueError, subprocess.TimeoutExpired) as exc:
                            body, receipt = b'', {'source_url': source['url'], 'retrieved_at_utc': utc(),
                                'http_status': 0, 'error': type(exc).__name__ + ': ' + str(exc), 'classification': 'error'}
                    report['results'].append(monitor.ingest(source, body, receipt))
                    write(run / 'report.json', report)
                report.update(completed_at_utc=utc(), complete=True)
                write(run / 'report.json', report)
                monitor.library(sources)
                code = 2 if any(r['status'] == 'fetch_error' for r in report['results']) else 0
            print(json.dumps(report, ensure_ascii=False, indent=2))
            return code
    except (OSError, ValueError, KeyError, TypeError) as exc:
        parser.exit(1, f'Monitor failed: {exc}\n')


if __name__ == '__main__':
    raise SystemExit(main())
