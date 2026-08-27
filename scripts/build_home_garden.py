#!/usr/bin/env python3
import json,re
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]; DATA=ROOT/'data'; SRC=ROOT/'data-src'/'home-garden-01.json'

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
 attrs=load(DATA/'rules/attributes.json',{'version':1,'definitions':{}}); attrs['version']=max(int(attrs.get('version',1)),9); d=attrs.setdefault('definitions',{})
 d['pressureOver005']={"label":"Максимальное рабочее давление превышает 0,05 МПа","type":"boolean"}
 d['agrochemicalRegistered']={"label":"Продукт зарегистрирован как пестицид/агрохимикат в установленном порядке","type":"boolean"}
 d['fuelOrElectric']={"label":"Источник работы/нагрева","type":"single","options":["Без энергии / механический","Электрический","Газ/жидкое/твердое топливо","Не указано"]}
 write(DATA/'rules/attributes.json',attrs)
 sources=load(DATA/'sources.json',{'version':1,'sources':{}}); sources['version']=max(int(sources.get('version',1)),7); s=sources.setdefault('sources',{})
 s['cz-homeware-experiment']={"title":"Эксперимент по маркировке товаров для дома и интерьера","authority":"Честный знак / ЦРПТ","url":"https://markirovka.ru/knowledge/tovarnyegruppy/obschie-voprosy-gis/eksperiment-po-markirovke-otdelnykh-vidov-tovarov-dlya-doma-i-interera"}
 s['pp-rf-1458-2025']={"title":"Постановление Правительства РФ от 20.09.2025 № 1458","authority":"Правительство Российской Федерации","url":"https://government.ru/docs/all/161041/"}
 s['cz-cosmetics-household-stages']={"title":"Сроки и этапы маркировки косметической продукции, бытовой химии и товаров личной гигиены","authority":"Честный знак / ЦРПТ","url":"https://markirovka.ru/knowledge/tovarnye-gruppy/kosmetika-bytovaya-himiya/sroki-i-etapy-markirovki-kosmeticheskoy-produktsii-bytovoy-khimii-i-tovarov-lichnoy-gigieny"}
 s['tr-ts-010']={"title":"ТР ТС 010/2011 «О безопасности машин и оборудования»","authority":"Евразийская экономическая комиссия","url":"https://eec.eaeunion.org/upload/medialibrary/203/P_823_1.pdf"}
 s['tr-ts-025']={"title":"ТР ТС 025/2012 «О безопасности мебельной продукции»","authority":"Евразийская экономическая комиссия","url":"https://eec.eaeunion.org/upload/medialibrary/f2f/RS_P_32.pdf"}
 s['tr-ts-006']={"title":"ТР ТС 006/2011 «О безопасности пиротехнических изделий»","authority":"Евразийская экономическая комиссия","url":"https://eec.eaeunion.org/upload/medialibrary/399/TR-TS-Pirotechnika.pdf"}
 s['fz-109-agrochem']={"title":"Федеральный закон № 109-ФЗ «О безопасном обращении с пестицидами и агрохимикатами», ст. 8","authority":"Нормативное основание государственной регистрации пестицидов и агрохимикатов","url":"https://www.consultant.ru/document/cons_doc_LAW_15221/906669d8e8e315bc7d229a2c9458d3bc5b27e4d9/"}
 write(DATA/'sources.json',sources)

EXP_TOKENS=('3924','4419','4806','481830','482361','482369','6911','6912','7013','7323','7418','7615','8215','9617','630710','960310','960390','9604','3406','392640','4414','4420','442110','4602','6702','681099','6913','7009','8306','9105','940550')
def exp_possible(p):
 compact=re.sub(r'\s+','',p.get('tn',''))
 return p['profile'] in {'food_contact_experiment','decor_experiment','homeware_experiment'} and any(x in compact for x in EXP_TOKENS)
