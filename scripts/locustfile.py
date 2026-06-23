from locust import HttpUser, task, between

class AttackerUser(HttpUser):
    wait_time = between(0.1, 1.0)
    
    @task(3)
    def simulate_scan(self):
        payload = {
            "endpoint": "/.env",
            "method": "GET",
            "severity": "HIGH",
            "source_ip": "10.0.0.50",
            "timestamp": "2026-06-22T10:00:00Z"
        }
        headers = {"X-API-Key": "hc_live_fsj-onia9stXSc2HgIuUDqfwR_f5Oe0Q4sTZTMhBku0"}
        self.client.post("/api/ingest", json=payload, headers=headers)

    @task(1)
    def simulate_dashboard_poll(self):
        # Using a basic auth mock or bypassing if the dashboard is unprotected during testing
        # We will just hit health for performance metrics
        self.client.get("/api/health")
