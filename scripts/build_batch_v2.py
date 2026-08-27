#!/usr/bin/env python3
import json,re,sys
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
DATA=ROOT/'data'

def load(p,d):
    return json.loads(p.read_text(encoding='utf-8')) if p.exists() else d

def write(p,o,pretty=False):
    p.parent.mkdir(parents=True,exist_ok=True)
    p.write_text(json.dumps(o,ensure_ascii=False,indent=2 if pretty else None,separators=None if pretty else (',',':')),encoding='utf-8')

def shard(pid):
    s=((pid-1)//500)*500+1
    return f'{s:05d}-{s+499:05d}.json'

def extract_codes(text):
    out=[]
    for m in re.findall(r'\b\d{4}(?:\s?\d{2})?(?:\s?\d{3})?(?:\s?\d)?\b',str(text or '')):
        v=m.replace(' ','')
        if len(v) >= 4 and v not in out:
            out.append(v)
    return out[:12]

def merge_sources(batch):
    incoming=batch.get('sources') or {}
    if not incoming: return
    store=load(DATA/'sources.json',{'version':1,'sources':{}})
    store['version']=max(int(store.get('version',1)),11)
    store.setdefault('sources',{}).update(incoming)
    write(DATA/'sources.json',store,pretty=True)

def union_source_ids(product):
    out=[]
    for sid in product.get('sourceIds',[]):
        if sid not in out: out.append(sid)
    for v in product.get('variants',[]):
        for sid in v.get('sourceIds',[]):
            if sid not in out: out.append(sid)
    return out

def overall_marking(product):
    variants=product.get('variants',[])
    dims={}
    for key in ('current','future','experiment'):
        statuses=[]; labels=[]
        for v in variants:
            item=(v.get('marking') or {}).get(key) or {}
            st=item.get('status','unknown'); statuses.append(st)
            if item.get('label') and item.get('label') not in labels: labels.append(item['label'])
        if not statuses:
            dims[key]={'status':'unknown'}
        elif all(x=='yes' for x in statuses):
            dims[key]={'status':'yes','label':labels[0] if len(labels)==1 else 'Во всех реалистичных вариантах: да'}
        elif all(x=='no' for x in statuses):
            dims[key]={'status':'no','label':labels[0] if len(labels)==1 else 'Во всех реалистичных вариантах: не обнаружен'}
        elif key=='experiment' and any(x=='yes' for x in statuses):
            dims[key]={'status':'yes','label':'Есть хотя бы один вариант, попадающий в эксперимент/пилот'}
        else:
            dims[key]={'status':'unknown','label':'Зависит от точной классификации конкретного товара'}
    return dims

def overall_documents(product):
    variants=product.get('variants',[])
    results={v.get('result') for v in variants}
    if variants and results=={'green'}:
        return {'status':'none','items':[],'refusalLetter':'Высокая вероятность / зависит от окончательного кода','basis':'Все зафиксированные реалистичные варианты имеют низкую регуляторную нагрузку. Окончательный документ подтверждается после точного ТН ВЭД.'}
    if variants and results=={'red'}:
        return {'status':'mandatory','items':[],'refusalLetter':'Как основной документ — обычно нет','basis':'Во всех зафиксированных реалистичных вариантах есть существенные обязательные требования.'}
    return {'status':'check','items':[],'refusalLetter':'Зависит от выбранного ТН ВЭД','basis':'Набор обязательных документов различается между возможными вариантами классификации.'}

def main():
    if len(sys.argv)<2:
        raise SystemExit('Usage: build_batch_v2.py data-src/batch-v2-*.json [more...]')
    summary=load(DATA/'compliance-summary.json',{})
    detail_files={}; rule_files={}; total_added=0; last_checked=None
    for arg in sys.argv[1:]:
        path=ROOT/arg; batch=load(path,{})
        merge_sources(batch)
        checked=batch.get('checkedAt','2026-08-27'); last_checked=checked
        for p in batch.get('products',[]):
            pid=int(p['id']); total_added+=1; sh=shard(pid)
            detail_files.setdefault(sh,load(DATA/'compliance/details'/sh,{}))
            rule_files.setdefault(sh,load(DATA/'rules/products'/sh,{}))
            variants=p.get('variants',[]); candidates=[]; seen=[]
            for v in variants:
                code=str(v.get('code','')).strip()
                if not code or code in seen: continue
                seen.append(code)
                candidates.append({'code':code,'confidence':v.get('confidence','средний'),'description':v.get('when','Предварительный вариант классификации'),'sourceIds':v.get('sourceIds',[])})
            detail={'normalizedName':p.get('name',''),'marking':overall_marking(p),'tnved':{'candidates':candidates,'needsClarification':p.get('influences',[])},'documents':overall_documents(p),'sourceIds':union_source_ids(p),'lastChecked':checked,'screeningReason':p.get('screeningReason','')}
            detail_files[sh][str(pid)]=detail
            scenarios=[]
            for i,v in enumerate(variants,1):
                code=str(v.get('code','')).strip()
                if not code: continue
                scenarios.append({'label':v.get('when') or f'Вариант {i}','note':v.get('note',''),'sourceIds':v.get('sourceIds',[]),'output':{'tnvedCandidates':[{'code':code}],'documents':v.get('documents') or {'status':'check','items':[]},'marking':v.get('marking') or {},'result':v.get('result',p.get('result','yellow')),'sourceIds':v.get('sourceIds',[])}})
            rule_files[sh][str(pid)]={'questionIds':[],'scenarios':scenarios}
            all_codes=[]
            for v in variants:
                for c in extract_codes(v.get('code','')):
                    if c not in all_codes: all_codes.append(c)
            marks=detail['marking']; flags=[]
            for v in variants:
                d=v.get('documents') or {}
                for item in d.get('items',[]):
                    typ=item.get('type') if isinstance(item,dict) else None
                    if typ and typ not in flags: flags.append(typ)
                if d.get('status')=='none' and 'none' not in flags: flags.append('none')
                if d.get('refusalLetter') and 'refusal' not in flags and 'Нет' not in str(d.get('refusalLetter')): flags.append('refusal')
            if not flags: flags=['unknown']
            summary[str(pid)]={'result':p.get('result','yellow'),'markingCurrent':marks['current'].get('status','unknown'),'markingFuture':marks['future'].get('status','unknown'),'experiment':marks['experiment'].get('status','unknown'),'documentFlags':flags,'tnvedCodes':all_codes,'lastChecked':checked}
    write(DATA/'compliance-summary.json',summary)
    for n,o in detail_files.items(): write(DATA/'compliance/details'/n,o)
    for n,o in rule_files.items(): write(DATA/'rules/products'/n,o)
    meta=load(DATA/'meta.json',{}); stats={'green':0,'yellow':0,'red':0}
    for s in summary.values():
        if s.get('result') in stats: stats[s['result']]+=1
    meta['complianceStatus']='partial'; meta['checkedProducts']=len(summary); meta['screeningStats']=stats
    if last_checked: meta['lastComplianceBuild']=last_checked
    write(DATA/'meta.json',meta,pretty=True)
    print(f'Batch v2 merged {total_added} products; total {len(summary)}; stats {stats}')

if __name__=='__main__': main()