def mark_no(): return {'current':{'status':'no','label':'Обязательная маркировка по выявленному сценарию не обнаружена'},'future':{'status':'no','label':'Утвержденный будущий этап не обнаружен'},'experiment':{'status':'no'}}
def marking_for(p):
 prof=p['profile']
 if prof=='home_fragrance': return {'current':{'status':'yes','label':'Возможна действующая маркировка бытовой химии по ТН ВЭД 3307 при совпадении ОКПД2; для диффузоров/ароматизаторов требуется точная проверка кода'},'future':{'status':'no'},'experiment':{'status':'no'}}
 if exp_possible(p): return {'current':{'status':'no','label':'Обязательная маркировка пока не установлена'},'future':{'status':'no','label':'На 27.08.2026 опубликованного обязательного этапа после эксперимента не выявлено'},'experiment':{'status':'yes','label':'Предположительно входит в добровольный эксперимент товаров для дома при подтверждении указанного кода ТН ВЭД','date':'01.10.2025–31.08.2026'}}
 if prof in {'food_contact_experiment','decor_experiment','homeware_experiment'}: return {'current':{'status':'no'},'future':{'status':'no'},'experiment':{'status':'unknown','label':'Проверить точный 10-значный ТН ВЭД: часть близких товаров находится в эксперименте до 31.08.2026'}}
 if prof=='textile_regulated': return {'current':{'status':'unknown','label':'Текстильное изделие: проверить точный код относительно действующей маркировки легкой промышленности'},'future':{'status':'no'},'experiment':{'status':'no'}}
 return mark_no()

