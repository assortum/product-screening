#!/usr/bin/env python3
import json, re
from pathlib import Path
import build_children as base

ROOT=Path(__file__).resolve().parents[1]
DATA=ROOT/'data'
SRC=ROOT/'data-src'/'children-02.json'

SPECIAL={'child_stroller','pacifier_nipple','teether','diaper_hygiene','child_care_equipment','medical_or_electronic','medical_or_feeding'}

def docs_special(p):
    pr=p['profile']
    if pr=='child_stroller':
        return ([{'type':'certificate','label':'Сертификат соответствия по ТР ТС 007/2011','status':'обязателен для детских колясок'}],['certificate'],'Нет','ТР ТС 007/2011 относит детские коляски к продукции, подлежащей обязательной сертификации.',['tr-ts-007','eec-child-products-2024'])
    if pr=='pacifier_nipple':
        return ([{'type':'sgr','label':'Свидетельство о государственной регистрации','status':'обязательно для сосок/пустышек соответствующей области'},{'type':'declaration','label':'Декларация по ТР ТС 007/2011','status':'после государственной регистрации'}],['sgr','declaration'],'Нет','Соски и пустышки относятся к продукции для детей до 3 лет, для которой ТР ТС 007/2011 предусматривает государственную регистрацию с последующим декларированием.',['tr-ts-007','eec-child-products-2024'])
    if pr=='teether':
        return ([{'type':'other','label':'Обязательная оценка соответствия','status':'форма зависит от квалификации как изделие для ухода либо игрушка'}],['unknown'],'Нет','Прорезыватель требует идентификации: при игровом назначении применяется ТР ТС 008/2011; для изделия ухода за ребёнком проверяется ТР ТС 007/2011.',['tr-ts-007','tr-ts-008','cz-toys-scope'])
    if pr=='diaper_hygiene':
        return ([{'type':'sgr','label':'СГР + декларация по ТР ТС 007/2011','status':'для одноразовых санитарно-гигиенических изделий детей до 3 лет'},{'type':'other','label':'Оценка по ТР ТС 007/2011','status':'для многоразовых/текстильных вариантов форма зависит от конструкции'}],['sgr','declaration'],'Нет','Одноразовые санитарно-гигиенические изделия для детей до 3 лет подлежат государственной регистрации с последующим декларированием; многоразовые варианты требуют отдельной идентификации.',['tr-ts-007'])
    if pr=='child_care_equipment':
        return ([{'type':'other','label':'Обязательная оценка соответствия детского изделия','status':'высокая вероятность; точная форма зависит от конструкции и области техрегламента'}],['unknown'],'Нет','Для манежей, переносок, ходунков, стульчиков и аналогичных изделий название Ozon недостаточно для выбора одной формы документа; детское назначение и конструкция требуют отдельной проверки обязательной оценки.',['tr-ts-007','pp-rf-2425'])
    if pr=='medical_or_electronic':
        return ([{'type':'other','label':'Регистрация медицинского изделия','status':'при медицинском назначении'},{'type':'other','label':'Оценка электрооборудования','status':'для электрического исполнения'}],['unknown'],'Возможно после уточнения','Для молокоотсоса режим зависит от ручного/электрического исполнения и заявленного медицинского назначения.',['tr-ts-004','tr-ts-020','rzn-med-registration'])
    if pr=='medical_or_feeding':
        return ([{'type':'sgr','label':'СГР / декларация по ТР ТС 007/2011','status':'при квалификации как изделие для кормления ребёнка до 3 лет'},{'type':'other','label':'Регистрация медицинского изделия','status':'при медицинском назначении'}],['sgr','declaration'],'Нет','Система кормления может относиться к регулируемым изделиям для кормления либо к медицинскому изделию; обе ветки требуют обязательного документа.',['tr-ts-007','rzn-med-registration'])
    return base.docs_for(p)

def detail2(p,checked):
    if p['profile'] not in SPECIAL:
        return base.detail(p,checked)
    items,flags,refusal,basis,sources=docs_special(p)
    return {'normalizedName':p['name'],'marking':base.mark_block(p),'tnved':{'candidates':[{'code':p['tn'],'confidence':p.get('confidence','средний'),'description':'Точный 10-значный код определяется после уточнения существенных характеристик.'}],'needsClarification':['материал','конструкция','возраст/назначение','самостоятельное изделие или комплектующая']},'documents':{'items':items,'refusalLetter':refusal,'basis':basis},'sourceIds':sources,'lastChecked':checked,'regulatoryComplexity':'complex' if p['result']=='red' else 'clarify'},flags

