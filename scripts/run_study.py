"""Execute the frozen inventory with real processes and retain every planned row."""
import argparse
import json
import os
import platform
import subprocess
import sys
import time
import uuid
from datetime import datetime, timezone
from pathlib import Path
import httpx
import psutil
from packages.contracts.identity import digest, file_digest, write_json
from packages.operations.ledger import Ledger

ROOT = Path(__file__).resolve().parents[1]
GATEWAY = "http://127.0.0.1:8765"
WORKER = "http://127.0.0.1:8766"


def stamp():
    return datetime.now(timezone.utc).isoformat()


def wait_ready(url, process, seconds=40):
    deadline = time.monotonic() + seconds
    while time.monotonic() < deadline:
        if process.poll() is not None:
            raise RuntimeError(f"Process exited before readiness: {process.returncode}")
        try:
            response = httpx.get(url, timeout=1, trust_env=False)
            if response.status_code == 200:
                return response.json() if response.content else {"ready": True}
        except (httpx.HTTPError, ValueError):
            pass
        time.sleep(0.1)
    raise RuntimeError("Readiness deadline exceeded.")


def terminate(process):
    if process and process.poll() is None:
        process.terminate()
        try:
            process.wait(timeout=6)
        except subprocess.TimeoutExpired:
            process.kill()
            process.wait(timeout=4)


