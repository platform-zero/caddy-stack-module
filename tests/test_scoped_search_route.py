"""Source contract only; native access/revocation/TLS require separate receipts."""
from pathlib import Path
import unittest

SOURCE = Path(__file__).resolve().parents[1] / 'stack.config/caddy/Caddyfile'


class ScopedSearchRoute(unittest.TestCase):
    def setUp(self):
        self.route = SOURCE.read_text().split('# webservices-component-start searxng\n', 1)[1].split('# webservices-component-end searxng', 1)[0]

    def test_machine_match_is_exact_and_method_bounded(self):
        match = self.route.split('@p0_websearch_machine {', 1)[1].split('}', 1)[0]
        self.assertEqual([line.strip() for line in match.splitlines() if line.strip()],
                         ['method GET POST', 'path /search', 'header Authorization "Basic *"'])

    def test_machine_credentials_are_not_browser_or_upstream_credentials(self):
        machine = self.route.split('handle @p0_websearch_machine {', 1)[1].split('\n\t\thandle {', 1)[0]
        self.assertIn('basic_auth bcrypt "p0-websearch" {', machine)
        self.assertIn('import /data/p0-search-access/accounts/*.caddy', machine)
        self.assertIn('header_up -Authorization', machine)
        self.assertIn('header_up -Cookie', machine)
        self.assertNotIn('keycloak_auth', machine)
        self.assertNotIn('{$', machine)

    def test_startup_and_health_hash_only_through_private_stdin(self):
        runtime = (SOURCE.parents[2] / 'stack.runtime.yaml').read_text()
        self.assertNotIn('hash-password --plaintext', runtime)
        self.assertEqual(runtime.count('caddy hash-password --algorithm bcrypt --bcrypt-cost 14'), 2)
        # Native Caddy reads a line: unterminated private stdin returns EOF.
        self.assertEqual(runtime.count("printf '%s\\\\n'"), 2)
        self.assertNotIn("printf '%s'", runtime)
        self.assertIn('|| exit 1', runtime)

    def test_browser_sso_and_group_policy_are_preserved(self):
        browser = self.route.split('\n\t\thandle {', 1)[1]
        self.assertIn('import keycloak_auth websearch', browser)
        self.assertIn('import keycloak_group_allow websearch admins|operators|agents', browser)
        self.assertIn('reverse_proxy searxng:8080', browser)
        self.assertEqual(self.route.count('handle @p0_websearch_machine'), 1)
        self.assertNotIn('respond 200', self.route)


if __name__ == '__main__':
    unittest.main()
