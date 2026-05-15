from fastapi import APIRouter

from scout.main import scheduler

router = APIRouter(prefix="/v1/scout")


@router.get("/status")
async def status() -> dict:
    jobs = [
        {
            "id": job.id,
            "next_run_time": job.next_run_time.isoformat()
            if job.next_run_time
            else None,
        }
        for job in scheduler.get_jobs()
    ]
    return {
        "scheduler_running": scheduler.running,
        "jobs": jobs,
        "job_count": len(jobs),
    }


@router.post("/scheduler/pause")
async def pause_scheduler() -> dict:
    scheduler.pause()
    return {"paused": True}


@router.post("/scheduler/resume")
async def resume_scheduler() -> dict:
    scheduler.resume()
    return {"paused": False}
