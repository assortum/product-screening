#!/usr/bin/env python3
import json,re
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]; DATA=ROOT/'data'; SRC=ROOT/'data-src'/'books-01.json'

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
 attrs=load(DATA/'rules/attributes.json',{'version':1,'definitions':{}}); attrs['version']=max(int(attrs.get('version',1)),10); d=attrs.setdefault('definitions',{})
 d['publicationAge']={"label":"Возраст конкретного печатного экземпляра","type":"single","options":["Не более 100 лет","Старше 100 лет","Не указано"]}
 d['physicalMediaType']={"label":"Тип физического носителя аудиокниги","type":"single","options":["Оптический диск CD/DVD","Полупроводниковый/USB-носитель","Магнитный носитель","Иной/не указано"]}
 write(DATA/'rules/attributes.json',attrs)
 sources=load(DATA/'sources.json',{'version':1,'sources':{}}); sources['version']=max(int(sources.get('version',1)),8); s=sources.setdefault('sources',{})
 s['eec-tnved-49']={"title":"Группа 49 ТН ВЭД ЕАЭС — печатные книги, газеты и другая полиграфическая продукция","authority":"Евразийская экономическая комиссия","url":"https://eec.eaeunion.org/comission/department/catr/ett/ru.2022/ru.49_2022_08.03.2026.pdf"}
 s['eec-tnved-49-notes']={"title":"Пояснения к группе 49 ТН ВЭД ЕАЭС","authority":"Евразийская экономическая комиссия","url":"https://eec.eaeunion.org/upload/files/catr/psn/psn49.pdf"}
 s['rospotreb-age-books']={"title":"О возрастной маркировке книг","authority":"Роспотребнадзор","url":"https://zpp.rospotrebnadzor.ru/news/federal/574527"}
 s['cz-radioelectronics-scope']={"title":"Какие товары подлежат обязательной маркировке? Радиоэлектроника","authority":"Честный знак / ЦРПТ","url":"https://markirovka.ru/knowledge/tovarnye-gruppy/radioelektronika/kakie-tovary-podlezhat-obyazatelnoy-markirovke-radioelektronika"}
 write(DATA/'sources.json',sources)

def simple_docs(info=True):
 basis='Обязательная сертификация/декларирование по ПП РФ № 2425 для данного вида печатной информационной продукции не выявлены.'
 if info: basis += ' При этом книжная/информационная продукция должна учитывать требования 436-ФЗ к возрастной классификации и знаку информационной продукции.'
 return {'items':[],'refusalLetter':'Не требуется / обязательное подтверждение соответствия предположительно отсутствует','basis':basis}
def mark_no(label='Обязательная маркировка Честный знак не обнаружена'): return {'current':{'status':'no','label':label},'future':{'status':'no','label':'Утвержденный будущий этап Честного знака не обнаружен'},'experiment':{'status':'no'}}
def detail(p,checked):
 prof=p['profile']; src=['pp-rf-2425']; flags=['none']; needs=[]; m=mark_no(); docs=simple_docs(); reason='Низкая регуляторная нагрузка; Честный знак и обязательная оценка соответствия не выявлены.'
 if prof=='printed_book': src=['eec-tnved-49','eec-tnved-49-notes','rospotreb-age-books','pp-rf-2425']; needs=['вид печатного издания для уточнения 10-значного кода'];
 elif prof=='printed_periodical': src=['eec-tnved-49','eec-tnved-49-notes','rospotreb-age-books','pp-rf-2425']; needs=['периодичность выпуска и формат/переплет для точной классификации'];
 elif prof=='antique_print':
  src=['eec-tnved-49','eec-tnved-49-notes','rospotreb-age-books','pp-rf-2425']; needs=['точный год выпуска конкретного экземпляра','старше ли экземпляр 100 лет']; docs={'items':[],'refusalLetter':'Возможно после уточнения','basis':'До установления точного года нельзя выбрать между обычной печатной продукцией группы 49 и антиквариатом группы 97. Обязательный сертификат/декларация по базовым перечням не выявлены, но для старых культурных ценностей могут действовать отдельные правила оборота/вывоза.'}; flags=['unknown']; reason='Регуляторная нагрузка невысокая, но ТН ВЭД и возможный режим культурной ценности зависят от возраста конкретного экземпляра.'
 elif prof=='physical_audio':
  src=['cz-radioelectronics-scope','rospotreb-age-books','pp-rf-2425']; needs=['тип физического носителя: CD/DVD, USB/flash, магнитный или иной','записанный или незаписанный носитель']; docs=simple_docs(); m=mark_no('Для записанного носителя группы 8523 отдельная обязательная маркировка в проверенном перечне радиоэлектроники не выявлена; окончательно сверить тип носителя'); reason='Физический носитель требует уточнения подгруппы 8523, но существенная регуляторная нагрузка по текущим данным не выявлена.'
 elif prof=='digital_nonphysical':
  src=['rospotreb-age-books']; docs={'items':[],'refusalLetter':'Не применимо','basis':'Цифровой контент/цифровой сертификат не является физическим импортируемым товаром для целей ТН ВЭД. Требования к информационной продукции и цифровой торговле рассматриваются отдельно от товарной сертификации.'}; flags=['none']; needs=['подтверждение, что покупателю передается только цифровой контент/право без физического носителя']; reason='Нематериальный продукт: физическая товарная сертификация и ТН ВЭД не применяются.'
 return {'normalizedName':p['name'],'marking':m,'tnved':{'candidates':[{'code':p['tn'],'confidence':'высокий' if p['tn'] in ('4901','4902') else 'средний','description':'Точный сценарий указан по имеющимся данным.'}],'needsClarification':needs},'documents':docs,'sourceIds':src,'lastChecked':checked,'screeningReason':reason},flags