def detail(p,checked):
 prof=p['profile']; result=p['result']; m=marking_for(p); src=['pp-rf-2425']; flags=[]; needs=['материал','конструкция/назначение для точного 10-значного ТН ВЭД']
 if prof=='simple_home':
  docs={'items':[],'refusalLetter':'Да, высокая вероятность','basis':'Для простого неэлектрического изделия общего хозяйственного/садового назначения обязательное подтверждение по проверенным базовым перечням предположительно отсутствует. Перед закупкой фиксируется точный ТН ВЭД и проверяется ПП РФ № 2425.'}; flags=['none','refusal']; reason='Низкая регуляторная нагрузка при подтверждении простой конструкции и назначения.'
 elif prof in {'food_contact_experiment','homeware_experiment'}:
  docs={'items':[],'refusalLetter':'Возможно после уточнения','basis':'Материал, назначение и контакт с пищей могут менять обязательные санитарные/национальные требования. Отдельно проверяется эксперимент по товарам для дома; сам эксперимент не является обязательной маркировкой.'}; flags=['unknown']; src=['cz-homeware-experiment','pp-rf-1458-2025','pp-rf-2425']; needs=['основной материал','контакт с пищей','точный ТН ВЭД']; reason='Пилот ЧЗ и/или материал/пищевой контакт требуют уточнения, но обязательная маркировка по эксперименту ещё не установлена.'
 elif prof=='decor_experiment':
  docs={'items':[],'refusalLetter':'Возможно после уточнения','basis':'Для обычного декора обязательное подтверждение часто отсутствует, но часть кодов декора включена в добровольный эксперимент маркировки до 31.08.2026. Нужен точный материал и ТН ВЭД.'}; flags=['unknown']; src=['cz-homeware-experiment','pp-rf-1458-2025','pp-rf-2425']; needs=['материал','является ли изделие декором/предметом интерьера','точный ТН ВЭД']; reason='Регуляторный риск повышен из-за экспериментальной товарной группы.'
 elif prof=='home_fragrance':
  docs={'items':[{'type':'other','label':'Проверка разрешительного документа по фактическому составу/назначению','status':'не определяется только названием'}],'refusalLetter':'Нет до уточнения','basis':'Средства для ароматизации помещений могут классифицироваться в 3307. Для части товаров 3307 при соответствующем ОКПД2 действует обязательная маркировка с 2025 года.'}; flags=['other']; src=['cz-cosmetics-household-stages']; needs=['состав','форма товара','ТН ВЭД','ОКПД2']; reason='Возможна действующая маркировка бытовой химии; требуется разрешительная идентификация.'
 elif prof=='electric_or_machine':
  docs={'items':[{'type':'declaration','label':'Оценка соответствия по ТР ТС 010/2011','status':'для машин/оборудования при попадании в область действия'},{'type':'declaration','label':'Проверка ТР ТС 004/2011 и 020/2011','status':'для электрического исполнения; зависит от параметров'},{'type':'other','label':'ТР ЕАЭС 037/2016','status':'для электротехники/радиоэлектроники при применимости'}],'refusalLetter':'Нет либо только после исключения регламентов','basis':'Садовое/электрическое оборудование требует идентификации по типу машины, приводу, напряжению и электрическим функциям.'}; flags=['declaration']; src=['tr-ts-010','tr-ts-004','tr-ts-020']; needs=['электрическое или механическое исполнение','напряжение','тип привода','точное назначение']; reason='Машины/электрооборудование имеют обязательные технические требования.'
 elif prof=='equipment_ambiguous':
  docs={'items':[],'refusalLetter':'Возможно после уточнения','basis':'Название может обозначать как простую механическую деталь, так и регулируемое оборудование/электрическую часть. Форма подтверждения определяется после идентификации.'}; flags=['unknown']; src=['tr-ts-010','tr-ts-004','tr-ts-020','pp-rf-2425']; needs=['самостоятельное изделие или запчасть','электрические функции','рабочие параметры','материал']; reason='Нужна техническая идентификация.'
 elif prof=='agrochemical':
  docs={'items':[{'type':'other','label':'Государственная регистрация пестицида/агрохимиката','status':'обязательна при юридической идентификации как пестицид/агрохимикат'}],'refusalLetter':'Нет','basis':'Статья 8 Федерального закона № 109-ФЗ предусматривает государственную регистрацию пестицидов и агрохимикатов с внесением сведений в реестр.'}; flags=['other']; src=['fz-109-agrochem']; needs=['состав','назначение','является ли продукт пестицидом/агрохимикатом','регистрационная запись']; reason='Специальный регистрационный режим делает вход сложным.'
 elif prof=='pyrotechnics':
  docs={'items':[{'type':'certificate','label':'Обязательное подтверждение по ТР ТС 006/2011','status':'форма зависит от класса пиротехнического изделия'}],'refusalLetter':'Нет','basis':'Пиротехнические изделия регулируются ТР ТС 006/2011.'}; flags=['certificate']; src=['tr-ts-006']; needs=['класс пиротехнического изделия','назначение и состав']; reason='Пиротехническая продукция имеет обязательную оценку соответствия.'
 elif prof=='furniture':
  docs={'items':[{'type':'declaration','label':'Декларация соответствия по ТР ТС 025/2012','status':'для соответствующей мебельной продукции'}],'refusalLetter':'Нет','basis':'Мебельная продукция является объектом ТР ТС 025/2012.'}; flags=['declaration']; src=['tr-ts-025']; needs=['является ли изделие мебелью','назначение и конструкция']; reason='Обязательная оценка мебели.'
 elif prof=='textile_regulated':
  docs={'items':[{'type':'declaration','label':'Обязательная оценка по ТР ТС 017/2011','status':'форма зависит от точной классификации текстильного изделия'}],'refusalLetter':'Нет','basis':'Текстильное готовое изделие необходимо проверять по ТР ТС 017/2011; дополнительно — действующую маркировку легкой промышленности по точному коду.'}; flags=['declaration']; src=['tr-ts-017','cz-legprom-scope']; needs=['вид текстильного изделия','состав','конструкция','ТН ВЭД']; reason='Текстильная продукция имеет существенную регуляторную нагрузку.'
 elif prof=='composition_ambiguous':
  docs={'items':[],'refusalLetter':'Возможно после уточнения','basis':'Состав и назначение определяют товарную позицию и возможные санитарные/химические требования.'}; flags=['unknown']; src=['pp-rf-2425']; needs=['полный состав','назначение','форма/материал']; reason='Необходим состав.'
 else: # purpose_ambiguous
  docs={'items':[],'refusalLetter':'Возможно после уточнения','basis':'Юридический режим зависит от назначения: декоративное изделие, игрушка, текстильный аксессуар или живой растительный товар.'}; flags=['unknown']; src=['tr-ts-008','cz-toys-scope','cz-homeware-experiment','pp-rf-2425']; needs=['фактическое назначение','детское/игровое назначение','живой или искусственный материал','ТН ВЭД']; reason='Назначение может переключить товар между несколькими регулируемыми группами.'
 return {'normalizedName':p['name'],'marking':m,'tnved':{'candidates':[{'code':p['tn'],'confidence':'низкий' if '/' in p['tn'] or 'требуется' in p['tn'] else 'средний','description':'Предварительный сценарий; точный 10-значный код определяется после характеристик.'}],'needsClarification':needs},'documents':docs,'sourceIds':src,'lastChecked':checked,'screeningReason':reason},flags

