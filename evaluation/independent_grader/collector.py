"""Parse Collector file exporter output, independently of runtime export code."""

import json
from pathlib import Path


def attributes(items):
    result = {}
    for item in items:
        value = item.get("value", {})
        for kind in ("stringValue", "intValue", "doubleValue", "boolValue"):
            if kind in value:
                result[item["key"]] = int(value[kind]) if kind == "intValue" else value[kind]
                break
    return result


def read_collector(path: Path):
    if not path.is_file():
        return []
    spans = []
    for line in path.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        record = json.loads(line)
        for resource in record.get("resourceSpans", []):
            rattr = attributes(resource.get("resource", {}).get("attributes", []))
            for scope in resource.get("scopeSpans", []):
                for span in scope.get("spans", []):
                    spans.append(
                        {
                            "name": span["name"],
                            "trace_id": span["traceId"],
                            "span_id": span["spanId"],
                            "parent_id": span.get("parentSpanId"),
                            "start_ns": int(span["startTimeUnixNano"]),
                            "end_ns": int(span["endTimeUnixNano"]),
                            "service": rattr.get("service.name"),
                            "process_id": rattr.get("process.pid"),
                            "attributes": attributes(span.get("attributes", [])),
                        }
                    )
    return spans