class Lab:
    def __init__(self, run_id):
        self.run_id = run_id
        self.directory = ROOT / "artifacts/raw" / run_id
        self.directory.mkdir(parents=True, exist_ok=False)
        self.revision = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT,
                                                text=True).strip()
        self.env = {**os.environ, "TRACEPATH_PROFILE": "lab", "SOURCE_REVISION": self.revision,
            "WORKER_URL": WORKER, "OTEL_ENDPOINT": "http://127.0.0.1:4318/v1/traces",
            "RAW_DIR": str(self.directory), "ALLOWED_ORIGIN": "http://127.0.0.1:5173"}
        self.processes, self.logs = [], []
        self.collector = self.worker = self.gateway = None
        self.started_at = stamp()
        self.peak_rss = {}

    def start_process(self, command, label):
        log_dir = ROOT / ".local/logs" / self.run_id
        log_dir.mkdir(parents=True, exist_ok=True)
        stream = (log_dir / f"{label}-{len(self.processes)}.log").open("w", encoding="utf-8")
        process = subprocess.Popen(command, cwd=ROOT, env=self.env, stdout=stream,
            stderr=subprocess.STDOUT, creationflags=subprocess.CREATE_NO_WINDOW if os.name == "nt" else 0)
        self.processes.append(process)
        self.logs.append(stream)
        return process

    def start_collector(self):
        output = (self.directory / "collector.jsonl").as_posix()
        config = self.directory / "collector.yaml"
        config.write_text(f"""receivers:
  otlp:
    protocols:
      http:
        endpoint: 127.0.0.1:4318
exporters:
  file:
    path: {output}
    append: true
    flush_interval: 50ms
extensions:
  health_check:
    endpoint: 127.0.0.1:13133
service:
  extensions: [health_check]
  pipelines:
    traces:
      receivers: [otlp]
      exporters: [file]
""", encoding="utf-8")
        binary = os.environ["COLLECTOR_BINARY"]
        self.collector = self.start_process([binary, "--config", str(config)], "collector")
        wait_ready("http://127.0.0.1:13133", self.collector)

    def start_gateway(self):
        self.gateway = self.start_process([sys.executable, "-m", "uvicorn", "packages.api.gateway:app",
            "--host", "127.0.0.1", "--port", "8765", "--no-access-log"], "gateway")
        return wait_ready(GATEWAY+"/ready", self.gateway)

    def start(self):
        self.start_collector()
        self.worker = self.start_process([sys.executable, "-m", "uvicorn", "packages.api.worker:app",
            "--host", "127.0.0.1", "--port", "8766", "--no-access-log"], "worker")
        worker = wait_ready(WORKER+"/ready", self.worker)
        gateway = self.start_gateway()
        write_json(self.directory / "environment.json", {"schema_version": 1,
            "run_id": self.run_id, "source_revision": self.revision, "started_at": self.started_at,
            "os": platform.platform(), "python": platform.python_version(),
            "processor": platform.processor(), "cpu_count": os.cpu_count(),
            "worker": worker, "gateway": gateway,
            "collector_binary_sha256": file_digest(Path(os.environ["COLLECTOR_BINARY"])),
            "database": "dedicated Postgres; credential omitted", "profile": "native_processes"})

    def session(self):
        r = httpx.post(GATEWAY+"/v1/sessions", json={}, timeout=10, trust_env=False)
        r.raise_for_status()
        return r.json()["token"]

    def execute(self, row, session, category):
        observation = {"planned_id": row["planned_id"], "run_id": self.run_id,
            "source_revision": self.revision, "category": category, "family": row["family"],
            "lane": row["lane"], "started_at": stamp(), "query_digest": digest(row["query"])}
        if "pair_id" in row:
            observation["pair_id"] = row["pair_id"]
        outage = row["family"] == "collector_outage"
        if outage:
            terminate(self.collector)
            observation["injector"] = {"action": "stop collector process", "pid": self.collector.pid,
                                      "observed_exit_code": self.collector.poll()}
        headers = {"Authorization": "Bearer "+session}
        if row["family"] == "malformed_context":
            headers["traceparent"] = "malformed-context"
        start = time.perf_counter_ns()
        try:
            response = httpx.post(GATEWAY+"/experiment/search", headers=headers, timeout=20, trust_env=False,
                json={"query": row["query"], "operation_key": row["planned_id"], "run_id": self.run_id,
                      "telemetry": row["telemetry"], "fault": row["family"]})
            observation["client_duration_ms"] = (time.perf_counter_ns()-start)/1e6
            observation["status_code"] = response.status_code
            if response.status_code == 200:
                result = response.json()
                observation.update(request_id=result["request_id"], output_digest=result["output_digest"],
                    returned_hits=result["hits"], attempts=result["attempts"], context_status=result["context_status"],
                    business_status="committed")
                # A fresh independent HTTP client reads the committed result after response.
                readback = httpx.get(GATEWAY+"/v1/requests/"+result["request_id"], headers=headers,
                                    timeout=10, trust_env=False)
                observation["http_readback"] = readback.status_code == 200 and readback.json()["output_digest"] == result["output_digest"]
            else:
                observation.update(business_status="failed", detail=response.json().get("detail"))
        except httpx.HTTPError as error:
            observation.update(client_duration_ms=(time.perf_counter_ns()-start)/1e6,
                               business_status="unavailable", error_type=type(error).__name__)
        finally:
            observation["finished_at"] = stamp()
            with (self.directory / "clients.jsonl").open("a", encoding="utf-8") as stream:
                stream.write(json.dumps(observation, sort_keys=True)+"\n")
            if outage:
                self.start_collector()
            self.sample_resources()
        return observation

    def sample_resources(self):
        for name, proc in (("gateway", self.gateway), ("worker", self.worker), ("collector", self.collector)):
            try:
                value = psutil.Process(proc.pid).memory_info().rss
                self.peak_rss[name] = max(value, self.peak_rss.get(name, 0))
            except psutil.Error:
                pass

    def export_ledger(self):
        with Ledger(os.environ["DATABASE_URL"]).connection() as connection:
            receipts = [row[0] for row in connection.execute(
                "SELECT receipt FROM tracepath.receipts WHERE receipt->>'run_id'=%s ORDER BY request_id",
                (self.run_id,)).fetchall()]
            attempts = [row[0] for row in connection.execute(
                "SELECT observation FROM tracepath.attempts WHERE run_id=%s ORDER BY attempt_id",
                (self.run_id,)).fetchall()]
        write_json(self.directory / "ledger.json", {"receipts": receipts, "attempts": attempts,
                   "read_at": stamp(), "reader_pid": os.getpid(), "independent_connection": True})

    def close(self):
        self.export_ledger()
        resources = {"sampled_peak_rss_bytes": self.peak_rss,
                     "method": "psutil RSS sampled after every request; not a continuous peak"}
        resources["cpu_seconds"] = {}
        for name, proc in (("gateway", self.gateway), ("worker", self.worker)):
            try:
                times = psutil.Process(proc.pid).cpu_times()
                resources["cpu_seconds"][name] = times.user+times.system
            except psutil.Error:
                resources["cpu_seconds"][name] = None
        write_json(self.directory / "resources.json", resources)
        for process in reversed(self.processes):
            terminate(process)
        for stream in self.logs:
            stream.close()
        write_json(self.directory / "window.json", {"started_at": self.started_at, "finished_at": stamp()})


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--development", action="store_true")
    args = parser.parse_args()
    inv = json.loads((ROOT/"evaluation/inventory.json").read_text())
    pre = json.loads((ROOT/"evaluation/preregistration.json").read_text())
    if digest(inv) != pre["inventory_digest"]:
        raise RuntimeError("Frozen inventory identity changed.")
    run_id = ("development-" if args.development else "study-")+uuid.uuid4().hex[:12]
    lab = Lab(run_id)
    try:
        lab.start()
        session = lab.session()
        for i in range(4):
            row = {"planned_id": f"warmup-{i}", "query": "How does a sensor expire?", "family": "normal",
                   "lane": "traced" if i % 2 else "untraced", "telemetry": bool(i % 2)}
            lab.execute(row, session, "warmup")
        if args.development:
            rows = [{**r, "planned_id": r["lineage_id"]+"-dev", "telemetry": True, "lane": "traced"}
                    for r in inv["scenario_lineages"] if r["split"] == "development"]
            categories = [("development", rows)]
        else:
            categories = [("primary", inv["primary"]), ("overhead", inv["overhead"])]
        for category, rows in categories:
            for i, row in enumerate(rows):
                if i % 12 == 0:
                    session = lab.session()
                result = lab.execute(row, session, category)
                print(f"{row['planned_id']} {result['business_status']}", flush=True)
    finally:
        lab.close()
    print(f"RUN_ID={run_id}", flush=True)


if __name__ == "__main__":
    main()
