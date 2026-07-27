def bind_preview(preview_id: str, generation: int, actor: str) -> dict[str, object]:
    return {"preview_id": preview_id, "generation": generation, "actor": actor, "used": False}


def consume(binding: dict[str, object], generation: int) -> None:
    if binding["used"] or binding["generation"] != generation:
        raise ValueError("approval replay or generation mismatch")
    binding["used"] = True
