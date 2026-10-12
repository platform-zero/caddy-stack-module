import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

class SharedPublicCATest(unittest.TestCase):
    def test_only_public_anchor_volume_is_shared(self):
        text = (ROOT / 'stack.runtime.yaml').read_text()
        resource_block = text.split('\nvolumes:\n', 1)[1].split('\nservices:\n', 1)[0]
        self.assertEqual(resource_block, '  caddy_ca:\n    hostPath: "${STACK_VOLUME_ROOT}/caddy_ca"\n    rootlessStrategy: "shared"')
        self.assertNotIn('caddy_certs:', resource_block)
        self.assertNotIn('caddy_data:', resource_block)
        self.assertIn('"caddy_ca:/ca"', text)

    def test_public_anchor_has_rootful_producer(self):
        text = (ROOT / 'stack.runtime.yaml').read_text()
        producer = text.split('\nservices:\n  caddy:\n', 1)[1]
        self.assertIn('placement: "rootful"', producer)
        self.assertIn('"caddy_ca:/ca"', producer)
        self.assertIn('"caddy_certs:/certs"', producer)

if __name__ == '__main__':
    unittest.main()
