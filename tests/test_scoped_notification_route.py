import pathlib,re,unittest
SOURCE=(pathlib.Path(__file__).resolve().parents[1]/'stack.config/caddy/Caddyfile').read_text()
class ScopedNotificationRoute(unittest.TestCase):
 def test_native_bearer_keeps_ntfy_authority_not_shared_browser_identity(self):
  block=SOURCE.split('ntfy.{$DOMAIN} {',1)[1].split('ntfy-native.{$DOMAIN}',1)[0]
  native=block.split('handle @ntfy_owner_token {',1)[1].split('\n\t}',1)[0]
  self.assertIn('reverse_proxy ntfy:80',native);self.assertNotIn('header_up Authorization',native);self.assertNotIn('keycloak_auth',native)
  self.assertIn('^Bearer[[:space:]]+tk_[A-Za-z0-9]+$',block)
 def test_publisher_and_browser_authority_are_separate(self):
  block=SOURCE.split('ntfy.{$DOMAIN} {',1)[1].split('ntfy-native.{$DOMAIN}',1)[0]
  self.assertIn('header Authorization "{$NTFY_PUBLISHER_AUTHORIZATION}"',block);self.assertIn('import keycloak_group_allow ntfy admins|operators',block);self.assertIn('header_up Authorization "{$NTFY_SSO_AUTHORIZATION}"',block)
if __name__=='__main__':unittest.main()
