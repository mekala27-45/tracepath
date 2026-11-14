"""Fresh process-death recovery, concurrent context isolation and privacy canary."""
import json
import os
import subprocess
import sys
import uuid
from concurrent.futures import ThreadPoolExecutor
import httpx
from packages.contracts.identity import write_json
from packages.operations.ledger import Ledger
from evaluation.independent_grader.collector import read_collector
from evaluation.independent_grader.topology import grade
from scripts.run_study import Lab, GATEWAY, ROOT


def main():
    run_id = "recovery-"+uuid.uuid4().hex[:12]
    lab = Lab(run_id)
    result = {"run_id": run_id, "source_revision": lab.revision}
    try:
        lab.start()
        session = lab.session()
        headers = {"Authorization": "Bearer "+session}
        payload = {"query": "How does Anchor recover a committed receipt?", "operation_key": "crash-recover",
                   "run_id": run_id, "telemetry": True, "fault": "crash_after_commit"}
        old_pid = lab.gateway.pid
        try:
            httpx.post(GATEWAY+"/experiment/search", headers=headers, json=payload, timeout=20, trust_env=False)
            raise AssertionError("Gateway did not lose its response.")
        except httpx.RemoteProtocolError:
            pass
        lab.gateway.wait(timeout=10)
        result.update(crashed_pid=old_pid, observed_exit_code=lab.gateway.returncode)
        lab.start_gateway()
        result["restarted_pid"] = lab.gateway.pid
        child_code = """import os,json,httpx
p=json.loads(os.environ['RECOVERY_PAYLOAD']); p['fault']='none'
r=httpx.post('http://127.0.0.1:8765/experiment/search',json=p,headers={'Authorization':'Bearer '+os.environ['RECOVERY_SESSION']},timeout=20,trust_env=False)
r.raise_for_status(); d=r.json(); assert d['replay']; print(json.dumps({'request_id':d['request_id'],'replay':d['replay'],'output_digest':d['output_digest']}))
"""
        child = subprocess.run([sys.executable, "-c", child_code], capture_output=True, text=True,
            timeout=30, env={**os.environ, "RECOVERY_SESSION": session, "RECOVERY_PAYLOAD": json.dumps(payload)})
        if child.returncode:
            raise AssertionError("Independent recovery client failed: "+child.stderr[-800:])
        result["fresh_process_readback"] = json.loads(child.stdout)
        request_id = result["fresh_process_readback"]["request_id"]
        with Ledger(os.environ["DATABASE_URL"]).connection() as connection:
            result["receipt_count"] = connection.execute("SELECT count(*) FROM tracepath.receipts WHERE request_id=%s",
                                                        (request_id,)).fetchone()[0]
            result["attempt_count_after_replay"] = connection.execute("SELECT count(*) FROM tracepath.attempts WHERE request_id=%s",
                                                                     (request_id,)).fetchone()[0]
        canary = "TRACEPATH_SYNTHETIC_SECRET_4d271b"
        rows = [{"planned_id": f"concurrent-{i}", "family": "normal", "lane": "traced", "telemetry": True,
                 "query": query} for i,query in enumerate(["Tern freshness "+canary, "Model tokenizer identity"])]
        sessions = [lab.session(), lab.session()]
        with ThreadPoolExecutor(max_workers=2) as pool:
            concurrent = list(pool.map(lambda pair: lab.execute(pair[0],pair[1],"isolation"),zip(rows,sessions)))
        result["concurrent_request_ids"] = [r["request_id"] for r in concurrent]
        foreign = httpx.get(GATEWAY+"/v1/requests/"+concurrent[0]["request_id"],
            headers={"Authorization":"Bearer "+sessions[1]},timeout=10,trust_env=False)
        result["foreign_session_status"] = foreign.status_code
    finally:
        lab.close()
    spans = read_collector(lab.directory/"collector.jsonl")
    ledger = json.loads((lab.directory/"ledger.json").read_text())
    result["isolation_grades"] = []
    for request_id in result["concurrent_request_ids"]:
        receipt = next(r for r in ledger["receipts"] if r["request_id"] == request_id)
        result["isolation_grades"].append(grade([s for s in spans if s["attributes"].get("request_id")==request_id],
                                               receipt, receipt["attempts"]))
    surfaces = list(lab.directory.glob("*.json"))+list(lab.directory.glob("*.jsonl"))
    result["canary_absent"] = all(canary not in p.read_text(encoding="utf-8") for p in surfaces)
    result["accepted"] = (result["receipt_count"]==1 and result["attempt_count_after_replay"]==1
        and result["observed_exit_code"]==86 and result["foreign_session_status"]==404
        and result["canary_absent"] and all(g["verdict"]=="complete" for g in result["isolation_grades"]))
    write_json(ROOT/"artifacts/accepted/recovery.json",result)
    print(json.dumps(result,indent=2))
    if not result["accepted"]:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
