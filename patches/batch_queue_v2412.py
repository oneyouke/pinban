from __future__ import annotations

from dataclasses import dataclass, asdict, field
from datetime import datetime, timezone
from pathlib import Path
import json, os, tempfile, traceback, uuid
from typing import Callable, Any

VALID_STATES = {'pending','running','success','failed','cancelled'}


def _now():
    return datetime.now(timezone.utc).isoformat()


@dataclass
class BatchJob:
    workspace_path: str
    output_path: str
    name: str = ''
    job_id: str = field(default_factory=lambda: uuid.uuid4().hex)
    state: str = 'pending'
    attempts: int = 0
    created_at: str = field(default_factory=_now)
    started_at: str = ''
    finished_at: str = ''
    error: str = ''
    result: dict = field(default_factory=dict)

    def to_dict(self): return asdict(self)

    @classmethod
    def from_dict(cls, data):
        obj = cls(str(data.get('workspace_path') or ''), str(data.get('output_path') or ''), str(data.get('name') or ''))
        for key in ('job_id','state','attempts','created_at','started_at','finished_at','error','result'):
            if key in data: setattr(obj,key,data[key])
        if obj.state not in VALID_STATES: obj.state='pending'
        return obj


@dataclass
class BatchQueue:
    jobs: list[BatchJob] = field(default_factory=list)
    schema_version: int = 1

    def add(self, workspace_path: str, output_path: str, name: str='') -> BatchJob:
        job=BatchJob(str(workspace_path),str(output_path),name or Path(workspace_path).stem)
        self.jobs.append(job); return job

    def retry_failed(self):
        count=0
        for j in self.jobs:
            if j.state=='failed':
                j.state='pending'; j.error=''; j.started_at=''; j.finished_at=''; count+=1
        return count

    def cancel_pending(self):
        for j in self.jobs:
            if j.state=='pending': j.state='cancelled'; j.finished_at=_now()

    def to_dict(self): return {'schema_version':self.schema_version,'jobs':[j.to_dict() for j in self.jobs]}

    @classmethod
    def from_dict(cls,data): return cls([BatchJob.from_dict(x) for x in (data.get('jobs') or [])],int(data.get('schema_version',1)))


def save_queue(path: str|Path, queue: BatchQueue):
    path=Path(path); path.parent.mkdir(parents=True,exist_ok=True)
    fd,tmp=tempfile.mkstemp(prefix=path.name+'.',suffix='.tmp',dir=str(path.parent)); os.close(fd)
    tmp=Path(tmp)
    try:
        tmp.write_text(json.dumps(queue.to_dict(),ensure_ascii=False,indent=2),encoding='utf-8')
        with tmp.open('r+b') as f:
            f.flush(); os.fsync(f.fileno())
        os.replace(tmp,path)
    finally:
        if tmp.exists(): tmp.unlink(missing_ok=True)
    return path


def load_queue(path: str|Path):
    return BatchQueue.from_dict(json.loads(Path(path).read_text(encoding='utf-8')))


def run_batch(queue: BatchQueue, executor: Callable[[BatchJob], dict|None], *, on_update: Callable[[BatchJob],Any]|None=None, stop_on_error: bool=False):
    """Run pending jobs. Executor performs the real preflight + production export for one job.
    Every job is isolated: an exception becomes failed state and later jobs continue by default.
    """
    summary={'success':0,'failed':0,'cancelled':0,'skipped':0}
    for job in queue.jobs:
        if job.state=='cancelled': summary['cancelled']+=1; continue
        if job.state!='pending': summary['skipped']+=1; continue
        job.state='running'; job.attempts+=1; job.started_at=_now(); job.finished_at=''; job.error=''; job.result={}
        if on_update: on_update(job)
        try:
            ws=Path(job.workspace_path)
            if not ws.is_file(): raise FileNotFoundError(f'工作区不存在：{ws}')
            out=Path(job.output_path)
            out.parent.mkdir(parents=True,exist_ok=True)
            result=executor(job) or {}
            if not isinstance(result,dict): result={'value':result}
            job.result=result; job.state='success'; summary['success']+=1
        except Exception as exc:
            job.state='failed'; summary['failed']+=1
            job.error=f'{type(exc).__name__}: {exc}'
            job.result={'traceback':traceback.format_exc(limit=8)}
        finally:
            job.finished_at=_now()
            if on_update: on_update(job)
        if job.state=='failed' and stop_on_error: break
    return summary
