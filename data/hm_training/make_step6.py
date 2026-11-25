import json
from pathlib import Path
p=Path('data/hm_training')
base=[json.loads(x) for x in (p/'examples.step5-A-C.candidate-v2.jsonl').read_text(encoding='utf8').splitlines()]
old=[json.loads(x) for x in (p/'examples.context.step3-compact.draft.jsonl').read_text(encoding='utf8').splitlines()]
sy=old[0]['messages'][0]['content']
def row(i,q,a):
 ans={'reply':a,'citations':[],'engine_claims':[],'hint_level':0,'suggested_actions':[],'intent':'concept'}
 return {'id':f'HM6-{i:02d}','split':'train','group_id':f'step6-{i:02d}','source_id':'HM-ORIGINAL-SYNTHETIC-STEP6-V1','reviewed_by_human':False,'rights_cleared':False,'approved_for_training':False,'allowed_block_ids':[],'candidate_status':'candidate_pending_human_review','messages':[{'role':'system','content':sy},{'role':'user','content':f'MODE: chat\n\n<<<HM_DATA kind="QUESTION">>>\n{q}\n<<<HM_END>>>''},{'role':'assistant','content':json.dumps(ans,ensure_ascii=False,separators=(',',':'))}]}
more=[('Trong G trưởng, Em7 mang số La Mã nào?','Trong G trưởng, Em7 là vi7.'),('Từ E lên G là quãng gì?','Từ E lên G là quãng ba thứ (m3).'),('Trong D trưởng, A7 là bậc nào?','Trong D trưởng, A7 là V7. Mình dùng giọng bạn nêu, không dùng giọng đang chọn trên giao diện.'),('Trong F trưởng, Gm7 mang số La Mã nào?','Trong F trưởng, Gm7 là ii7.')]
rows=base+[row(i+1,q,a) for i,(q,a) in enumerate(more)]
out=p/'examples.step6-4.candidate.jsonl'
out.write_text('\n'.join(json.dumps(x,ensure_ascii=False,separators=(',',':')) for x in rows)+'\n',encoding='utf8')
print(out,len(rows))
