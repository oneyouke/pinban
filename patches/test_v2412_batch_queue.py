from pathlib import Path
import tempfile
from batch_queue import BatchQueue, save_queue, load_queue, run_batch

with tempfile.TemporaryDirectory() as td:
    td=Path(td)
    ws1=td/'订单甲.dipw'; ws2=td/'订单乙.dipw'; ws3=td/'缺失.dipw'
    ws1.write_text('{"schema_version":1}',encoding='utf-8')
    ws2.write_text('{"schema_version":1}',encoding='utf-8')
    q=BatchQueue()
    a=q.add(ws1,td/'out'/'a.pdf','甲')
    b=q.add(ws3,td/'out'/'b.pdf','坏单')
    c=q.add(ws2,td/'out'/'c.pdf','乙')
    qp=save_queue(td/'队列.json',q)
    q=load_queue(qp)
    assert len(q.jobs)==3 and q.jobs[0].name=='甲'

    calls=[]
    def executor(job):
        calls.append(job.name)
        Path(job.output_path).write_bytes(b'%PDF-1.4\n%%EOF\n')
        return {'ok':True,'output':job.output_path}

    s=run_batch(q,executor)
    assert s['success']==2 and s['failed']==1
    assert calls==['甲','乙'], calls
    assert q.jobs[1].state=='failed' and '工作区不存在' in q.jobs[1].error
    assert q.jobs[2].state=='success'
    assert q.jobs[0].attempts==1

    assert q.retry_failed()==1
    assert q.jobs[1].state=='pending'
    ws3.write_text('{"schema_version":1}',encoding='utf-8')
    s2=run_batch(q,executor)
    assert s2['success']==1 and q.jobs[1].attempts==2

    save_queue(qp,q)
    q2=load_queue(qp)
    assert all(j.state=='success' for j in q2.jobs)

print('V2.4.12 batch queue tests passed')
