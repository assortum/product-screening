#!/usr/bin/env python3
import json, re
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
DATA=ROOT/'data'
SRC=ROOT/'data-src'/'children-01.json'

YELLOW_PROFILES={
 'toy_accessory','toy_ambiguous','educational_media','accessory_generic','child_restraint_accessory',
 'feeding_accessory','child_cycle_accessory','child_seat_accessory','stroller_accessory','carrier_accessory',
 'hygiene_accessory','highchair_accessory','sanitary_accessory','child_transport_accessory','playground_accessory',
 'electronic_accessory','child_safety_structure_accessory','textile_child_accessory','child_safety_structure',
 'simple_safety_accessory','wearable_safety_accessory','carrier_or_restraint','hygiene_or_safety_set','simple_child_accessory'
}

CLARIFY={
 'toy':['точный вид игрушки','материал','электрический/механический принцип','возрастная группа до 14 лет'],
 'toy_accessory':['самостоятельная игрушка или только запчасть/аксессуар','игровое назначение','материал','электроника'],
 'toy_ambiguous':['игровое назначение','возраст пользователя','материал','конструкция'],
 'child_restraint':['материал и тип каркаса','обивка','конструкция детского удерживающего устройства'],
 'child_restraint_accessory':['конкретный вид аксессуара','самостоятельная функция безопасности или запчасть','материал'],
 'child_cycle':['двух-/трехколесный велосипед, беговел или игрушка на колесах','конструкция','ОКПД2 из разрешительного документа'],
 'child_cycle_accessory':['конкретный вид детали','является ли рамой велосипеда','материал','самостоятельная функция'],
 'feeding_bottle':['материал бутылочки','возраст ребёнка','контакт с пищей'],
 'feeding_accessory':['конкретная деталь: соска, крышка, ручка, трубочка и т.д.','материал','возраст','контакт с пищей'],
 'feeding_utensils':['вид прибора','материал','возраст ребёнка','контакт с пищей'],
 'sanitary_reusable':['материал','назначение для ухода за ребёнком','возраст','конструкция'],
 'sanitary_accessory':['конкретная функция','материал','самостоятельное изделие или деталь'],
 'child_electronic':['питание и номинальное напряжение','наличие радиомодуля','медицинское/немедицинское назначение','функция устройства'],
 'child_electronic_seat':['электропривод','питание/напряжение','конструкция сиденья','возраст'],
 'electronic_accessory':['конкретная электронная/пассивная деталь','питание','радиомодуль','функция'],
 'rideon_transport':['игрушечное или транспортное назначение','электропривод','возраст','конструкция'],
 'playground_or_toy':['стационарное оборудование площадки или домашняя игрушка','тип оборудования','место установки','конструкция'],
 'playground_accessory':['конкретная функция','является ли частью оборудования площадки','материал'],
 'toy_or_electronic':['игровое назначение','электропитание','радиомодуль','функция устройства'],
 'toy_or_child_textile':['игровое назначение','текстильное изделие или игрушка','материал','возраст'],
 'educational_media':['вид носителя','наличие электроники','является ли игрушкой/игрой'],
 'accessory_generic':['конкретный вид детали','материал','функция','самостоятельное изделие или комплектующая'],
 'child_seat_accessory':['конкретный вид аксессуара','материал','самостоятельная функция или часть сиденья'],
 'stroller_accessory':['конкретный вид аксессуара','материал','является ли частью коляски'],
 'carrier_accessory':['конкретный вид аксессуара','материал','несущая/удерживающая функция'],
 'hygiene_accessory':['конкретный вид изделия','материал','контакт с кожей','одноразовый/многоразовый'],
 'highchair_accessory':['конкретный вид изделия','материал','контакт с пищей','несущая функция'],
 'child_transport_accessory':['конкретная деталь','материал','электроника','самостоятельная функция'],
 'child_safety_structure_accessory':['конкретная деталь','материал','несущая/запирающая функция'],
 'textile_child_accessory':['вид текстильного изделия','материал','детское назначение','контакт с ребёнком'],
 'child_safety_structure':['конструкция','материал','назначение как изделие для ухода/безопасности','место установки'],
 'simple_safety_accessory':['материал','наличие электроники','игровое назначение','самостоятельная функция'],
 'wearable_safety_accessory':['конструкция','материал','защитное назначение','контакт с телом'],
 'carrier_or_restraint':['несущая/удерживающая функция','материал','способ крепления','возраст'],
 'hygiene_or_safety_set':['полный состав набора','материал и назначение каждого компонента'],
 'simple_child_accessory':['конкретная функция','материал','самостоятельное изделие или деталь']
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
    return out[:10]

def shard_name(pid):
    start=((pid-1)//500)*500+1
    return f'{start:05d}-{start+499:05d}.json'

def mark_block(p):
    cur=p.get('markCurrent','unknown'); fut=p.get('markFuture','unknown'); exp=p.get('experiment','unknown')
    if cur=='yes' and p['profile'] in {'toy','rideon_transport'}:
        current={'status':'yes','label':'Обязательная маркировка игр и игрушек для детей действует с 01.12.2025'}
        future={'status':'no','label':'Маркировка уже действует; с 01.09.2026 меняется этап учета оборота, а не перечень этой карточки'}
        experiment={'status':'no','label':'Эксперимент завершен; действует обязательный режим'}
    elif cur=='yes' and p['profile']=='child_cycle':
        current={'status':'yes','label':'Для подтвержденного детского велосипеда применяется действующая маркировка велосипедов'}
        future={'status':'no','label':'Маркировка уже действует'}
        experiment={'status':'no'}
    else:
        current={'status':cur,'label':'Требуется точный ТН ВЭД/ОКПД2 и проверка по действующим товарным группам маркировки' if cur=='unknown' else None}
        future={'status':fut,'label':'Будущие этапы требуют проверки после окончательной идентификации' if fut=='unknown' else None}
        experiment={'status':exp,'label':'Экспериментальные группы требуют проверки после окончательной идентификации' if exp=='unknown' else None}
    return {'current':current,'future':future,'experiment':experiment}

def docs_for(p):
    pr=p['profile']
    if pr in {'toy','rideon_transport'}:
        return ([{'type':'certificate','label':'Сертификат соответствия ЕАЭС по ТР ТС 008/2011','status':'обязателен при квалификации как игрушка'}],['certificate'],'Нет','Игрушки до 14 лет подлежат обязательной сертификации по ТР ТС 008/2011; соответствующие позиции 9503 00 одновременно входят в обязательную маркировку.',['tr-ts-008','cz-toys-scope','cz-toys-stages'])
    if pr in {'toy_accessory','toy_ambiguous'}:
        return ([{'type':'certificate','label':'Сертификат по ТР ТС 008/2011','status':'если изделие само является игрушкой'}],['unknown'],'Возможно после уточнения','Само нахождение рядом с игрушкой не делает аксессуар игрушкой. Нужно установить самостоятельное игровое назначение и код.',['tr-ts-008','cz-toys-scope'])
    if pr=='child_restraint':
        return ([{'type':'other','label':'Обязательная оценка соответствия по ТР ТС 018/2011','status':'обязательна для детского удерживающего устройства'}],['other'],'Нет','Автокресла и бустеры являются детскими удерживающими устройствами; точная форма документа и код зависят от конструкции и применяемой схемы оценки.',['tr-ts-018','eec-child-products-2024','eec-tnved-94'])
    if pr=='child_cycle':
        return ([{'type':'certificate','label':'Сертификат соответствия по ТР ТС 007/2011','status':'для детских велосипедов в области регламента'},{'type':'certificate','label':'Сертификат по ТР ТС 008/2011','status':'если изделие классифицируется как игрушка на колесах'}],['certificate'],'Нет','Конструкция определяет ветку: детский велосипед регулируется ТР ТС 007/2011, игрушка на колесах — ТР ТС 008/2011. В обоих сценариях есть обязательная оценка.',['tr-ts-007','tr-ts-008','cz-bicycles-scope','cz-toys-scope'])
    if pr in {'feeding_bottle','feeding_utensils'}:
        return ([{'type':'sgr','label':'Свидетельство о государственной регистрации','status':'для соответствующей продукции детей до 3 лет'},{'type':'declaration','label':'Декларация соответствия по ТР ТС 007/2011','status':'после СГР / по применимой схеме'}],['sgr','declaration'],'Нет','ТР ТС 007/2011 предусматривает государственную регистрацию с последующим декларированием для посуды и изделий для кормления детей до 3 лет.',['tr-ts-007','eec-child-products-2024'])
    if pr=='sanitary_reusable':
        return ([{'type':'certificate','label':'Сертификат соответствия по ТР ТС 007/2011','status':'для соответствующих многоразовых санитарно-гигиенических изделий'}],['certificate'],'Нет','Для многоразовых санитарно-гигиенических изделий из резины, пластмассы и металла ТР ТС 007/2011 предусматривает обязательную сертификацию. Материал и назначение нужно подтвердить.',['tr-ts-007','eec-child-products-2024'])
    if pr in {'child_electronic','child_electronic_seat'}:
        return ([{'type':'other','label':'Обязательная оценка электрооборудования','status':'наиболее вероятна; точный регламент и форма зависят от питания, напряжения и функции'},{'type':'other','label':'Государственная регистрация медицинского изделия','status':'только при заявленном медицинском назначении'}],['unknown'],'Нет','Для электрического/электронного изделия необходимо проверить ТР ТС 004/2011, ТР ТС 020/2011 и другие применимые требования; медицинское назначение меняет режим полностью.',['tr-ts-004','tr-ts-020','rzn-med-registration'])
    if pr=='playground_or_toy':
        return ([{'type':'other','label':'Оценка соответствия по ТР ЕАЭС 042/2017','status':'для оборудования детской игровой площадки; форма зависит от вида оборудования'},{'type':'certificate','label':'Сертификат по ТР ТС 008/2011','status':'если это домашняя игрушка'}],['certificate','declaration'],'Нет','Стационарное оборудование игровой площадки и домашняя игрушка — разные объекты регулирования, но оба сценария предполагают обязательную оценку соответствия.',['tr-eaeu-042','tr-eaeu-042-text','tr-ts-008','cz-toys-scope'])
    if pr=='toy_or_electronic':
        return ([{'type':'certificate','label':'Сертификат по ТР ТС 008/2011','status':'при игровом назначении'},{'type':'other','label':'Обязательная оценка электрооборудования','status':'если это не игрушка, а электронное устройство'}],['certificate','unknown'],'Нет','Обе основные ветки регулируемые; необходимо определить, является ли изделие игрушкой или самостоятельным электронным устройством.',['tr-ts-008','tr-ts-004','tr-ts-020','cz-toys-scope'])
    if pr=='toy_or_child_textile':
        return ([{'type':'certificate','label':'Сертификат по ТР ТС 008/2011','status':'при квалификации как игрушка'},{'type':'other','label':'Оценка по ТР ТС 007/2011','status':'если это детское текстильное изделие соответствующей области'}],['certificate','declaration'],'Нет','Игровой коврик может быть игрушкой либо детским текстильным изделием; обе ветки требуют отдельной идентификации.',['tr-ts-008','tr-ts-007','cz-toys-scope'])
    return ([],['unknown'],'Возможно после уточнения','Название не позволяет подтвердить обязательный документ. Нужны материал, конструкция, функция и статус самостоятельного изделия/комплектующей.',['pp-rf-2425','tr-ts-007'])

def detail(p, checked):
    items,flags,refusal,basis,sources=docs_for(p)
    return {'normalizedName':p['name'],'marking':mark_block(p),'tnved':{'candidates':[{'code':p['tn'],'confidence':p.get('confidence','средний'),'description':'Точный 10-значный код определяется после уточнения существенных характеристик.'}],'needsClarification':CLARIFY.get(p['profile'],['материал','конструкция','назначение'])},'documents':{'items':items,'refusalLetter':refusal,'basis':basis},'sourceIds':sources,'lastChecked':checked,'regulatoryComplexity':'complex' if p['result']=='red' else 'clarify'}, flags

def out(code,doc,result,mark='unknown'):
    return {'tnvedCandidates':[{'code':code}],'documents':{'status':'mandatory' if result=='red' else ('none' if result=='green' else 'check'),'items':[] if not doc else [{'label':doc}]},'marking':{'current':{'status':mark},'future':{'status':'no' if mark=='yes' else 'unknown'},'experiment':{'status':'no' if mark=='yes' else 'unknown'}},'result':result}

def rule_for(p):
    pr=p['profile']
    if pr=='toy':
        return {'questionIds':['toyPurpose','material','electric'],'scenarios':[{'label':'Подтверждено: игрушка для ребёнка','when':{'toyPurpose':{'eq':'yes'}},'output':out('9503 00','Сертификат по ТР ТС 008/2011','red','yes')},{'label':'Фактически не игрушка','when':{'toyPurpose':{'eq':'no'}},'output':out('требуется классификация по фактической функции','Требуется ручная проверка','yellow','unknown')}]}
    if pr in {'toy_accessory','toy_ambiguous'}:
        return {'questionIds':['finishedArticle','toyPurpose','material','electric'],'scenarios':[{'label':'Самостоятельная игрушка','when':{'finishedArticle':{'eq':'yes'},'toyPurpose':{'eq':'yes'}},'output':out('9503 00','Сертификат по ТР ТС 008/2011','red','yes')},{'label':'Только деталь/аксессуар, не самостоятельная игрушка','when':{'finishedArticle':{'eq':'no'}},'output':out('код по функции и материалу детали','Нужна проверка конкретной детали','yellow','unknown')}]}
    if pr=='child_restraint':
        return {'questionIds':['seatFrameMaterial'],'scenarios':[{'label':'Металлический обитый каркас','when':{'seatFrameMaterial':{'eq':'Металлический, обитый'}},'output':out('9401710001','Обязательная оценка по ТР ТС 018/2011','red','unknown')},{'label':'Металлический иной каркас','when':{'seatFrameMaterial':{'eq':'Металлический, иной'}},'output':out('9401790001','Обязательная оценка по ТР ТС 018/2011','red','unknown')},{'label':'Пластмассовый каркас','when':{'seatFrameMaterial':{'eq':'Пластмассовый'}},'output':out('9401800001','Обязательная оценка по ТР ТС 018/2011','red','unknown')}]}
    if pr=='child_cycle':
        return {'questionIds':['childCycleType'],'scenarios':[{'label':'Двухколесный детский велосипед','when':{'childCycleType':{'eq':'Двухколесный велосипед'}},'output':out('871200','Сертификат по ТР ТС 007/2011','red','yes')},{'label':'Трехколесный детский велосипед','when':{'childCycleType':{'eq':'Трехколесный велосипед'}},'output':out('9503001009','Сертификат по ТР ТС 007/2011; маркировка проверяется как велосипед по ТН ВЭД+ОКПД2','red','yes')},{'label':'Беговел без педалей','when':{'childCycleType':{'eq':'Беговел без педалей'}},'output':out('871200 либо 950300','Обязательная оценка; окончательная ветка требует классификации','red','unknown')},{'label':'Игрушка на колесах / каталка','when':{'childCycleType':{'eq':'Игрушка на колесах / каталка'}},'output':out('950300','Сертификат по ТР ТС 008/2011','red','yes')}]}
    if pr in {'feeding_bottle','feeding_utensils'}:
        return {'questionIds':['material','childAge','foodContact'],'scenarios':[{'label':'Изделие для кормления ребёнка до 3 лет','when':{'foodContact':{'eq':'yes'},'childAge':{'in':['До 1 года','1–3 года']}},'output':out(p['tn'],'СГР + декларация по ТР ТС 007/2011','red','unknown')},{'label':'Назначение старше 3 лет','when':{'foodContact':{'eq':'yes'},'childAge':{'eq':'Старше 3 лет'}},'output':out(p['tn'],'Требуется отдельное определение формы по ТР ТС 007/2011','red','unknown')}]}
    if pr=='sanitary_reusable':
        return {'questionIds':['material','childCareProduct'],'scenarios':[{'label':'Многоразовое изделие ухода за ребёнком','when':{'childCareProduct':{'eq':'yes'},'material':{'in':['Пластик','Резина/эластомер','Металл']}},'output':out(p['tn'],'Сертификат по ТР ТС 007/2011','red','unknown')},{'label':'Не является изделием ухода за ребёнком','when':{'childCareProduct':{'eq':'no'}},'output':out('код по материалу и фактической функции','Требуется ручная проверка','yellow','unknown')}]}
    if pr in {'child_electronic','child_electronic_seat','electronic_accessory'}:
        return {'questionIds':['electric','mainsPowered','batteryPowered','ratedVoltage','radioWireless','medicalPurpose'],'scenarios':[{'label':'Есть заявленное медицинское назначение','when':{'medicalPurpose':{'eq':'yes'}},'output':out('код зависит от функции медицинского изделия','Государственная регистрация медицинского изделия','red','unknown')},{'label':'Электрическое/электронное изделие','when':{'electric':{'eq':'yes'},'medicalPurpose':{'eq':'no'}},'output':out(p['tn'],'Обязательные требования к электрооборудованию уточняются по питанию, напряжению и функции','red','unknown')},{'label':'Пассивный аксессуар без электроники','when':{'electric':{'eq':'no'}},'output':out('код по функции и материалу','Возможен менее сложный режим после проверки перечней','yellow','unknown')}]}
    if pr=='rideon_transport':
        return {'questionIds':['toyPurpose','electric'],'scenarios':[{'label':'Игрушка на колесах для катания ребёнка','when':{'toyPurpose':{'eq':'yes'}},'output':out('950300','Сертификат по ТР ТС 008/2011','red','yes')},{'label':'Не является игрушкой','when':{'toyPurpose':{'eq':'no'}},'output':out('требуется классификация как транспорт/оборудование','Требуется ручная обязательная оценка','yellow','unknown')}]}
    if pr=='playground_or_toy':
        item=p['name'].lower()
        playground_doc='Декларация по ТР ЕАЭС 042/2017 для игрового домика площадки' if 'домик' in item else ('Обязательная оценка по ТР ЕАЭС 042/2017; форма определяется видом оборудования' if ('горк' in item or 'качел' in item) else 'Обязательная оценка по ТР ЕАЭС 042/2017')
        return {'questionIds':['playgroundUse','toyPurpose'],'scenarios':[{'label':'Оборудование детской игровой площадки','when':{'playgroundUse':{'eq':'Оборудование детской игровой площадки'}},'output':out('код определяется видом оборудования площадки',playground_doc,'red','unknown')},{'label':'Домашняя игрушка / игровой инвентарь','when':{'playgroundUse':{'eq':'Домашняя игрушка / игровой инвентарь'},'toyPurpose':{'eq':'yes'}},'output':out('950300','Сертификат по ТР ТС 008/2011','red','yes')},{'label':'Аттракцион','when':{'playgroundUse':{'eq':'Аттракцион'}},'output':out('требуется отдельная классификация','Отдельные обязательные требования к аттракционам','red','unknown')}]}
    if pr=='toy_or_electronic':
        return {'questionIds':['toyPurpose','electric','mainsPowered','radioWireless'],'scenarios':[{'label':'Игрушка','when':{'toyPurpose':{'eq':'yes'}},'output':out('950300','Сертификат по ТР ТС 008/2011','red','yes')},{'label':'Самостоятельное электронное устройство','when':{'toyPurpose':{'eq':'no'},'electric':{'eq':'yes'}},'output':out('группа 85/90','Обязательная оценка электрооборудования','red','unknown')}]}
    if pr=='toy_or_child_textile':
        return {'questionIds':['toyPurpose','textileProduct','material'],'scenarios':[{'label':'Игровой коврик является игрушкой','when':{'toyPurpose':{'eq':'yes'}},'output':out('950300','Сертификат по ТР ТС 008/2011','red','yes')},{'label':'Детское текстильное изделие, не игрушка','when':{'toyPurpose':{'eq':'no'},'textileProduct':{'eq':'yes'}},'output':out('группа 57/63','Обязательная оценка по ТР ТС 007/2011 — форма зависит от вида','red','unknown')}]}
    if pr=='textile_child_accessory':
        return {'questionIds':['textileProduct','childCareProduct','material'],'scenarios':[{'label':'Детское текстильное изделие','when':{'textileProduct':{'eq':'yes'},'childCareProduct':{'eq':'yes'}},'output':out(p['tn'],'Требуется проверка формы оценки по ТР ТС 007/2011','red','unknown')},{'label':'Декоративный аксессуар общего назначения','when':{'childCareProduct':{'eq':'no'}},'output':out(p['tn'],'Требуется проверка по фактическому виду текстильного изделия','yellow','unknown')}]}
    if pr=='simple_safety_accessory':
        return {'questionIds':['material','electric','toyPurpose'],'scenarios':[{'label':'Пассивный неигровой аксессуар','when':{'electric':{'eq':'no'},'toyPurpose':{'eq':'no'}},'output':out(p['tn'],'Проверить ПП РФ №2425 и применимость ТР ТС 007/2011; возможен простой вход','yellow','unknown')},{'label':'Электронное изделие','when':{'electric':{'eq':'yes'}},'output':out(p['tn'],'Требуется проверка электрооборудования','red','unknown')},{'label':'Изделие фактически является игрушкой','when':{'toyPurpose':{'eq':'yes'}},'output':out('950300','Сертификат по ТР ТС 008/2011','red','yes')}]}
    return {'questionIds':['finishedArticle','material','electric','toyPurpose'],'scenarios':[{'label':'Самостоятельная игрушка','when':{'finishedArticle':{'eq':'yes'},'toyPurpose':{'eq':'yes'}},'output':out('950300','Сертификат по ТР ТС 008/2011','red','yes')},{'label':'Пассивная деталь/аксессуар','when':{'finishedArticle':{'eq':'no'},'electric':{'eq':'no'}},'output':out(p['tn'],'Требуется проверка конкретной детали; возможен простой режим','yellow','unknown')},{'label':'Электрическая деталь/аксессуар','when':{'electric':{'eq':'yes'}},'output':out(p['tn'],'Требуется проверка обязательных требований к электрооборудованию','red','unknown')}]}

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
        summary[str(p['id'])]={'result':p['result'],'markingCurrent':p.get('markCurrent','unknown'),'markingFuture':p.get('markFuture','unknown'),'experiment':p.get('experiment','unknown'),'documentFlags':flags,'tnvedCodes':codes(p['tn']),'lastChecked':checked}
        detail_files[shard][str(p['id'])]=d
        rule_files[shard][str(p['id'])]=rule_for(p)
    write(DATA/'compliance-summary.json',summary)
    for name,obj in detail_files.items(): write(DATA/'compliance/details'/name,obj)
    for name,obj in rule_files.items(): write(DATA/'rules/products'/name,obj)
    meta=load(DATA/'meta.json',{})
    stats={'green':0,'yellow':0,'red':0}
    for s in summary.values():
        if s.get('result') in stats: stats[s['result']]+=1
    meta['complianceStatus']='partial'; meta['checkedProducts']=len(summary); meta['screeningStats']=stats; meta['lastComplianceBuild']=checked
    (DATA/'meta.json').write_text(json.dumps(meta,ensure_ascii=False,indent=2),encoding='utf-8')
    print(f"Merged {len(products)} child products; total {len(summary)}; stats {stats}")

if __name__=='__main__':
    main()
