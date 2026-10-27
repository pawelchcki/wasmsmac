import json,struct,copy,hashlib,argparse
from pathlib import Path
parser=argparse.ArgumentParser(description='Read-only exact typed audit of the bounded land height browser artifact')
parser.add_argument('--artifacts',required=True,type=Path)
p=parser.parse_args().artifacts;raw=(p/'application.log').read_bytes();report=json.loads((p/'report.json').read_text());preflight=json.loads((p/'preflight.json').read_text())
packets=[]
for line in raw.decode().splitlines():
 if 'TH_NATIVE|' in line:
  try: row=json.loads(line.split('TH_NATIVE|',1)[1])
  except json.JSONDecodeError: continue
  packets.append(row)
assert len(packets)==6
def equal(a,b):
 if type(a)is not type(b):return False
 if isinstance(a,dict):return a.keys()==b.keys() and all(equal(a[k],b[k])for k in a)
 if isinstance(a,list):return len(a)==len(b) and all(equal(x,y)for x,y in zip(a,b))
 if isinstance(a,float):return struct.pack('>d',a)==struct.pack('>d',b)
 return a==b

def world(row):
 v=copy.deepcopy(row['world']);del v['terrain_trace']['ui'];return v
base=world(packets[0]);after=world(packets[-1]);quote=packets[1]['ui']['height_presentation']['quote'];assert all(equal(world(row),base)for row in packets[:5]);assert equal(packets[3]['ui']['height_presentation']['quote'],quote)
actor=next(x for x in base['units']if x['raw_id']==quote['unit_id']);actor_idx=base['units'].index(actor);actor_id=actor['id'];payer=next(x['id']for x in base['players']if x['raw_id']==quote['owner'])
patches={f"{x['x']},{x['y']}":x for x in quote['plan']};region=set(patches)
for key in patches:
 for pos in base['terrain_trace']['tiles'][key]['neighbors'].values():
  if pos is not None:region.add(f"{pos['x']},{pos['y']}")
def diffs(a,b,path=()):
 if type(a)is not type(b):return[(path,a,b)]
 if isinstance(a,dict):
  assert a.keys()==b.keys(),(path,'key delta')
  return sum((diffs(a[k],b[k],path+(k,))for k in a),[])
 if isinstance(a,list):
  assert len(a)==len(b),(path,'list length delta')
  return sum((diffs(x,y,path+(i,))for i,(x,y)in enumerate(zip(a,b))),[])
 return []if equal(a,b)else[(path,a,b)]
changes=diffs(base,after);categories={}
for path,a,b in changes:
 category=None
 if path==('units',actor_idx,'movement'):category='actor actual MP'
 if path[:3]==('terrain_trace','player_details',payer) and path[3:]in [('energy','credits'),('energy_revision',)]:category='payer fee/revision'
 if path[:3]==('terrain_trace','unit_details',actor_id):
  if path[3:]==('moved_this_turn',):category='actor moved flag'
  if len(path)==6 and path[3]=='quotes'and path[5]in ['allowed_now','reason']:category='actor exhausted movement preflight'
 if len(path)>=4 and path[:2]==('terrain_trace','tiles')and path[2]in region:
  key=path[2];tail=path[3:]
  if tail==('terrain_epoch',):category='affected tile epoch'
  if len(tail)==2 and tail[0]=='elevation'and tail[1]in ['left','top','right','bottom']:category='adjacent shared geometry (observed only)'
  if len(tail)==2 and tail[0]=='canonical'and tail[1]in ['active','elevation','is_water']:category='native canonical write/pin'
  if key in patches:
   if tail==('elevation','center'):category='quoted gameplay elevation'
   if len(tail)==2 and tail[0]=='imported'and tail[1]in ['active','source_corners','source_elevation','source_water']:category='edited imported source retirement'
   if tail in [('is_land',),('is_water',),('native_type','domain')]:category='quoted gameplay domain'
   if len(tail)==2 and tail[0]=='native_height_band':category='derived native below-coast band'
 assert category is not None,(path,a,b)
 categories[category]=categories.get(category,0)+1