def sc(code,items,result,cur='no',exp='no'):
 return {'tnvedCandidates':[{'code':code}],'documents':{'status':'none' if result=='green' else 'mandatory' if result=='red' else 'check','items':items},'marking':{'current':{'status':cur},'future':{'status':'no'},'experiment':{'status':exp}},'result':result}
def rule(p):
 prof=p['profile']; code=p['tn']
 if prof=='simple_home': return {'questionIds':['electric','toyPurpose'], 'scenarios':[{'label':'Простое неэлектрическое изделие общего назначения','when':{'electric':{'eq':'no'},'toyPurpose':{'eq':'no'}},'output':sc(code,[],'green')},{'label':'Есть электрические функции','when':{'electric':{'eq':'yes'}},'output':sc(code,[{'label':'Проверка технических регламентов электрооборудования'}],'red','unknown')},{'label':'Заявлено как игрушка','when':{'toyPurpose':{'eq':'yes'}},'output':sc('возможна 9503',[{'label':'Сертификат ТР ТС 008/2011 и проверка ЧЗ игрушек'}],'red','yes')}]}
 if prof in {'food_contact_experiment','homeware_experiment'}: return {'questionIds':['material','foodContact'], 'scenarios':[{'label':'Материал/конструкция требуют уточнения','when':{},'output':sc(code,[{'label':'Проверить обязательный документ по материалу и ПП РФ № 2425; отдельно пилот товаров для дома'}],'yellow','no','yes' if exp_possible(p) else 'unknown')}]}
 if prof=='decor_experiment': return {'questionIds':['material'], 'scenarios':[{'label':'Декоративное изделие','when':{},'output':sc(code,[{'label':'Часто возможен отказной сценарий после точного кода; проверить эксперимент товаров для дома'}],'yellow','no','yes' if exp_possible(p) else 'unknown')}]}
 if prof=='home_fragrance': return {'questionIds':['householdChemical'], 'scenarios':[{'label':'Средство ароматизации помещений / бытовая химия','when':{'householdChemical':{'eq':'yes'}},'output':sc(code,[{'label':'Проверить ТН ВЭД + ОКПД2; возможна действующая маркировка по группе 3307'}],'red','yes')},{'label':'Не относится к бытовой химии','when':{'householdChemical':{'eq':'no'}},'output':sc(code,[{'label':'Требуется повторная классификация по составу'}],'yellow','unknown')}]}
 if prof=='electric_or_machine': return {'questionIds':['fuelOrElectric','ratedVoltage'], 'scenarios':[{'label':'Электрическая машина/оборудование','when':{'fuelOrElectric':{'eq':'Электрический'}},'output':sc(code,[{'label':'ТР ТС 010/2011 + применимые электротехнические регламенты'}],'red','unknown')},{'label':'Механическое исполнение','when':{'fuelOrElectric':{'eq':'Без энергии / механический'}},'output':sc(code,[{'label':'Проверить ТР ТС 010/2011 по конкретному виду машины'}],'yellow','no')}]}
 if prof=='equipment_ambiguous': return {'questionIds':['finishedArticle','electric','pressureOver005'], 'scenarios':[{'label':'Простая неэлектрическая комплектующая','when':{'finishedArticle':{'eq':'no'},'electric':{'eq':'no'},'pressureOver005':{'eq':'no'}},'output':sc(code,[{'label':'Возможен простой сценарий после точной классификации детали'}],'yellow','no')},{'label':'Самостоятельное электрическое оборудование','when':{'finishedArticle':{'eq':'yes'},'electric':{'eq':'yes'}},'output':sc(code,[{'label':'Обязательная проверка технических регламентов'}],'red','unknown')},{'label':'Оборудование под давлением','when':{'pressureOver005':{'eq':'yes'}},'output':sc(code,[{'label':'Проверить применимость ТР ТС 032/2013 по давлению, объему и среде'}],'red','no')}]}
 if prof=='agrochemical': return {'questionIds':['agrochemicalRegistered'], 'scenarios':[{'label':'Пестицид/агрохимикат зарегистрирован','when':{'agrochemicalRegistered':{'eq':'yes'}},'output':sc(code,[{'label':'Специальный регистрационный режим 109-ФЗ'}],'red','no')},{'label':'Регистрация отсутствует/статус не подтвержден','when':{'agrochemicalRegistered':{'eq':'no'}},'output':sc(code,[{'label':'Сначала определить, является ли продукт пестицидом/агрохимикатом'}],'yellow','no')}]}
 if prof=='pyrotechnics': return {'questionIds':[],'scenarios':[]}
 if prof=='furniture': return {'questionIds':['furniture'], 'scenarios':[{'label':'Мебельная продукция','when':{'furniture':{'eq':'yes'}},'output':sc('9403',[{'label':'Декларация по ТР ТС 025/2012'}],'red','no')},{'label':'Не является мебелью','when':{'furniture':{'eq':'no'}},'output':sc(code,[{'label':'Требуется повторная классификация'}],'yellow','no')}]}
 if prof=='textile_regulated': return {'questionIds':['textileProduct','material'], 'scenarios':[{'label':'Текстильное готовое изделие','when':{'textileProduct':{'eq':'yes'}},'output':sc(code,[{'label':'ТР ТС 017/2011 + проверка маркировки легпрома'}],'red','unknown')}]}
 if prof=='purpose_ambiguous': return {'questionIds':['toyPurpose','textileProduct'], 'scenarios':[{'label':'Игровое назначение','when':{'toyPurpose':{'eq':'yes'}},'output':sc('возможна 9503',[{'label':'ТР ТС 008/2011 и ЧЗ игрушек'}],'red','yes')},{'label':'Не игрушка','when':{'toyPurpose':{'eq':'no'}},'output':sc(code,[{'label':'Проверить материал и фактическое назначение'}],'yellow','unknown')}]}
 return {'questionIds':[],'scenarios':[]}

