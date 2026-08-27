#!/usr/bin/env python3
import json, re
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
DATA=ROOT/'data'
SRC=ROOT/'data-src'/'shoes-01.json'

YELLOW_MODES={'shoe_part','sports_equipment','carnival_shoe','shoe_ambiguous'}

CLARIFY={
 'shoe_general':['материал верха','материал подошвы','водонепроницаемость','взрослое или детское назначение'],
 'shoe_sport':['материал верха','материал подошвы','вид спортивной обуви','взрослое или детское назначение'],
 'ski_boot':['материал верха/подошвы','конструкция лыжного ботинка','взрослое или детское назначение'],
 'felt_shoe':['материал верха','наличие и материал отдельной подошвы','взрослое или детское назначение'],
 'rubber_shoe':['водонепроницаемость','способ соединения верха и подошвы','взрослое или детское назначение'],
 'shoe_ppe':['материал верха','защитные свойства СИЗ','металлический подносок','взрослое или детское назначение'],
 'work_shoe':['материал верха','защитные свойства СИЗ','металлический подносок','взрослое или детское назначение'],
 'shoe_part':['конкретная деталь','материал','самостоятельное готовое изделие или запчасть','защитное назначение'],
 'ice_skates':['комплектные коньки с прикрепленным лезвием или только ботинок','взрослое/детское назначение'],
 'roller_skates':['комплектные роликовые коньки с прикрепленными роликами или только ботинок','взрослое/детское назначение'],
 'fins':['действительно ли это плавательные ласты','взрослое/детское назначение','игровое или спортивное назначение'],
 'carnival_shoe':['настоящая многоразовая обувь или только праздничный реквизит','наличие подошвы','материал'],
 'half_shoe':['наличие собственной подошвы','конструкция и степень покрытия стопы','материал'],
 'warmup_bootie':['наличие собственной подошвы','самостоятельная обувь или текстильный чехол/аксессуар','материал']
}

def load(path, default):
    return json.loads(path.read_text(encoding='utf-8')) if path.exists() else default

def write(path,obj):
    path.parent.mkdir(parents=True,exist_ok=True)
    path.write_text(json.dumps(obj,ensure_ascii=False,separators=(',',':')),encoding='utf-8')

def codes(text):
    out=[]
    for m in re.findall(r'\b\d{4}(?:\s?\d{2})?(?:\s?\d{3})?(?:\s?\d)?\b',text):
        v=m.replace(' ','')
        if v not in out: out.append(v)
    return out[:8]

