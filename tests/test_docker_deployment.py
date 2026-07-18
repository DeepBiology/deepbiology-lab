from pathlib import Path
import unittest


REPOSITORY_ROOT = Path(__file__).resolve().parents[1]


class DockerDeploymentTests(unittest.TestCase):
    def test_application_port_is_internal_only(self):
        compose = (REPOSITORY_ROOT / "compose.yaml").read_text()
        mcp_service = compose.split("  caddy:", 1)[0]
        caddy_service = compose.split("  caddy:", 1)[1]

        self.assertIn('      - "8000"', mcp_service)
        self.assertNotIn("    ports:", mcp_service)
        self.assertNotIn("8000:8000", compose)
        self.assertIn("    stop_grace_period: 30s", mcp_service)
        self.assertIn('      - "443:443"', caddy_service)
        self.assertIn('      - "80:80"', caddy_service)

    def test_deployment_does_not_configure_a_global_api_key(self):
        compose = (REPOSITORY_ROOT / "compose.yaml").read_text()
        environment_example = (REPOSITORY_ROOT / ".env.example").read_text()

        self.assertNotIn("DEEPBIOLOGY_API_KEY", compose)
        configured_variables = [
            line for line in environment_example.splitlines()
            if line and not line.lstrip().startswith("#")
        ]
        self.assertFalse(any(line.startswith("DEEPBIOLOGY_API_KEY=") for line in configured_variables))

    def test_proxy_routes_only_mcp_over_the_private_service_name(self):
        caddyfile = (REPOSITORY_ROOT / "Caddyfile").read_text()

        self.assertIn("@mcp path /mcp /mcp/*", caddyfile)
        self.assertIn("reverse_proxy mcp:8000", caddyfile)
        self.assertIn('respond "Not Found" 404', caddyfile)
        self.assertNotIn("healthz", caddyfile)

    def test_image_runs_as_an_unprivileged_http_server(self):
        dockerfile = (REPOSITORY_ROOT / "Dockerfile").read_text()

        self.assertIn("USER 10001:10001", dockerfile)
        self.assertIn("MCP_TRANSPORT=streamable-http", dockerfile)
        self.assertIn("MCP_HOST=0.0.0.0", dockerfile)
        self.assertIn("PORT=8000", dockerfile)
        self.assertIn("http://127.0.0.1:8000/healthz", dockerfile)
        self.assertIn('CMD ["deepbiology-lab-mcp"]', dockerfile)

    def test_local_secrets_and_certificates_are_ignored(self):
        gitignore = (REPOSITORY_ROOT / ".gitignore").read_text().splitlines()

        for pattern in (".env", "*.key", "*.pem", "*.p12", "*.pfx", "*.crt", "*.cer"):
            self.assertIn(pattern, gitignore)
        self.assertIn("!.env.example", gitignore)


if __name__ == "__main__":
    unittest.main()
