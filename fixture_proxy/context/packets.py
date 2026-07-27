import hashlib


def select_packet(task_id: str, content: str) -> dict[str, str]:
    return {"task_id": task_id, "content": content, "sha256": hashlib.sha256(content.encode()).hexdigest()}


def reject_stale(packet: dict[str, str], expected_sha256: str) -> None:
    if packet["sha256"] != expected_sha256:
        raise ValueError("stale context packet")