def sc(code,result='green',items=None):
 return {'tnvedCandidates':[{'code':code}],'documents':{'status':'none' if result=='green' else 'check','items':items or []},'marking':{'current':{'status':'no'},'future':{'status':'no'},'experiment':{'status':'no'}},'result':result}
def rule(p):
 prof=p['profile']; code=p['tn']
 if prof=='antique_print':
  base='4901' if p['name']=='Печатная книга' else '4902'
  return {'questionIds':['publicationAge'],'scenarios':[{'label':'Экземпляр не старше 100 лет','when':{'publicationAge':{'eq':'Не более 100 лет'}},'output':sc(base,'green')},{'label':'Экземпляр старше 100 лет','when':{'publicationAge':{'eq':'Старше 100 лет'}},'output':sc('9706',[{'label':'Дополнительно проверить режим культурных ценностей/антиквариата'}],'yellow')}]}
 if prof=='physical_audio':
  return {'questionIds':['physicalMediaType'],'scenarios':[{'label':'Записанный оптический диск','when':{'physicalMediaType':{'eq':'Оптический диск CD/DVD'}},'output':sc('852349')},{'label':'Полупроводниковый/USB-носитель','when':{'physicalMediaType':{'eq':'Полупроводниковый/USB-носитель'}},'output':sc('852351 / иной код 8523 после уточнения')},{'label':'Магнитный носитель','when':{'physicalMediaType':{'eq':'Магнитный носитель'}},'output':sc('852329')}]}
 return {'questionIds':[],'scenarios':[]}

def main():
 patch_registry(); b=load(SRC,{}); products=b.get('products',[]); checked=b.get('checkedAt','2026-08-27'); summary=load(DATA/'compliance-summary.json',{}); dfs={}; rfs={}
 for p in products:
  sh=shard(p['id']); dfs.setdefault(sh,load(DATA/'compliance/details'/sh,{})); rfs.setdefault(sh,load(DATA/'rules/products'/sh,{})); d,flags=detail(p,checked); summary[str(p['id'])]={'result':p['result'],'markingCurrent':d['marking']['current']['status'],'markingFuture':'no','experiment':'no','documentFlags':flags,'tnvedCodes':codes(p['tn']),'lastChecked':checked}; dfs[sh][str(p['id'])]=d; rfs[sh][str(p['id'])]=rule(p)
 write(DATA/'compliance-summary.json',summary)
 for n,o in dfs.items(): write(DATA/'compliance/details'/n,o)
 for n,o in rfs.items(): write(DATA/'rules/products'/n,o)
 meta=load(DATA/'meta.json',{}); stats={'green':0,'yellow':0,'red':0}
 for s in summary.values():
  if s.get('result') in stats: stats[s['result']]+=1
 meta['complianceStatus']='partial'; meta['checkedProducts']=len(summary); meta['screeningStats']=stats; meta['lastComplianceBuild']=checked; write(DATA/'meta.json',meta)
 print(f"Merged {len(products)} book products; total {len(summary)}; stats {stats}")
if __name__=='__main__': main()