def main():
 patch_registry(); b=load(SRC,{}); products=b.get('products',[]); checked=b.get('checkedAt','2026-08-27'); summary=load(DATA/'compliance-summary.json',{}); dfs={}; rfs={}
 for p in products:
  sh=shard(p['id']); dfs.setdefault(sh,load(DATA/'compliance/details'/sh,{})); rfs.setdefault(sh,load(DATA/'rules/products'/sh,{})); d,flags=detail(p,checked); summary[str(p['id'])]={'result':p['result'],'markingCurrent':d['marking']['current']['status'],'markingFuture':d['marking']['future']['status'],'experiment':d['marking']['experiment']['status'],'documentFlags':flags,'tnvedCodes':codes(p['tn']),'lastChecked':checked}; dfs[sh][str(p['id'])]=d; rfs[sh][str(p['id'])]=rule(p)
 write(DATA/'compliance-summary.json',summary)
 for n,o in dfs.items(): write(DATA/'compliance/details'/n,o)
 for n,o in rfs.items(): write(DATA/'rules/products'/n,o)
 meta=load(DATA/'meta.json',{}); stats={'green':0,'yellow':0,'red':0}
 for s in summary.values():
  if s.get('result') in stats: stats[s['result']]+=1
 meta['complianceStatus']='partial'; meta['checkedProducts']=len(summary); meta['screeningStats']=stats; meta['lastComplianceBuild']=checked; write(DATA/'meta.json',meta)
 print(f"Merged {len(products)} home/garden products; total {len(summary)}; stats {stats}")
if __name__=='__main__': main()
