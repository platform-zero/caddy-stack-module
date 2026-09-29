import base64
import importlib.util
import os
import pathlib
import unittest


os.environ.update({
    "KEYCLOAK_TOKEN_URL": "http://127.0.0.1/unused",
    "NTFY_NATIVE_CLIENT_SECRET": "test-client-secret",
    "NTFY_NATIVE_GATEWAY_SECRET": "test-gateway-secret",
})
source = pathlib.Path(__file__).parents[1] / "stack.config/caddy/ntfy-native-auth.py"
spec = importlib.util.spec_from_file_location("ntfy_native_auth", source)
auth = importlib.util.module_from_spec(spec)
spec.loader.exec_module(auth)


class NtfyNativeAuthTest(unittest.TestCase):
    def test_basic_credentials_are_strict(self):
        valid = base64.b64encode(b"gerald:secret:with-colon").decode()
        self.assertEqual(auth.basic_credentials("Basic " + valid),
                         ("gerald", "secret:with-colon"))
        self.assertIsNone(auth.basic_credentials("Basic invalid!"))
        self.assertIsNone(auth.basic_credentials("Bearer " + valid))

    def test_personal_topics_are_private(self):
        gerald = {"preferred_username": "gerald", "groups": ["users"]}
        other = {"preferred_username": "other", "groups": ["users"]}
        self.assertTrue(auth.permitted(gerald, "GET", "/gerald_alerts/ws?since=none"))
        self.assertTrue(auth.permitted(gerald, "POST", "/gerald_alerts"))
        self.assertFalse(auth.permitted(other, "GET", "/gerald_alerts/ws"))
        self.assertFalse(auth.permitted(gerald, "GET", "/other_alerts/json"))
        self.assertFalse(auth.permitted(gerald, "GET", "/gerald_alerts,other_alerts/ws"))
        self.assertFalse(auth.permitted(gerald, "GET", "/gerald_alerts%2Fother/ws"))
        delegated = {"preferred_username": "other", "groups": ["users", "ntfy-topic-gerald_alerts"]}
        self.assertTrue(auth.permitted(delegated, "GET", "/gerald_alerts/ws"))
        self.assertFalse(auth.permitted(delegated, "GET", "/another_alerts/ws"))

    def test_platform_topics_are_read_only_for_operator_groups(self):
        admin = {"preferred_username": "admin", "groups": ["admins"]}
        viewer = {"preferred_username": "viewer", "groups": ["users"]}
        self.assertTrue(auth.permitted(admin, "GET", "/webservices-alerts/ws"))
        self.assertFalse(auth.permitted(admin, "POST", "/webservices-alerts"))
        self.assertFalse(auth.permitted(viewer, "GET", "/webservices-alerts/ws"))
        self.assertFalse(auth.permitted(admin, "DELETE", "/webservices-alerts"))

    def test_onboarding_is_denied(self):
        account = {"preferred_username": "new", "groups": ["users", "onboarding_required"]}
        self.assertFalse(auth.permitted(account, "GET", "/new_alerts/ws"))


if __name__ == "__main__":
    unittest.main()