def rule2(p):
    pr=p['profile']
    if pr=='child_stroller':
        return {'questionIds':['finishedArticle','material'],'scenarios':[{'label':'Готовая детская коляска','when':{'finishedArticle':{'eq':'yes'}},'output':base.out('871500','Сертификат по ТР ТС 007/2011','red','unknown')},{'label':'Только аксессуар/запчасть','when':{'finishedArticle':{'eq':'no'}},'output':base.out('код по конкретной детали','Требуется отдельная проверка детали','yellow','unknown')}]}
    if pr=='pacifier_nipple':
        return {'questionIds':['material','childAge'],'scenarios':[{'label':'Соска/пустышка для ребёнка до 3 лет','when':{'childAge':{'in':['До 1 года','1–3 года']}},'output':base.out(p['tn'],'СГР + декларация по ТР ТС 007/2011','red','unknown')}]}
    if pr=='teether':
        return {'questionIds':['toyPurpose','material','childAge'],'scenarios':[{'label':'Прорезыватель является игрушкой','when':{'toyPurpose':{'eq':'yes'}},'output':base.out('950300','Сертификат по ТР ТС 008/2011','red','yes')},{'label':'Изделие ухода, не игрушка','when':{'toyPurpose':{'eq':'no'}},'output':base.out(p['tn'],'Требуется обязательная оценка по ТР ТС 007/2011; форма после идентификации','red','unknown')}]}
    if pr=='diaper_hygiene':
        return {'questionIds':['material','childAge','textileProduct'],'scenarios':[{'label':'Одноразовое санитарно-гигиеническое изделие до 3 лет','when':{'childAge':{'in':['До 1 года','1–3 года']},'textileProduct':{'eq':'no'}},'output':base.out('961900','СГР + декларация по ТР ТС 007/2011','red','unknown')},{'label':'Многоразовое/текстильное изделие','when':{'textileProduct':{'eq':'yes'}},'output':base.out(p['tn'],'Обязательная оценка по ТР ТС 007/2011; форма зависит от конструкции','red','unknown')}]}
    if pr=='child_care_equipment':
        return {'questionIds':['childCareProduct','furniture','electric','material'],'scenarios':[{'label':'Самостоятельное изделие для ухода за ребёнком','when':{'childCareProduct':{'eq':'yes'},'electric':{'eq':'no'}},'output':base.out(p['tn'],'Требуется определить обязательную форму по применимому техрегламенту','red','unknown')},{'label':'Электрическое детское оборудование','when':{'electric':{'eq':'yes'}},'output':base.out(p['tn'],'Обязательные требования детской продукции + электрооборудования','red','unknown')},{'label':'Не является детским изделием ухода','when':{'childCareProduct':{'eq':'no'}},'output':base.out(p['tn'],'Ручная классификация по фактическому назначению','yellow','unknown')}]}
    if pr=='medical_or_electronic':
        return {'questionIds':['electric','mainsPowered','batteryPowered','medicalPurpose'],'scenarios':[{'label':'Медицинское назначение','when':{'medicalPurpose':{'eq':'yes'}},'output':base.out('код медицинского изделия зависит от конструкции','Регистрация медицинского изделия','red','unknown')},{'label':'Электрический немедицинский прибор','when':{'electric':{'eq':'yes'},'medicalPurpose':{'eq':'no'}},'output':base.out(p['tn'],'Обязательная оценка электрооборудования','red','unknown')},{'label':'Ручное немедицинское изделие','when':{'electric':{'eq':'no'},'medicalPurpose':{'eq':'no'}},'output':base.out(p['tn'],'Требуется проверка материалов/контакта и обязательных перечней','yellow','unknown')}]}
    if pr=='medical_or_feeding':
        return {'questionIds':['medicalPurpose','foodContact','childAge','material'],'scenarios':[{'label':'Медицинское назначение','when':{'medicalPurpose':{'eq':'yes'}},'output':base.out('код медицинского изделия зависит от конструкции','Регистрация медицинского изделия','red','unknown')},{'label':'Изделие для кормления ребёнка до 3 лет','when':{'medicalPurpose':{'eq':'no'},'foodContact':{'eq':'yes'},'childAge':{'in':['До 1 года','1–3 года']}},'output':base.out(p['tn'],'СГР + декларация по ТР ТС 007/2011','red','unknown')}]}
    return base.rule_for(p)

def main():
    batch=base.load(SRC,{})
    products=batch.get('products',[]); checked=batch.get('checkedAt','2026-08-27')
    summary=base.load(DATA/'compliance-summary.json',{})
    details={}; rules={}
    for p in products:
        shard=base.shard_name(p['id'])
        if shard not in details: details[shard]=base.load(DATA/'compliance/details'/shard,{})
        if shard not in rules: rules[shard]=base.load(DATA/'rules/products'/shard,{})
        d,flags=detail2(p,checked)
        summary[str(p['id'])]={'result':p['result'],'markingCurrent':p.get('markCurrent','unknown'),'markingFuture':p.get('markFuture','unknown'),'experiment':p.get('experiment','unknown'),'documentFlags':flags,'tnvedCodes':base.codes(p['tn']),'lastChecked':checked}
        details[shard][str(p['id'])]=d; rules[shard][str(p['id'])]=rule2(p)
    base.write(DATA/'compliance-summary.json',summary)
    for name,obj in details.items(): base.write(DATA/'compliance/details'/name,obj)
    for name,obj in rules.items(): base.write(DATA/'rules/products'/name,obj)
    meta=base.load(DATA/'meta.json',{})
    stats={'green':0,'yellow':0,'red':0}
    for s in summary.values():
        if s.get('result') in stats: stats[s['result']]+=1
    meta['complianceStatus']='partial'; meta['checkedProducts']=len(summary); meta['screeningStats']=stats; meta['lastComplianceBuild']=checked
    (DATA/'meta.json').write_text(json.dumps(meta,ensure_ascii=False,indent=2),encoding='utf-8')
    print(f"Merged {len(products)} remaining child products; total {len(summary)}; stats {stats}")

if __name__=='__main__':
    main()
