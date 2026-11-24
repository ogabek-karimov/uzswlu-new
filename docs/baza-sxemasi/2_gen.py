import json,sys,os,re
m=json.load(open(sys.argv[1])); out=sys.argv[2]; os.makedirs(out,exist_ok=True)
# abstract meros: AttachmentBase maydonlari
ab=m['content.AttachmentBase']['fields']
for k,v in m.items():
    if 'AttachmentBase' in v['bases']: v['fields']=ab+v['fields']
    if 'SingletonModel' in v['bases']: v['singleton']=True
concrete={k:v for k,v in m.items() if v['meta'].get('abstract')!='True'}
def ent(k): return k.replace('.','_')
def resolve(app,rel):
    if rel=='self': return None
    if rel=='settings.AUTH_USER_MODEL': return 'accounts.User'
    if '.' in rel: return rel
    return f'{app}.{rel}'
fk=[]
for k,v in concrete.items():
    for f in v['fields']:
        if f['rel']:
            t=resolve(v['app'],f['rel']) if f['rel']!='self' else k
            fk.append((k,f['name'],t,f))
soft=[('accounts.User','role','accounts.Role','slug'),('accounts.User','scope','structure.Faculty','slug'),
 ('structure.Department','faculty_slug','structure.Faculty','slug'),
 ('accounts.User','hemis_id','structure.StaffProfile','hemis_id'),('accounts.StaffSession','hemis_id','structure.StaffProfile','hemis_id'),
 ('structure.StaffDocument','hemis_id','structure.StaffProfile','hemis_id'),('content.Leader','staff_id','structure.StaffProfile','hemis_id'),
 ('accounts.StaffTask','assignee_id','structure.StaffProfile','hemis_id'),('accounts.StaffTask','author_id','structure.StaffProfile','hemis_id'),
 ('content.Post','sdg','pages.SdgGoal','number'),
 ('core.Activity','entity+entity_id','*','har qanday yozuv'),('panel.Version','entity+entity_id','*','har qanday yozuv')]
json.dump({'fk':[(a,b,c) for a,b,c,_ in fk],'soft':soft,'models':list(concrete)},open(f'{out}/rels.json','w'),ensure_ascii=False,indent=1)
def card(f):
    return {'ForeignKey':'many','OneToOneField':'one','ManyToManyField':'many'}[f['type']]
def attrs(k,v,full=True):
    rows=[]
    rows.append('        int id PK')
    for f in v['fields']:
        if f['name']=='id': continue
        t=re.sub('Field$','',f['type']).replace('ForeignKey','FK').replace('ManyToMany','M2M').replace('OneToOne','O2O')
        flag=' FK' if f['type'] in('ForeignKey','OneToOneField') else ''
        if f['unique'] or f['name'] in('slug','hemis_id') and k in('accounts.Role','structure.Faculty','structure.StaffProfile','pages.Page'): flag+=' UK' if not flag else ''
        if f['type']=='ManyToManyField': continue
        rows.append(f'        {t.lower() if t!="FK" else "int"} {f["name"]}{flag}')
    return rows
def diagram(keys,title):
    keys=list(keys); ks=set(keys); lines=['erDiagram']
    ext=set()
    rl=[]
    for a,fname,t,f in fk:
        if a in ks or t in ks:
            if t is None or t not in concrete: continue
            ext.update(x for x in (a,t) if x not in ks)
            if f['type']=='ManyToManyField': rl.append(f'    {ent(a)} }}o--o{{ {ent(t)} : "{fname} (M2M)"')
            else:
                lab=f'{fname}'+(' ✕cascade' if f['on_delete'] and 'CASCADE' in f['on_delete'] else ' protect' if f['on_delete'] and 'PROTECT' in f['on_delete'] else '')
                left='|o' if f['null'] else '||'
                if f['type']=='OneToOneField': rl.append(f'    {ent(t)} {left}--o| {ent(a)} : "{lab}"')
                else: rl.append(f'    {ent(t)} {left}--o{{ {ent(a)} : "{lab}"')
    for a,fa,t,ft in soft:
        if t=='*':
            if a in ks: rl.append(f'    {ent(a)} }}o..o| ANY_MODEL : "{fa}"')
            continue
        if a in ks or t in ks:
            ext.update(x for x in (a,t) if x not in ks)
            rl.append(f'    {ent(t)} |o..o{{ {ent(a)} : "{fa} → {ft}"')
    for k in keys: 
        lines.append(f'    {ent(k)} {{'); lines+=attrs(k,concrete[k]); lines.append('    }')
    for k in sorted(ext):
        lines.append(f'    {ent(k)} {{\n        string tashqi_model\n    }}')
    if any('ANY_MODEL' in r for r in rl): lines.append('    ANY_MODEL {\n        string polimorf\n    }')
    return '\n'.join(lines+sorted(set(rl)))+'\n'
groups={'accounts':'Foydalanuvchilar va rollar','core':'Media, sayt sozlamalari, faollik','content':'Kontent: yangilik, hujjat, video, rahbarlar','pages':'Sahifalar va BRM (SDG)','structure':'Tuzilma: fakultet, kafedra, qabul, aloqa','panel':'Panel: kirishlar, versiyalar','hemis':'HEMIS'}
for g in groups:
    ks=[k for k in concrete if concrete[k]['app']==g]
    open(f'{out}/{g}.mmd','w',encoding='utf-8').write(diagram(ks,groups[g]))
# overview: faqat nomlar (atributlarsiz)
ov=['erDiagram']; seen=set()
for a,fname,t,f in fk:
    if t not in concrete or a==t and False: continue
    cardn='|o' if f['null'] else '||'
    ov.append(f'    {ent(t)} {cardn}--o{{ {ent(a)} : "{fname}"' + '"' if False else f'    {ent(t)} {cardn}--o{{ {ent(a)} : "{fname}"')
for a,fa,t,ft in soft:
    if t!='*': ov.append(f'    {ent(t)} |o..o{{ {ent(a)} : "{fa}"')
for k in concrete: ov.append(f'    {ent(k)}')
open(f'{out}/overview.mmd','w',encoding='utf-8').write('\n'.join(ov)+'\n')
print(len(concrete),'modellar',len(fk),'FK/M2M',len(soft),'mantiqiy')