def shard_name(pid):
    start=((pid-1)//500)*500+1
    return f'{start:05d}-{start+499:05d}.json'

def docs_for(p):
    mode=p['mode']
    if mode=='footwear':
        return {
          'items':[
            {'type':'declaration','label':'Декларация соответствия ЕАЭС по ТР ТС 017/2011','status':'для взрослой обуви'},
            {'type':'certificate','label':'Сертификат соответствия ЕАЭС по ТР ТС 007/2011','status':'для детской обуви'}],
          'refusalLetter':'Нет',
          'basis':'Готовая обувь требует обязательной оценки соответствия. Для взрослой продукции применяется ТР ТС 017/2011, для детской — ТР ТС 007/2011.'}, ['declaration','certificate'], ['tr-ts-017','tr-ts-007']
    if mode=='footwear_ppe':
        return {
          'items':[
            {'type':'declaration','label':'Декларация по ТР ТС 017/2011','status':'для взрослой обуви без защитного назначения СИЗ'},
            {'type':'certificate','label':'Сертификат по ТР ТС 007/2011','status':'для детской обуви'},
            {'type':'other','label':'Оценка соответствия по ТР ТС 019/2011','status':'при заявленных защитных свойствах СИЗ'}],
          'refusalLetter':'Нет',
          'basis':'Режим зависит от возраста и заявленных защитных свойств. Защитная рабочая/специальная обувь проверяется по ТР ТС 019/2011.'}, ['declaration','certificate'], ['tr-ts-017','tr-ts-007','tr-ts-019']
    if mode=='sports_equipment':
        return {
          'items':[], 'refusalLetter':'Возможно после уточнения',
          'basis':'Если изделие является комплектным спортивным инвентарем группы 9506, оно не должно автоматически классифицироваться как обувь группы 64. Обязательные документы требуют отдельной проверки по точному изделию и возрастному назначению.'}, ['unknown'], ['eec-tnved-95','pp-rf-2425']
    if mode=='shoe_part':
        return {'items':[],'refusalLetter':'Возможно после уточнения','basis':'Запчасть или комплектующая не является автоматически готовой обувью. Код и обязательные документы определяются по функции и материалу детали.'}, ['unknown'], ['cz-footwear-scope','tr-ts-017']
    if mode=='carnival_shoe':
        return {'items':[],'refusalLetter':'Возможно после уточнения','basis':'Настоящая многоразовая обувь группы 64 регулируется как обувь; отдельный праздничный реквизит может классифицироваться иначе.'}, ['unknown'], ['cz-footwear-scope','tr-ts-017']
    return {'items':[],'refusalLetter':'Возможно после уточнения','basis':'По названию нельзя подтвердить, является ли товар готовой обувью группы 64 или текстильным/спортивным аксессуаром другой группы.'}, ['unknown'], ['cz-footwear-scope','tr-ts-017','eec-tnved-95']

def mark_block(p):
    if p['mark']=='yes':
        return {'current':{'status':'yes','label':'Готовая обувь групп ТН ВЭД 6401–6405 подлежит обязательной маркировке'},'future':{'status':'no','label':'Отдельный будущий этап не требуется: обязательная маркировка уже действует'},'experiment':{'status':'no','label':'Эксперимент не является основанием вывода'}}
    if p['mark']=='no':
        return {'current':{'status':'no','label':'Для подтвержденного спортивного инвентаря группы 9506 обувная маркировка не применяется'},'future':{'status':'no','label':'Утвержденный будущий этап в рамках обувной маркировки не выявлен'},'experiment':{'status':'no'}}
    return {'current':{'status':'unknown','label':'Зависит от того, является ли изделие готовой обувью группы 64'},'future':{'status':'no','label':'Отдельный утвержденный будущий этап не выявлен'},'experiment':{'status':'no'}}

def detail(p,checked):
    docs,flags,src=docs_for(p)
    sources=[]
    for s in src+(['cz-footwear-scope','pp-rf-860-2019'] if p['mark']!='no' else []):
        if s not in sources: sources.append(s)
    return {
      'normalizedName':p['name'],
      'marking':mark_block(p),
      'tnved':{'candidates':[{'code':p['tn'],'confidence':p['confidence'],'description':'Точный 10-значный код определяется после уточнения материала, конструкции и назначения.'}], 'needsClarification':CLARIFY.get(p['profile'],['материал','конструкция','назначение'])},
      'documents':docs,
      'sourceIds':sources,
      'lastChecked':checked,
      'screeningReason':'Не соответствует стратегии простого входа: готовая обувь требует маркировки и обязательной оценки соответствия.' if p['mode'] not in YELLOW_MODES else 'Нужна дополнительная идентификация: товар может не являться готовой обувью группы 64.'
    },flags

def scenario_output(code,doc,result='red',mark='yes'):
    return {'tnvedCandidates':[{'code':code}], 'documents':{'status':'mandatory' if result=='red' else 'check','items':[{'label':doc}]}, 'marking':{'current':{'status':mark},'future':{'status':'no'},'experiment':{'status':'no'}}, 'result':result}

def standard_shoe_rule(p, ppe=False):
    q=['upperMaterial','waterproofFootwear','ageGroup']
    if ppe: q += ['protectivePPE','metalSafetyToe']
    sc=[]
    materials=[('Натуральная кожа','6403'),('Текстиль','6404'),('Иной/комбинированный','6405')]
    for age,doc in [('Взрослые','Декларация ЕАЭС по ТР ТС 017/2011'),('Дети','Сертификат ЕАЭС по ТР ТС 007/2011')]:
        sc.append({'label':f'Резина/пластмасса, водонепроницаемая, {age.lower()}','when':{'upperMaterial':{'eq':'Резина/пластмасса'},'waterproofFootwear':{'eq':'yes'},'ageGroup':{'eq':age}},'output':scenario_output('6401',doc)})
        sc.append({'label':f'Резина/пластмасса, прочая, {age.lower()}','when':{'upperMaterial':{'eq':'Резина/пластмасса'},'waterproofFootwear':{'eq':'no'},'ageGroup':{'eq':age}},'output':scenario_output('6402',doc)})
        for mat,code in materials:
            sc.append({'label':f'{mat}, {age.lower()}','when':{'upperMaterial':{'eq':mat},'ageGroup':{'eq':age}},'output':scenario_output(code,doc)})
    if ppe:
        sc.append({'label':'Защитная обувь / СИЗ','when':{'protectivePPE':{'eq':'yes'}},'output':scenario_output('6401–6405; подгруппа зависит от материала и конструкции','Оценка соответствия по ТР ТС 019/2011','red','yes')})
    return {'questionIds':q,'scenarios':sc}

def rule(p):
    pr=p['profile']
    if p['mode']=='footwear': return standard_shoe_rule(p)
    if p['mode']=='footwear_ppe': return standard_shoe_rule(p,True)
    if pr=='shoe_part':
        return {'questionIds':['finishedArticle','material','protectivePPE'], 'scenarios':[
          {'label':'Это именно запчасть/деталь','when':{'finishedArticle':{'eq':'no'}},'output':scenario_output('6406 либо код по материалу/функции','Требуется отдельная проверка обязательных требований','yellow','unknown')},
          {'label':'Фактически готовая мотообувь','when':{'finishedArticle':{'eq':'yes'}},'output':scenario_output('6401–6405','Обязательная оценка готовой обуви','red','yes')}]}
    if pr=='ice_skates':
        return {'questionIds':['completeSportsEquipment','ageGroup'], 'scenarios':[
          {'label':'Комплектные ледовые коньки','when':{'completeSportsEquipment':{'eq':'yes'}},'output':scenario_output('9506701000','Требуется отдельная проверка обязательных документов по спортивному инвентарю','yellow','no')},
          {'label':'Отдельный ботинок без прикрепленного конька','when':{'completeSportsEquipment':{'eq':'no'}},'output':scenario_output('6401–6405','Обязательная оценка обуви; точный документ зависит от возраста','red','yes')}]}
    if pr=='roller_skates':
        return {'questionIds':['completeSportsEquipment','ageGroup'], 'scenarios':[
          {'label':'Комплектные роликовые коньки','when':{'completeSportsEquipment':{'eq':'yes'}},'output':scenario_output('9506703000','Требуется отдельная проверка обязательных документов по спортивному инвентарю','yellow','no')},
          {'label':'Отдельный ботинок без роликов','when':{'completeSportsEquipment':{'eq':'no'}},'output':scenario_output('6401–6405','Обязательная оценка обуви; точный документ зависит от возраста','red','yes')}]}
    if pr=='fins':
        return {'questionIds':['completeSportsEquipment','ageGroup','toyPurpose'], 'scenarios':[
          {'label':'Плавательные ласты как спортивный инвентарь','when':{'completeSportsEquipment':{'eq':'yes'},'toyPurpose':{'eq':'no'}},'output':scenario_output('9506290000','Требуется отдельная проверка обязательных документов','yellow','no')},
          {'label':'Изделие предназначено как игрушка','when':{'toyPurpose':{'eq':'yes'}},'output':scenario_output('возможна группа 9503','Обязательная оценка по требованиям к игрушкам','red','no')}]}
    if pr=='carnival_shoe':
        return {'questionIds':['carnivalRequisite','integratedSole','upperMaterial'], 'scenarios':[
          {'label':'Настоящая многоразовая обувь','when':{'carnivalRequisite':{'eq':'no'},'integratedSole':{'eq':'yes'}},'output':scenario_output('6401–6405','Обязательная оценка обуви','red','yes')},
          {'label':'Только праздничный реквизит','when':{'carnivalRequisite':{'eq':'yes'}},'output':scenario_output('возможна группа 9505','Требуется отдельная классификация','yellow','no')}]}
    if pr in {'half_shoe','warmup_bootie'}:
        return {'questionIds':['integratedSole','finishedArticle','upperMaterial'], 'scenarios':[
          {'label':'Самостоятельная обувь с собственной подошвой','when':{'integratedSole':{'eq':'yes'},'finishedArticle':{'eq':'yes'}},'output':scenario_output('6401–6405','Обязательная оценка обуви','red','yes')},
          {'label':'Текстильный/спортивный аксессуар без собственной подошвы','when':{'integratedSole':{'eq':'no'}},'output':scenario_output('требуется классификация вне группы 64','Возможен менее регулируемый сценарий после уточнения','yellow','no')}]}
    return standard_shoe_rule(p)

def main():
    batch=load(SRC,{})
    products=batch.get('products',[]); checked=batch.get('checkedAt','2026-08-27')
    summary=load(DATA/'compliance-summary.json',{})
    detail_files={}; rule_files={}
    for p in products:
        shard=shard_name(p['id'])
        if shard not in detail_files: detail_files[shard]=load(DATA/'compliance/details'/shard,{})
        if shard not in rule_files: rule_files[shard]=load(DATA/'rules/products'/shard,{})
        d,flags=detail(p,checked)
        result='yellow' if p['mode'] in YELLOW_MODES else 'red'
        summary[str(p['id'])]={'result':result,'markingCurrent':p['mark'],'markingFuture':'no','experiment':'no','documentFlags':flags,'tnvedCodes':codes(p['tn']),'lastChecked':checked}
        detail_files[shard][str(p['id'])]=d
        rule_files[shard][str(p['id'])]=rule(p)
    write(DATA/'compliance-summary.json',summary)
    for name,obj in detail_files.items(): write(DATA/'compliance/details'/name,obj)
    for name,obj in rule_files.items(): write(DATA/'rules/products'/name,obj)
    meta=load(DATA/'meta.json',{})
    stats={'green':0,'yellow':0,'red':0}
    for s in summary.values():
        if s.get('result') in stats: stats[s['result']]+=1
    meta['complianceStatus']='partial'; meta['checkedProducts']=len(summary); meta['screeningStats']=stats; meta['lastComplianceBuild']=checked
    (DATA/'meta.json').write_text(json.dumps(meta,ensure_ascii=False,indent=2),encoding='utf-8')
    print(f"Merged {len(products)} footwear products; total {len(summary)}; stats {stats}")

if __name__=='__main__': main()
