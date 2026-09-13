from django.test import SimpleTestCase, override_settings

@override_settings(ALLOWED_HOSTS=["testserver"], SECURE_SSL_REDIRECT=False)
class HealthTests(SimpleTestCase):
    def test_health_without_database(self):
        response = self.client.get("/health/")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {"status": "ok", "service": "eventger-backend"})

    def test_health_rejects_writes(self):
        self.assertEqual(self.client.post("/health/").status_code, 405)

    def test_unknown_host_rejected(self):
        self.assertEqual(self.client.get("/health/", HTTP_HOST="untrusted.example").status_code, 400)

    def test_cors_denied_by_default(self):
        response = self.client.get("/health/", HTTP_ORIGIN="https://untrusted.example")
        self.assertNotIn("Access-Control-Allow-Origin", response)
