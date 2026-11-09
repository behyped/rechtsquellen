import importlib.util
import json
from pathlib import Path
import tempfile
import unittest
from datetime import datetime, timezone, timedelta

spec = importlib.util.spec_from_file_location('watch_sources', Path(__file__).resolve().parents[1] / 'scripts/watch_sources.py')
w = importlib.util.module_from_spec(spec)
spec.loader.exec_module(w)


class WatchTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.source = {'id': 'za-example', 'title': 'Example', 'jurisdiction': 'ZA',
                       'url': 'https://www.gov.za/example.pdf', 'format': 'pdf', 'topics': ['privacy']}
        self.profiles = {'projects': [
            {'project_ref': 'example:za', 'jurisdictions': ['ZA'], 'topics': ['privacy'], 'basis_refs': ['fixture']},
            {'project_ref': 'example:cy', 'jurisdictions': ['CY'], 'topics': ['privacy'], 'basis_refs': ['fixture']},
            {'project_ref': 'example:unrelated', 'jurisdictions': ['ZA'], 'topics': ['corporate'], 'basis_refs': ['fixture']}]}
        self.monitor = w.Monitor(self.root, self.profiles)
        self.receipt = {'source_url': self.source['url'], 'retrieved_at_utc': w.utc(), 'http_status': 200}

    def ingest(self, body, **receipt):
        return self.monitor.ingest(self.source, body, dict(self.receipt, **receipt))

    def test_baseline_change_duplicate_and_project_routing(self):
        self.assertEqual(self.ingest(b'%PDF-1 original')['status'], 'baseline')
        changed = self.ingest(b'%PDF-1 amendment')
        self.assertEqual(changed['status'], 'changed')
        finding = w.read(self.root / changed['finding'])
        self.assertEqual([p['project_ref'] for p in finding['project_candidates']], ['example:za'])
        self.assertEqual(finding['project_candidates'][0]['applicability'], 'unconfirmed')
        self.assertIsNone(finding['applies_from'])
        self.assertEqual(self.ingest(b'%PDF-1 amendment')['status'], 'unchanged')
        self.assertEqual(len(list((self.root / 'findings').iterdir())), 1)
        self.assertEqual(len(list((self.root / 'objects').iterdir())), 2)

    def test_returned_version_is_visible_but_not_a_duplicate_finding(self):
        self.ingest(b'%PDF-1 original')
        self.ingest(b'%PDF-1 amendment')
        result = self.ingest(b'%PDF-1 original')
        self.assertEqual(result['status'], 'known_version_returned')
        self.assertTrue(result['attention'])
        self.assertEqual(len(list((self.root / 'findings').iterdir())), 1)

    def test_errors_never_advance_success_or_replace_valid_document(self):
        self.ingest(b'%PDF-1 original')
        before = dict(self.monitor.state['sources']['za-example'])
        result = self.ingest(b'<html>Unavailable</html>', http_status=503)
        self.assertEqual(result['status'], 'fetch_error')
        after = self.monitor.state['sources']['za-example']
        for key in ('last_success_at_utc', 'last_success_capture', 'current_object', 'comparison_sha256'):
            self.assertEqual(after[key], before[key])
        self.assertEqual(after['consecutive_errors'], 1)
        self.assertEqual(self.ingest(b'%PDF-1 original')['status'], 'unchanged')
        self.assertEqual(after['last_error'], 'HTTP status is not 200')
        self.assertEqual(self.monitor.state['sources']['za-example']['consecutive_errors'], 0)

    def test_error_page_with_200_is_not_pdf_success(self):
        self.assertEqual(self.ingest(b'<html>Access denied</html>')['status'], 'fetch_error')
        self.assertNotIn('last_success_at_utc', self.monitor.state['sources']['za-example'])

    def test_article_ignores_page_noise_but_not_legal_text_or_links(self):
        source = dict(self.source, format='html')
        body = b'<nav>today</nav><article><p>' + b'Substantive legislative information. ' * 4 + b'</p><a href="/old.pdf">Act</a></article>'
        normalized = w.comparison(source, body)
        self.assertEqual(normalized, w.comparison(source, body.replace(b'today', b'tomorrow')))
        self.assertNotEqual(normalized, w.comparison(source, body.replace(b'/old.pdf', b'/new.pdf')))
        self.assertNotEqual(normalized, w.comparison(source, body.replace(b'legislative', b'amended')))
        with self.assertRaises(ValueError):
            w.comparison(source, b'<html>Login or CAPTCHA</html>')

    def test_restart_keeps_dedup_state_and_old_captures(self):
        self.ingest(b'%PDF-1 original')
        self.ingest(b'%PDF-1 amendment')
        count = len(list((self.root / 'captures').iterdir()))
        self.monitor = w.Monitor(self.root, self.profiles)
        self.assertEqual(self.ingest(b'%PDF-1 amendment')['status'], 'unchanged')
        self.assertEqual(len(list((self.root / 'captures').iterdir())), count + 1)

    def test_staleness_and_errors_remain_distinct(self):
        then = (datetime.now(timezone.utc) - timedelta(days=8)).isoformat()
        self.ingest(b'%PDF-1 original', retrieved_at_utc=then)
        self.assertTrue(self.monitor.status([self.source])[0]['overdue'])
        self.assertIsNone(self.monitor.status([self.source])[0]['last_error'])
        self.ingest(b'', http_status=0, error='timeout')
        self.assertEqual(self.monitor.status([self.source])[0]['last_error'], 'timeout')

    def test_unrelated_source_has_no_project_candidate(self):
        self.assertEqual(w.candidates(dict(self.source, topics=['tax']), self.profiles), [])

    def test_url_and_source_bounds(self):
        for url in ['http://www.gov.za/a', 'https://evil.example/a', 'https://me:secret@www.gov.za/a',
                    'https://www.gov.za:8443/a', 'https://www.gov.za/a?token=x', 'file:///tmp/a']:
            with self.assertRaises(ValueError):
                w.safe_url(url)
        with self.assertRaises(ValueError):
            w.validate_watchlist({'schema_version': 1, 'sources': [self.source] * 17})
        with self.assertRaises(ValueError):
            w.validate_watchlist({'schema_version': 1, 'sources': [self.source, self.source]})

    def test_lock_refuses_concurrent_writer(self):
        with w.locked(self.root):
            with self.assertRaises(ValueError):
                with w.locked(self.root):
                    pass
        self.assertFalse((self.root / '.lock').exists())

    def test_corrupt_object_is_not_silently_overwritten(self):
        body = b'%PDF-1 original'
        self.ingest(body)
        (self.root / 'objects' / w.sha(body)).write_bytes(b'corrupted')
        with self.assertRaises(ValueError):
            self.ingest(body)


