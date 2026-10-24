"""First-city production source controls with literal phase/display observations."""
from protocol import ProtocolError
ALGORITHM='ui.initial_production_controls.v2'
PROFILES={('GAIANS','CITIZEN','stock'),('HIVE','CITIZEN','stock'),('GAIANS','TALENT','stock'),('GAIANS','CITIZEN','gaian-physics'),('GAIANS','CITIZEN','gaian-formers-cost-4'),('GAIANS','CITIZEN','gaian-formers-cost-8'),('GAIANS','CITIZEN','gaian-mineral-rule-12'),('GAIANS','CITIZEN','gaian-industry-minus-1')}
def validate_input(d):
    if not isinstance(d,dict) or set(d)!={'faction','difficulty','text_profile','world_width','world_height','map_route','research','target_id'} or any(type(d[k]) is not int for k in ('world_width','world_height','target_id')) or (d['faction'],d['difficulty'],d['text_profile']) not in PROFILES or (d['world_width'],d['world_height'],d['target_id'])!=(40,80,5) or d['map_route']!='load-map' or d['research']!='directed':raise ProtocolError('unsupported first-city production control')
def validate_output(d):
    if not isinstance(d,dict) or set(d)!={'first_city_before_panels','ready_before_panels','operations','after_operations','panel','after_panel','social_after','after_social'}:raise ProtocolError('incomplete phase production observation')
    for key in ('first_city_before_panels','ready_before_panels','after_operations','after_panel','after_social'):
        n=d[key]
        if not isinstance(n,dict) or set(n)!={'turn','faction_id','difficulty','map_kind','map_area_sqrt','raw_mineral_field','current_project_id','queue_size','industry_rating','mineral_rule_factor','owned_ids','city'} or any(type(n[k]) is not int for k in n if k not in ('owned_ids','city')):raise ProtocolError('invalid native production phase')
    if set(d['operations'])!={'project','pair','turns'} or len(d['operations']['pair'])!=2 or any(type(v) is not int for v in d['operations']['pair']):raise ProtocolError('invalid literal production report')
    if set(d['panel'])!={'project','turns','mineral_intake','mineral_consumption','mineral_surplus','allocation','labs_income'}:raise ProtocolError('incomplete actual resource panel')
    if set(d['social_after'])!={'industry'} or type(d['social_after']['industry']) is not int:raise ProtocolError('invalid displayed industry')
