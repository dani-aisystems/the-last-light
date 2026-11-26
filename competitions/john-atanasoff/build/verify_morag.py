"""Verify the precise dialogue consequences used in the slides against a fresh real-runner probe."""
import json, hashlib
from pathlib import Path
R=Path(__file__).resolve().parents[1]
log=R/'qa/redesign-review/morag-current.log'
rows=json.loads(next(x.split('MORAG_PROBE_RESULT ',1)[1] for x in log.read_text().splitlines() if 'MORAG_PROBE_RESULT ' in x))
expected=[('no_ch3_call',None,0,None),('lie_to_morag','lied_to_morag',-2,"You told me at half past one that the log was right. I'll not say anything about that on the air."),('deflect','deflected_morag',-1,'You asked me what it mattered, after eighteen years. Well. Now you know.'),('admit','admitted_to_morag',2,"You told me first. In the dark, with the set half dead. I'll remember that."),('admit_then_silence','admitted_to_morag',2,"I'll not put that in my log, Callum. You'll have to.")]
checks=[]
variants=[e[3] for e in expected[1:4]]
for row,(name,flag,rel,line) in zip(rows,expected,strict=True):
    lines=[x.split(': ',1)[1] for x in row['morag_lines_at_dawn']]
    assert row['case']==name
    assert row['rel_morag']==rel
    assert flag is None or row['flags'][flag]==1
    assert line is None or line in lines
    if line is None: assert all(v not in lines for v in variants)
    assert bool(row['flags'].get('told_truth'))==(name!='admit_then_silence')
    checks.append({'case':name,'pass':True,'expected_line':line,'actual_lines':lines,'relation':rel,'flag':flag})
out={'date':'2026-11-26','passed':len(checks),'total':len(expected),'log_sha256':hashlib.sha256(log.read_bytes()).hexdigest(),'checks':checks}
(R/'qa/redesign-review/MORAG_VERIFICATION.json').write_text(json.dumps(out,ensure_ascii=False,indent=2)+'\n')
print('Morag verification: 5/5, exact lines + flags + relationship + morning choice')