if __name__ == '__main__':
    unittest.main()

class TransportTests(unittest.TestCase):
    def test_disallowed_redirect_is_never_requested_and_evidence_is_kept(self):
        from unittest.mock import patch
        from subprocess import CompletedProcess
        import time
        with tempfile.TemporaryDirectory() as folder:
            folder = Path(folder); hop = folder / 'run'; hop.mkdir()
            source = {'url': 'https://www.gov.za/example.pdf'}
            def fake(args, **kwargs):
                Path(args[args.index('--output') + 1]).write_bytes(b'Redirect')
                Path(args[args.index('--dump-header') + 1]).write_text('HTTP/2 302\nSet-Cookie: secret=value\nLocation: https://outside.example/file\n')
                return CompletedProcess(args, 0, json.dumps({'http_code':302,'redirect_url':'https://outside.example/file'}), '')
            with patch.object(w.subprocess, 'run', side_effect=fake) as run:
                body, capture = w.fetch(source, hop, time.monotonic()+60, folder/'objects')
            self.assertEqual(run.call_count, 1)
            self.assertEqual(capture['error'], 'redirect_outside_allowlist')
            self.assertEqual((folder/'objects'/w.sha(body)).read_bytes(), b'Redirect')
            self.assertNotIn('secret', (hop/'http-0.headers.redacted.txt').read_text())
            self.assertFalse((hop/'http-0.body').exists())
            self.assertTrue((hop/'http-0.transport.json').exists())

    def test_deadline_stops_network_before_request(self):
        from unittest.mock import patch
        import time
        with tempfile.TemporaryDirectory() as folder:
            with patch.object(w.subprocess, 'run') as run:
                body, capture = w.fetch({'url':'https://www.gov.za/a'}, Path(folder), time.monotonic()-1, Path(folder)/'objects')
            run.assert_not_called()
            self.assertEqual(capture['error'], 'run_time_budget_exhausted')
