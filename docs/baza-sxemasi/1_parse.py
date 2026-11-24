import ast,glob,json,sys,os
base=sys.argv[1]
models={}
for f in sorted(glob.glob(f'{base}/apps/*/models.py')+glob.glob(f'{base}/apps/*/models/*.py')):
    app=f.split('/apps/')[1].split('/')[0]
    t=ast.parse(open(f,encoding='utf-8').read())
    for c in t.body:
        if not isinstance(c,ast.ClassDef): continue
        bases=[ast.unparse(b) for b in c.bases]
        meta={}
        fields=[]
        for n in c.body:
            if isinstance(n,ast.Assign) and len(n.targets)==1 and isinstance(n.targets[0],ast.Name) and isinstance(n.value,ast.Call):
                fn=ast.unparse(n.value.func).split('.')[-1]
                if fn.endswith('Field') or fn in('ForeignKey','OneToOneField','ManyToManyField','SlugField','JSONField','UUIDField','FileField','ImageField','EmailField','URLField','GenericForeignKey'):
                    rel=None
                    if fn in('ForeignKey','OneToOneField','ManyToManyField') and n.value.args:
                        rel=ast.unparse(n.value.args[0]).strip("'\"")
                    od=next((ast.unparse(k.value) for k in n.value.keywords if k.arg=='on_delete'),None)
                    rn=next((ast.unparse(k.value) for k in n.value.keywords if k.arg=='related_name'),None)
                    nul=any(k.arg=='null' and ast.unparse(k.value)=='True' for k in n.value.keywords)
                    uniq=any(k.arg in('unique',) and ast.unparse(k.value)=='True' for k in n.value.keywords)
                    fields.append(dict(name=n.targets[0].id,type=fn,rel=rel,on_delete=od,related=rn,null=nul,unique=uniq))
            if isinstance(n,ast.ClassDef) and n.name=='Meta':
                for m in n.body:
                    if isinstance(m,ast.Assign) and isinstance(m.targets[0],ast.Name) and m.targets[0].id in('abstract','db_table','proxy'):
                        meta[m.targets[0].id]=ast.unparse(m.value)
        models[f'{app}.{c.name}']=dict(app=app,name=c.name,bases=bases,fields=fields,meta=meta,file=f.split('backend/')[-1] if 'backend/' in f else f)
json.dump(models,open(sys.argv[2],'w'),ensure_ascii=False,indent=1)
print(len(models),'classes')
for k,v in models.items(): print(k,v['bases'],v['meta'],len(v['fields']))
