from django.test import SimpleTestCase, override_settings

@override_settings(ALLOWED_HOSTS=["testserver"], SECURE_SSL_REDIRECT=False)
class HealthTests(SimpleTestCase):
    def test_health_without_database(self):
        response = self.client.get("/health/")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {"status": "ok", "service": "eventger-backend"})

    def test_health_rejects_writes(self):
        response = self.client.post("/health/")

        self.assertEqual(response.status_code, 405)
        self.assertEqual(
            response.json(),
            {
                "success": False,
                "message": (
                    "El método HTTP no está permitido para este endpoint."
                ),
            },
        )

    def test_unknown_host_rejected(self):
        self.assertEqual(self.client.get("/health/", HTTP_HOST="untrusted.example").status_code, 400)

    def test_cors_denied_by_default(self):
        response = self.client.get("/health/", HTTP_ORIGIN="https://untrusted.example")
        self.assertNotIn("Access-Control-Allow-Origin", response)


@override_settings(ALLOWED_HOSTS=["testserver"], SECURE_SSL_REDIRECT=False)
class OpenAPISchemaTests(SimpleTestCase):
    def get_schema(self):
        response = self.client.get(
            "/api/schema/",
            HTTP_ACCEPT="application/vnd.oai.openapi+json",
        )
        self.assertEqual(response.status_code, 200)
        return response.json()

    def test_success_responses_use_api_envelopes(self):
        schema = self.get_schema()

        expected_responses = {
            ("/event-types/", "get", "200"): "EventTypeListResponse",
            ("/events/", "get", "200"): "EventListResponse",
            ("/events/", "post", "201"): "EventResponse",
            ("/events/{id}/", "get", "200"): "EventResponse",
            ("/events/{event_id}/subtasks/", "get", "200"): (
                "SubtaskListResponse"
            ),
            ("/events/{event_id}/subtasks/", "post", "201"): (
                "SubtaskResponse"
            ),
            ("/subtasks/", "get", "200"): "SubtaskListResponse",
            ("/subtasks/{id}/", "get", "200"): "SubtaskResponse",
        }

        for (path, method, status_code), component in expected_responses.items():
            with self.subTest(path=path, method=method, status_code=status_code):
                response_schema = schema["paths"][path][method]["responses"][
                    status_code
                ]["content"]["application/json"]["schema"]
                self.assertEqual(
                    response_schema["$ref"],
                    f"#/components/schemas/{component}",
                )

    def test_create_responses_document_validation_and_not_found_errors(self):
        schema = self.get_schema()

        event_responses = schema["paths"]["/events/"]["post"]["responses"]
        self.assertIn("400", event_responses)

        subtask_responses = schema["paths"][
            "/events/{event_id}/subtasks/"
        ]["post"]["responses"]
        self.assertIn("400", subtask_responses)
        self.assertIn("404", subtask_responses)

    def test_delete_responses_document_not_found_errors(self):
        schema = self.get_schema()

        event_responses = schema["paths"]["/events/{id}/"]["delete"][
            "responses"
        ]
        subtask_responses = schema["paths"]["/subtasks/{id}/"]["delete"][
            "responses"
        ]

        self.assertIn("204", event_responses)
        self.assertIn("404", event_responses)
        self.assertIn("204", subtask_responses)
        self.assertIn("404", subtask_responses)

    def test_create_operations_include_explicit_examples(self):
        schema = self.get_schema()

        event_post = schema["paths"]["/events/"]["post"]
        subtask_post = schema["paths"][
            "/events/{event_id}/subtasks/"
        ]["post"]

        self.assertTrue(
            event_post["requestBody"]["content"]["application/json"]["examples"]
        )
        self.assertTrue(
            event_post["responses"]["201"]["content"]["application/json"][
                "examples"
            ]
        )
        self.assertTrue(
            event_post["responses"]["400"]["content"]["application/json"][
                "examples"
            ]
        )
        self.assertTrue(
            event_post["responses"]["503"]["content"]["application/json"][
                "examples"
            ]
        )
        self.assertTrue(
            subtask_post["requestBody"]["content"]["application/json"][
                "examples"
            ]
        )
        self.assertTrue(
            subtask_post["responses"]["201"]["content"]["application/json"][
                "examples"
            ]
        )
        self.assertTrue(
            subtask_post["responses"]["400"]["content"]["application/json"][
                "examples"
            ]
        )
        self.assertTrue(
            subtask_post["responses"]["404"]["content"]["application/json"][
                "examples"
            ]
        )
