#!/usr/bin/env python3
import json,re
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]; DATA=ROOT/'data'; SRC=ROOT/'data-src'/'stationery-01.json'

def load(p,d): return json.loads(p.read_text(encoding='utf-8')) if p.exists() else d
def write(p,o): p.parent.mkdir(parents=True,exist_ok=True); p.write_text(json.dumps(o,ensure_ascii=False,separators=(',',':')),encoding='utf-8')
def shard(pid):
 s=((pid-1)//500)*500+1; return f'{s:05d}-{s+499:05d}.json'
def codes(t):
 out=[]
 for m in re.findall(r'\b\d{4}(?:\s?\d{2})?(?:\s?\d{3})?(?:\s?\d)?\b',t):
  v=m.replace(' ','')
  if v not in out: out.append(v)
 return out[:8]

def patch_registry():
 attrs=load(DATA/'rules/attributes.json',{'version':1,'definitions':{}})
 attrs['version']=max(int(attrs.get('version',1)),7)
 attrs.setdefault('definitions',{})['declaredForChildren']={"label":"Изготовитель заявляет товар как предназначенный для детей/подростков","type":"boolean"}
 write(DATA/'rules/attributes.json',attrs)
 sources=load(DATA/'sources.json',{'version':1,'sources':{}}); sources['version']=max(int(sources.get('version',1)),5); s=sources.setdefault('sources',{})
 s['eec-stationery-scope']={"title":"Справка о нераспространении ТР ТС 007/2011 на канцелярские товары, не заявленные для детей и подростков","authority":"Евразийская экономическая комиссия","url":"https://eec.eaeunion.org/upload/medialibrary/625/Spravka-po-kants.-tovaram.pdf"}
 s['cz-household-chemicals-stages']={"title":"Сроки и этапы маркировки косметики, бытовой химии и товаров личной гигиены","authority":"Честный знак / ЦРПТ","url":"https://markirovka.ru/knowledge/tovarnye-gruppy/kosmetika-bytovaya-himiya/sroki-i-etapy-markirovki-kosmeticheskoy-produktsii-bytovoy-khimii-i-tovarov-lichnoy-gigieny"}
 write(DATA/'sources.json',sources)

def doc_none(): return {'items':[],'refusalLetter':'Да, высокая вероятность','basis':'Для канцелярского товара общего/офисного назначения, не заявленного изготовителем для детей и подростков, ЕЭК указывала на отсутствие обязательных требований в рамках технических регламентов ТС. Дополнительно проверен национальный перечень ПП РФ № 2425.'}
def mark_no(): return {'current':{'status':'no','label':'Обязательная маркировка для этой канцелярской позиции по выявленному сценарию не обнаружена'},'future':{'status':'no','label':'Утверждённый будущий этап обязательной маркировки не обнаружен'},'experiment':{'status':'no','label':'Релевантный эксперимент не обнаружен'}}
def doc_child(): return {'items':[{'type':'declaration','label':'Декларация соответствия ЕАЭС по ТР ТС 007/2011','status':'обязательна для школьно-письменной принадлежности, заявленной для детей/подростков'}],'refusalLetter':'Нет','basis':'ТР ТС 007/2011 распространяется на школьно-письменные принадлежности, заявленные изготовителем как предназначенные для детей и подростков.'}
def doc_electronic(): return {'items':[{'type':'declaration','label':'Декларация/иная обязательная оценка по ТР ТС 020/2011','status':'применимость зависит от исполнения электронного устройства'},{'type':'other','label':'Дополнительно проверить ТР ЕАЭС 037/2016','status':'для изделий электротехники и радиоэлектроники'}],'refusalLetter':'Нет либо только после исключения электротехнических регламентов','basis':'Электронное исполнение переводит товар из простой канцелярии в область технического регулирования электроники.'}

def detail(p,checked):
 prof=p['profile']; sources=['pp-rf-2425']; flags=[]
 if prof=='office_simple': docs=doc_none(); flags=['none','refusal']; sources=['eec-stationery-scope','pp-rf-2425']; reason='Низкая регуляторная нагрузка при общем/офисном назначении.'
 elif prof=='school_child': docs=doc_child(); flags=['declaration']; sources=['tr-ts-007']; reason='Школьная принадлежность для детей требует обязательной оценки соответствия.'
 elif prof in ('child_dependent','chemical_child_dependent'): docs={'items':[],'refusalLetter':'Возможно после уточнения','basis':'Ключевой признак — заявлено ли изделие изготовителем как предназначенное для детей/подростков. Для химических/художественных материалов дополнительно важен состав и фактическое назначение.'}; flags=['unknown']; sources=['eec-stationery-scope','tr-ts-007','pp-rf-2425']; reason='После уточнения назначения возможен как простой, так и регулируемый сценарий.'
 elif prof=='electronic': docs=doc_electronic(); flags=['declaration']; sources=['tr-ts-020']; reason='Электронное устройство требует отдельной обязательной оценки.'
 elif prof=='electronic_ambiguous': docs={'items':[],'refusalLetter':'Возможно после уточнения','basis':'Если карта/браслет пассивные — возможен простой сценарий; электронная/RFID-версия требует проверки технических регламентов.'}; flags=['unknown']; sources=['tr-ts-020','pp-rf-2425']; reason='Статус зависит от наличия электроники/RFID.'
 else: docs={'items':[],'refusalLetter':'Возможно после уточнения','basis':'Необходимо исключить медицинское назначение и определить принцип работы.'}; flags=['unknown']; sources=['pp-rf-2425']; reason='Недостаточно данных для простой классификации.'
 needs=['материал','конструкция/функция для точного 10-значного ТН ВЭД']
 if prof in ('child_dependent','chemical_child_dependent','school_child'): needs.insert(0,'заявлено ли изготовителем назначение для детей/подростков')
 if prof=='chemical_child_dependent': needs += ['состав/основа материала','не является ли товар бытовой химией иной товарной группы']
 if prof=='electronic_ambiguous': needs=['есть ли электронная микросхема/RFID','источник питания','назначение']
 if prof=='assistive_ambiguous': needs=['принцип работы','медицинское/реабилитационное назначение','материал/конструкция']
 return {'normalizedName':p['name'],'marking':mark_no(),'tnved':{'candidates':[{'code':p['tn'],'confidence':'средний' if '/' not in p['tn'] else 'низкий','description':'Код указан как первичный сценарий; 10 знаков фиксируются после характеристик.'}],'needsClarification':needs},'documents':docs,'sourceIds':sources,'lastChecked':checked,'screeningReason':reason},flags

def scenario(code,docs,result,mark='no'):
 return {'tnvedCandidates':[{'code':code}],'documents':{'status':'none' if result=='green' else 'mandatory' if result=='red' else 'check','items':docs},'marking':{'current':{'status':mark},'future':{'status':'no'},'experiment':{'status':'no'}},'result':result}
def rules(p):
 prof=p['profile']; code=p['tn']
 if prof=='office_simple': return {'questionIds':['declaredForChildren'], 'scenarios':[{'label':'Общее/офисное назначение','when':{'declaredForChildren':{'eq':'no'}},'output':scenario(code,[],'green')},{'label':'Изготовитель заявляет детское/подростковое назначение','when':{'declaredForChildren':{'eq':'yes'}},'output':scenario(code,[{'label':'Декларация по ТР ТС 007/2011'}],'red')}]}
 if prof=='child_dependent': return {'questionIds':['declaredForChildren'], 'scenarios':[{'label':'Не заявлено для детей/подростков','when':{'declaredForChildren':{'eq':'no'}},'output':scenario(code,[],'green')},{'label':'Заявлено для детей/подростков','when':{'declaredForChildren':{'eq':'yes'}},'output':scenario(code,[{'label':'Декларация по ТР ТС 007/2011'}],'red')}]}
 if prof=='chemical_child_dependent': return {'questionIds':['declaredForChildren','householdChemical'], 'scenarios':[{'label':'Обычный канцелярский/художественный материал для общего использования','when':{'declaredForChildren':{'eq':'no'},'householdChemical':{'eq':'no'}},'output':scenario(code,[],'green')},{'label':'Материал заявлен для детей/подростков','when':{'declaredForChildren':{'eq':'yes'}},'output':scenario(code,[{'label':'Декларация по ТР ТС 007/2011'}],'red')},{'label':'Фактически относится к бытовой химии','when':{'householdChemical':{'eq':'yes'}},'output':scenario(code,[{'label':'Требуется проверка точного ТН ВЭД/ОКПД2 и маркировки бытовой химии'}],'red','unknown')}]}
 if prof=='school_child': return {'questionIds':[],'scenarios':[]}
 if prof=='electronic': return {'questionIds':['batteryPowered','mainsPowered'], 'scenarios':[{'label':'Электронный калькулятор','when':{},'output':scenario(code,[{'label':'Проверка/декларация по ТР ТС 020/2011 и применимым требованиям электроники'}],'red','no')}]}
 if prof=='electronic_ambiguous': return {'questionIds':['electric','radioWireless'], 'scenarios':[{'label':'Пассивная карта/браслет без электроники','when':{'electric':{'eq':'no'}},'output':scenario('3926 / иной код по материалу',[],'green')},{'label':'Электронная/RFID-карта или браслет','when':{'electric':{'eq':'yes'}},'output':scenario('8523 / иной электронный код',[{'label':'Обязательная проверка ТР ТС 020/2011 и иных требований электроники'}],'red','no')}]}
 if prof=='assistive_ambiguous': return {'questionIds':['medicalPurpose','electric'], 'scenarios':[{'label':'Немедицинский механический прибор','when':{'medicalPurpose':{'eq':'no'},'electric':{'eq':'no'}},'output':scenario(code,[{'label':'Требуется отдельная проверка по ПП РФ № 2425'}],'yellow')},{'label':'Медицинское назначение','when':{'medicalPurpose':{'eq':'yes'}},'output':scenario(code,[{'label':'Проверка государственной регистрации медицинского изделия'}],'red')}]}
 return {'questionIds':[],'scenarios':[]}

def main():
 patch_registry(); batch=load(SRC,{}); products=batch.get('products',[]); checked=batch.get('checkedAt','2026-08-27'); summary=load(DATA/'compliance-summary.json',{}); dfs={}; rfs={}
 for p in products:
  sh=shard(p['id']); dfs.setdefault(sh,load(DATA/'compliance/details'/sh,{})); rfs.setdefault(sh,load(DATA/'rules/products'/sh,{})); d,flags=detail(p,checked); summary[str(p['id'])]={'result':p['result'],'markingCurrent':'no','markingFuture':'no','experiment':'no','documentFlags':flags,'tnvedCodes':codes(p['tn']),'lastChecked':checked}; dfs[sh][str(p['id'])]=d; rfs[sh][str(p['id'])]=rules(p)
 write(DATA/'compliance-summary.json',summary)
 for n,o in dfs.items(): write(DATA/'compliance/details'/n,o)
 for n,o in rfs.items(): write(DATA/'rules/products'/n,o)
 meta=load(DATA/'meta.json',{}); stats={'green':0,'yellow':0,'red':0}
 for s in summary.values():
  if s.get('result') in stats: stats[s['result']]+=1
 meta['complianceStatus']='partial'; meta['checkedProducts']=len(summary); meta['screeningStats']=stats; meta['lastComplianceBuild']=checked; write(DATA/'meta.json',meta)
 print(f"Merged {len(products)} stationery products; total {len(summary)}; stats {stats}")
if __name__=='__main__': main()
