from pathlib import Path
import json, tempfile
import fitz

from batch_queue import BatchQueue, run_batch
from batch_executor import execute_batch_job
from workspace import save_workspace
from product import APP_VERSION

with tempfile.TemporaryDirectory(prefix='批量生产执行器_') as td:
    root=Path(td)
    src=root/'源文件.pdf'
    doc=fitz.open(); doc.new_page(width=595,height=842); doc.save(src); doc.close()

    ws=root/'自动拼版.dipw'
    save_workspace(ws,{
        'schema_version':1,
        'app_version':'2.4.13',
        'page_canvas':{
            'sheet':{'width_mm':320,'height_mm':450,'bleed_mm':3,'snap_mm':2},
            'placements':[{'path':str(src),'page_index':0,'width_pt':595,'height_pt':842,'x_mm':0,'y_mm':0,'rotation':0,'locked':False}],
        },
        'print_marks':{},
    })
    out=root/'输出'/'生产.pdf'
    q=BatchQueue(); q.add(str(ws),str(out),'正常任务')
    summary=run_batch(q,execute_batch_job)
    assert summary['success']==1, q.jobs[0].error
    actual=Path(q.jobs[0].result['output'])
    assert actual.exists(), actual
    assert actual.stat().st_size>100
    assert q.jobs[0].result.get('output_sha256')

    # V2.4.13-2.4.18 fail closed; V2.4.19 enables verified legacy manual-layout production.
    bad_ws=root/'手工版位.dipw'
    save_workspace(bad_ws,{
        'schema_version':1,
        'page_canvas':{
            'sheet':{'width_mm':320,'height_mm':450},
            'placements':[{'path':str(src),'page_index':0,'width_pt':595,'height_pt':842,'x_mm':10,'y_mm':20,'rotation':0,'locked':False}],
        },
        'print_marks':{},
    })
    q2=BatchQueue(); q2.add(str(bad_ws),str(root/'manual.pdf'),'手工版位')
    summary2=run_batch(q2,execute_batch_job)
    version=tuple(int(x) for x in APP_VERSION.split('.')[:3])
    if version >= (2,4,19):
        assert summary2['success']==1, q2.jobs[0].error
        manual_output=Path(q2.jobs[0].result['output'])
        assert manual_output.exists() and manual_output.stat().st_size>100
    else:
        assert summary2['failed']==1
        assert '手工版位' in q2.jobs[0].error

print('V2.4.13 BATCH EXECUTOR PASS')