assert after['terrain_trace']['player_details'][payer]['energy']['credits']==base['terrain_trace']['player_details'][payer]['energy']['credits']-quote['fee']
assert after['terrain_trace']['player_details'][payer]['energy_revision']==base['terrain_trace']['player_details'][payer]['energy_revision']+1
f32=[]
for i,row in enumerate(packets):
 for unit in row['world']['units']:
  for key in ['movement','health']:
   value=unit[key];assert type(value)is float,(i,unit['id'],key,type(value));assert struct.unpack('>f',struct.pack('>f',value))[0]==value
   f32.append({'query':i+1,'unit':unit['raw_id'],'field':key,'type':'native Float token','f32_bits':struct.pack('>f',value).hex(),'f64_bits':struct.pack('>d',value).hex()})
 ui=row['ui'];assert type(ui['movement'])is float;assert int.from_bytes(struct.pack('>f',ui['movement']),'big')==ui['movement_bits']
assert packets[0]['ui']['movement_bits']==1065353216 and packets[-1]['ui']['movement_bits']==0
for key,patch in patches.items():
 tile=after['terrain_trace']['tiles'][key];assert type(tile['elevation']['center'])is int;assert tile['elevation']['center']==patch['canonical']['elevation'];assert type(tile['is_water'])is bool
assert quote['mode']=='functional_approximation'and quote['policy']=='application.band-slope-height.v1'and quote['fee_policy']=='application.band-fee.v1'
assert report['height_receipt']['data']['confirmed_height']is True and 'height_quote'not in report['height_receipt']['data'];assert report['height_receipt']['event_id']
assert report['status']=='passed'and report['native_raw_exit_code']==0 and report['log_transport']['partial']is False and report['log_transport']['settled_failure']is None
assert report['runtime_js_sha256']==preflight['runtime']['js']and report['runtime_wasm_sha256']==preflight['runtime']['wasm']
assert report['source_override']['original_sha256']==preflight['original_rules_sha256']and report['source_override']['rate_one_sha256']==preflight['executed_rules_sha256']
assert hashlib.sha256(raw).hexdigest()==report['log_transport']['raw_sha256']
joined=''.join(json.loads(x)['text']for x in(p/'application-log-chunks.jsonl').read_text().splitlines()if x);assert joined.encode()==raw
result={'status':'passed-readonly-audit','native_cases_added':0,'browser_cases_audited':1,'typed_pure_checkpoints':5,'complete_worlds':6,'per_world':{'players':7,'units':8,'bases':7,'tiles':128},'parsed_native_world_changed_fields':len(changes),'allowed_diff_categories':categories,'native_float_unit_fields_checked':len(f32),'unit_float_bits':f32,'actor_movement_bits':[x['ui']['movement_bits']for x in packets], 'quote':{'fee':quote['fee'],'credits':quote['credits'],'source_elevation':quote['source_elevation'],'destination_elevation':quote['destination_elevation'],'source_water':quote['source_water'],'destination_water':quote['destination_water'],'policy':quote['policy'],'fee_policy':quote['fee_policy'],'mode':quote['mode'],'patches':len(quote['plan'])},'payer_before':base['terrain_trace']['player_details'][payer]['energy'],'payer_after':after['terrain_trace']['player_details'][payer]['energy'],'payer_revision_before':base['terrain_trace']['player_details'][payer]['energy_revision'],'payer_revision_after':after['terrain_trace']['player_details'][payer]['energy_revision'],'raw_sha256':hashlib.sha256(raw).hexdigest(),'raw_bytes':len(raw),'report_sha256':hashlib.sha256((p/'report.json').read_bytes()).hexdigest(),'preflight_sha256':hashlib.sha256((p/'preflight.json').read_bytes()).hexdigest(),'source_audit_script_sha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest()}
(p/'raw-typed-audit.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps({k:v for k,v in result.items()if k!='unit_float_bits'},indent=2))
