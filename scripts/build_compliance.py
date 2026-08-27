#!/usr/bin/env python3
import json, re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "data-src"
DATA = ROOT / "data"
CHECKED_DATE = "2026-08-27"

CLARIFICATIONS = {
 "bra_accessory":["конкретный вид аксессуара","материал","самостоятельное изделие или деталь/фурнитура"],
 "work_accessory":["конкретный вид изделия","материал","защитное назначение СИЗ","самостоятельное изделие или комплектующая"],
 "outerwear":["трикотажное или тканое изделие","пол/товарная группа","наличие покрытия"],
 "tie":["трикотажное или нетрикотажное изделие","материал"],
 "headwear":["материал","способ изготовления","самостоятельный головной убор или деталь"],
 "maternity_bandage":["медицинское/ортопедическое назначение","наличие регистрации медизделия","конструкция"],
 "first_layer":["точный вид изделия","слой/характер контакта с кожей","способ изготовления"],
 "garment_accessory":["самостоятельное изделие или часть одежды","способ изготовления","материал"],
 "overshoe":["наличие собственной подошвы","материал","защитное назначение СИЗ"],
 "broad_clothing":["конкретная конструкция","материал","одежда или аксессуар","слой"],
 "sports_first_layer":["слой одежды","конструкция","спортивное назначение"],
 "blouse":["трикотажное или тканое изделие","материал"],
 "baby_blouse":["рост до/свыше 86 см","возраст","способ изготовления","слой"],
 "workwear":["защитные свойства СИЗ","способ изготовления","пол/товарная группа","материал"],
 "baby_first":["возраст","рост до/свыше 86 см","1-й слой","способ изготовления"],
 "top":["способ изготовления","конструкция","пол"],
 "pants":["способ изготовления","пол","материал"],
 "baby_pants":["рост до/свыше 86 см","возраст","способ изготовления"],
 "bra":["конструкция","материал"],
 "gloves":["материал","способ изготовления"],
 "waders":["наличие собственной подошвы","материал","одежда или обувь","защитное назначение"],
 "sports_bottom":["слой","способ изготовления","пол"],
 "sweater":["трикотажная конструкция","сырьевой состав"],
 "gaiter":["конструкция","материал","наличие подошвы"],
 "hosiery":["сырьевой состав","слой/сезонность","назначение"],
 "compression":["медицинское назначение","регистрация медизделия","вид компрессионного изделия"],
 "work_headwear":["защитные свойства СИЗ","материал","тип головного убора"],
 "fur_accessory":["натуральный или искусственный мех","конструкция","мех как основной материал или отделка"],
 "rainwear":["материал/покрытие","способ изготовления","пол"],
 "faux_fur":["искусственный мех группы 4304 или текстильная имитация","конструкция"],
 "natural_fur":["вид меха","мех как основной материал/подкладка или только отделка"],
 "vest":["способ изготовления","пол","слой"],
 "underwear_male":["способ изготовления","слой","материал"],
 "carnival":["обычная одежда или только праздничный реквизит","материал","конструкция"],
 "child_carnival":["возраст","одежда/игровой костюм/реквизит","слой","рост"],
 "kigurumi":["домашняя одежда/пижама/карнавальная","слой","способ изготовления","пол"],
 "baby_kigurumi":["возраст","рост","слой","назначение"],
 "sports_uniform":["профессиональная экипировка спортивной команды","способ изготовления","слой"],
 "visor":["самостоятельный головной убор или деталь","материал","способ изготовления"],
 "baby_hosiery":["возраст","рост/размерная категория","чулочно-носочное изделие 1-го слоя"],
 "overall":["способ изготовления","пол","слой/подкладка"],
 "ski":["способ изготовления","пол","лыжное/сноубордическое назначение"],
 "baby_outer":["возраст","рост","слой/подкладка","способ изготовления"],
 "set":["состав комплекта по предметам","характеристики каждого предмета","признаки комплекта/набора"],
 "baby_set":["состав комплекта","возраст","рост","слой каждого предмета"],
 "underwear_set":["состав комплекта","пол","способ изготовления","вид каждого предмета"],
 "thermal_underwear":["слой","пол","способ изготовления","назначение как белье"],
 "underwear":["пол","способ изготовления","вид белья"]
}

def docs(mode):
    if mode=="adult_declaration":
        return ([{"type":"declaration","label":"Декларация соответствия ЕАЭС по ТР ТС 017/2011","status":"обязательна"}],["declaration"],"Нет","ТР ТС 017/2011 предусматривает обязательное декларирование для соответствующей одежды 2-го/3-го слоя, головных уборов, одежды из кожи/меха и иных указанных групп.",["tr-ts-017"])
    if mode=="adult_certificate":
        return ([{"type":"certificate","label":"Сертификат соответствия ЕАЭС по ТР ТС 017/2011","status":"обязателен"}],["certificate"],"Нет","Бельевые, корсетные и аналогичные изделия, а также чулочно-носочные изделия первого слоя подлежат обязательной сертификации по ТР ТС 017/2011.",["tr-ts-017"])
    if mode=="child_first":
        return ([{"type":"sgr","label":"СГР для детской продукции 1-го слоя до 3 лет","status":"обязательно при возрасте до 3 лет"},{"type":"declaration","label":"Декларация по ТР ТС 007/2011 после СГР","status":"обязательна"}],["sgr","declaration"],"Нет","Для бельевых и чулочно-носочных изделий 1-го слоя детей до 3 лет установлена государственная регистрация с последующим декларированием.",["tr-ts-007"])
    if mode=="child_second":
        return ([{"type":"certificate","label":"Сертификат соответствия ЕАЭС по ТР ТС 007/2011","status":"обязателен для типичной одежды 2-го слоя"}],["certificate"],"Нет","Одежда и изделия 2-го слоя для детей подлежат обязательной сертификации. Возраст и слой необходимо подтвердить.",["tr-ts-007"])
    if mode=="child_outer":
        return ([{"type":"certificate","label":"Сертификат по ТР ТС 007/2011","status":"для 3-го слоя до 1 года"},{"type":"declaration","label":"Декларация по ТР ТС 007/2011","status":"для 3-го слоя старше 1 года"}],["certificate","declaration"],"Нет","Для детской одежды 3-го слоя форма подтверждения меняется по возрасту: до 1 года — сертификация, старше 1 года — декларирование.",["tr-ts-007"])
    if mode=="child_ambiguous":
        return ([{"type":"certificate","label":"Обязательная оценка по ТР ТС 007/2011","status":"наиболее вероятна для детской одежды"},{"type":"declaration","label":"Декларация по ТР ТС 007/2011","status":"возможна для отдельных слоев/возрастов"}],["certificate","declaration"],"Нет","Товар относится к детской продукции, но форма зависит от слоя, возраста и фактического назначения.",["tr-ts-007"])
    if mode=="workwear":
        return ([{"type":"declaration","label":"Декларация по ТР ТС 017/2011","status":"для обычной рабочей одежды без функций СИЗ"},{"type":"certificate","label":"Оценка соответствия по ТР ТС 019/2011","status":"для СИЗ; форма зависит от защитных свойств"}],["declaration","certificate"],"Нет","Обычная рабочая одежда регулируется ТР ТС 017/2011; специальная защитная одежда/СИЗ — ТР ТС 019/2011.",["tr-ts-017","tr-ts-019"])
    if mode=="medical_corset":
        return ([{"type":"certificate","label":"Сертификат по ТР ТС 017/2011","status":"для немедицинского корсетного изделия"},{"type":"other","label":"Государственная регистрация медицинского изделия","status":"при медицинском назначении"}],["certificate"],"Нет","Немедицинский корсетный бандаж требует подтверждения по ТР ТС 017/2011; при медицинском назначении действует режим медицинского изделия.",["tr-ts-017","rzn-med-registration","pp-rf-1684-2024"])
    if mode=="compression":
        return ([{"type":"certificate","label":"Сертификат по ТР ТС 017/2011","status":"для немедицинского чулочно-носочного изделия 1-го слоя"},{"type":"other","label":"Государственная регистрация медицинского изделия","status":"при медицинском назначении"}],["certificate"],"Нет","Группа 6115 включена в обязательную маркировку, включая компрессионные изделия; при медицинском назначении дополнительно проверяется регистрация медизделия.",["tr-ts-017","cz-legprom-2025","rzn-med-registration"])
    if mode=="mandatory_ambiguous":
        return ([{"type":"other","label":"Обязательная оценка соответствия","status":"форма зависит от окончательной идентификации"}],["declaration","certificate"],"Нет","Возможны несколько регулируемых сценариев. Точную форму обязательной оценки нужно определить после уточнения конструкции.",["tr-ts-017"])
    return ([],["unknown"],"Возможно после уточнения","Название слишком широкое: возможен как регулируемый товар легкой промышленности, так и отдельная деталь/фурнитура другой группы.",["tr-ts-017","cz-legprom-scope"])

def codes(text):
    vals=[]
    for m in re.findall(r"\b\d{4}(?:\s?\d{2})?(?:\s?\d{3})?(?:\s?\d)?\b",text):
        v=m.replace(" ","")
        if v not in vals: vals.append(v)
    return vals[:8]

def mark_sources(p):
    if p["profile"]=="natural_fur": return ["cz-natural-fur"]
    if p["mark"]!="yes": return ["cz-legprom-scope"]
    p2025={"baby_blouse","baby_first","baby_pants","baby_vest","baby_kigurumi","baby_hosiery","compression","hosiery","headwear","bra","first_layer","gaiter","gloves","garment_accessory"}
    return ["cz-legprom-scope","cz-legprom-2025","pp-rf-883-2024"] if p["profile"] in p2025 else ["cz-legprom-scope","cz-legprom-2024"]

def detail(p, checked):
    items,flags,refusal,basis,src=docs(p["mode"])
    sources=[]
    for x in src+mark_sources(p):
        if x not in sources: sources.append(x)
    current={"status":p["mark"],"label":"Обязательная маркировка действует на дату анализа" if p["mark"]=="yes" else "Требуется точный код ТН ВЭД/ОКПД2 и идентификация"}
    if p["profile"]=="natural_fur": current={"status":"yes","label":"Натуральный мех: Data Matrix с 01.03.2026","date":"01.03.2026"}
    return {"normalizedName":p["name"],"marking":{"current":current,"future":{"status":"no","label":"Отдельный утвержденный будущий этап не выявлен; проверяется текущий режим"},"experiment":{"status":"no","label":"Эксперимент не является основанием текущего вывода"}},"tnved":{"candidates":[{"code":p["tn"],"confidence":p["confidence"],"description":"10-значный код нельзя надежно определить только по названию из исходного файла."}],"needsClarification":CLARIFICATIONS.get(p["profile"],["материал","конструкция","назначение"])},"documents":{"items":items,"refusalLetter":refusal,"basis":basis},"sourceIds":sources,"lastChecked":checked,"screeningReason":"Нужна дополнительная идентификация до окончательного решения." if p["mode"]=="ambiguous" else "Не соответствует стратегии простого регуляторного входа из-за обязательной оценки соответствия."},flags

def output(code,doc,result="red",mark="yes"):
    return {"tnvedCandidates":[{"code":code}],"documents":{"status":"mandatory","items":[{"label":doc}]},"marking":{"current":{"status":mark},"future":{"status":"no"},"experiment":{"status":"no"}},"result":result}

def rule(p):
    pr=p["profile"]; tn=p["tn"]; mark=p["mark"]
    if pr=="outerwear":
        q=["garmentConstruction","sexGroup"]; sc=[]
        for c,s,code in [("Трикотажное/вязаное","Мужское/для мальчиков","6101"),("Трикотажное/вязаное","Женское/для девочек","6102"),("Тканое/нетрикотажное","Мужское/для мальчиков","6201"),("Тканое/нетрикотажное","Женское/для девочек","6202")]: sc.append({"label":f"{c}, {s.lower()}","when":{"garmentConstruction":{"eq":c},"sexGroup":{"eq":s}},"output":output(code,"Декларация ЕАЭС по ТР ТС 017/2011")})
    elif pr=="pants":
        q=["garmentConstruction","sexGroup"]; sc=[]
        for c,s,code in [("Трикотажное/вязаное","Мужское/для мальчиков","6103"),("Трикотажное/вязаное","Женское/для девочек","6104"),("Тканое/нетрикотажное","Мужское/для мальчиков","6203"),("Тканое/нетрикотажное","Женское/для девочек","6204")]: sc.append({"label":f"{c}, {s.lower()}","when":{"garmentConstruction":{"eq":c},"sexGroup":{"eq":s}},"output":output(code,"Декларация ЕАЭС по ТР ТС 017/2011")})
    elif pr=="blouse":
        q=["garmentConstruction"]; sc=[{"label":"Трикотажная блузка","when":{"garmentConstruction":{"eq":"Трикотажное/вязаное"}},"output":output("6106","Декларация ЕАЭС по ТР ТС 017/2011")},{"label":"Тканая блузка","when":{"garmentConstruction":{"eq":"Тканое/нетрикотажное"}},"output":output("6206","Декларация ЕАЭС по ТР ТС 017/2011")}]
    elif pr=="sweater": q=["garmentConstruction","material"]; sc=[{"label":"Трикотажное изделие","when":{"garmentConstruction":{"eq":"Трикотажное/вязаное"}},"output":output("6110","Декларация ЕАЭС по ТР ТС 017/2011")}]
    elif pr=="maternity_bandage":
        q=["medicalPurpose","garmentLayer"]; sc=[{"label":"Медицинский/ортопедический бандаж","when":{"medicalPurpose":{"eq":"yes"}},"output":output("9021 (вероятная группа; требуется классификация)","Государственная регистрация медицинского изделия","red","unknown")},{"label":"Немедицинское корсетное изделие","when":{"medicalPurpose":{"eq":"no"}},"output":output("6212","Сертификат ЕАЭС по ТР ТС 017/2011")}]
    elif pr=="compression":
        q=["medicalPurpose"]; sc=[{"label":"Медицинское назначение","when":{"medicalPurpose":{"eq":"yes"}},"output":output("6115","Регистрация медицинского изделия; требования маркировки по 6115 сохраняются для проверки","red","yes")},{"label":"Без медицинского назначения","when":{"medicalPurpose":{"eq":"no"}},"output":output("6115","Сертификат ЕАЭС по ТР ТС 017/2011")}]
    elif pr.startswith("baby_"):
        q=["childHeight","childAge","garmentLayer","garmentConstruction"]; sc=[{"label":"До 86 см, трикотаж","when":{"childHeight":{"eq":"До 86 см включительно"},"garmentConstruction":{"eq":"Трикотажное/вязаное"}},"output":output("6111","Форма по ТР ТС 007/2011 зависит от слоя/возраста")},{"label":"До 86 см, тканое изделие","when":{"childHeight":{"eq":"До 86 см включительно"},"garmentConstruction":{"eq":"Тканое/нетрикотажное"}},"output":output("6209","Форма по ТР ТС 007/2011 зависит от слоя/возраста")},{"label":"1-й слой до 3 лет","when":{"childAge":{"in":["До 1 года","1–3 года"]},"garmentLayer":{"eq":"1-й слой — непосредственный контакт с кожей"}},"output":output("6111 / 6209","СГР + декларация по ТР ТС 007/2011")},{"label":"2-й слой","when":{"garmentLayer":{"eq":"2-й слой — ограниченный контакт с кожей"}},"output":output("6111 / 6209 либо соответствующая группа 61/62","Сертификат по ТР ТС 007/2011")},{"label":"3-й слой до 1 года","when":{"childAge":{"eq":"До 1 года"},"garmentLayer":{"eq":"3-й слой — верхняя одежда"}},"output":output("6111 / 6209","Сертификат по ТР ТС 007/2011")},{"label":"3-й слой старше 1 года","when":{"childAge":{"in":["1–3 года","Старше 3 лет"]},"garmentLayer":{"eq":"3-й слой — верхняя одежда"}},"output":output("6111 / 6209 либо соответствующая группа 61/62","Декларация по ТР ТС 007/2011")}]
    elif pr in {"workwear","work_headwear"}:
        q=["protectivePPE","garmentConstruction","sexGroup"]; sc=[{"label":"Обычная рабочая одежда без функций СИЗ","when":{"protectivePPE":{"eq":"no"}},"output":output(tn,"Декларация по ТР ТС 017/2011","red",mark)},{"label":"Защитная спецодежда / СИЗ","when":{"protectivePPE":{"eq":"yes"}},"output":output(tn,"Оценка соответствия по ТР ТС 019/2011","red","unknown")}]
    elif pr=="bra_accessory":
        q=["finishedArticle","material"]; sc=[{"label":"Деталь/фурнитура","when":{"finishedArticle":{"eq":"no"}},"output":output("классификация детали по материалу/функции","Нужна проверка применимости обязательных требований","yellow","no")},{"label":"Самостоятельное готовое изделие","when":{"finishedArticle":{"eq":"yes"}},"output":output("6117 / 6217 / 6212","Вероятна обязательная оценка по ТР ТС 017/2011","yellow","unknown")}]
    elif pr=="work_accessory":
        q=["finishedArticle","protectivePPE","material"]; sc=[{"label":"Элемент СИЗ","when":{"protectivePPE":{"eq":"yes"}},"output":output("зависит от изделия","Оценка по ТР ТС 019/2011","red","unknown")},{"label":"Не СИЗ и не самостоятельная одежда","when":{"protectivePPE":{"eq":"no"},"finishedArticle":{"eq":"no"}},"output":output("зависит от материала/функции","Возможен отказной сценарий только после идентификации","yellow","unknown")}]
    elif pr=="overshoe":
        q=["integratedSole","protectivePPE","material"]; sc=[{"label":"Есть собственная подошва","when":{"integratedSole":{"eq":"yes"}},"output":output("группа 64","Обязательная оценка как обуви/соответствующего изделия")},{"label":"Без подошвы, не СИЗ","when":{"integratedSole":{"eq":"no"},"protectivePPE":{"eq":"no"}},"output":output("6406 90 900 0 / 6307","Обязательная оценка после идентификации")},{"label":"Защитное изделие СИЗ","when":{"protectivePPE":{"eq":"yes"}},"output":output("зависит от конструкции","Оценка по ТР ТС 019/2011","red","unknown")}]
    elif pr=="waders":
        q=["integratedSole","protectivePPE","material"]; sc=[{"label":"С интегрированной обувью","when":{"integratedSole":{"eq":"yes"}},"output":output("6401 / 6402","Обязательная оценка как обуви/соответствующего изделия")},{"label":"Без интегрированной обуви","when":{"integratedSole":{"eq":"no"}},"output":output("6113 / 6210 / 6211","Декларация по ТР ТС 017/2011")}]
    elif pr=="carnival":
        q=["carnivalRequisite","garmentConstruction","material"]; sc=[{"label":"Обычная многоразовая одежда","when":{"carnivalRequisite":{"eq":"no"}},"output":output("группы 61/62","Обязательная оценка по ТР ТС 017/2011")},{"label":"Только праздничный реквизит","when":{"carnivalRequisite":{"eq":"yes"}},"output":output("возможна группа 9505","Требуется отдельная проверка","yellow","unknown")}]
    elif pr=="child_carnival":
        q=["toyPurpose","carnivalRequisite","childAge","childHeight","garmentLayer"]; sc=[{"label":"Детская одежда","when":{"toyPurpose":{"eq":"no"},"carnivalRequisite":{"eq":"no"}},"output":output("6111 / 6209 либо иные группы 61/62","Обязательная оценка по ТР ТС 007/2011")},{"label":"Игровой костюм/игрушка","when":{"toyPurpose":{"eq":"yes"}},"output":output("возможна группа 9503","Обязательная оценка по требованиям к игрушкам","red","unknown")},{"label":"Только праздничный реквизит","when":{"carnivalRequisite":{"eq":"yes"}},"output":output("возможна группа 9505","Требуется отдельная проверка","yellow","unknown")}]
    elif pr=="visor":
        q=["finishedArticle","material"]; sc=[{"label":"Самостоятельный головной убор","when":{"finishedArticle":{"eq":"yes"}},"output":output("6505 / 6506","Декларация по ТР ТС 017/2011")},{"label":"Отдельная деталь","when":{"finishedArticle":{"eq":"no"}},"output":output("3926 / 6307 / иные по материалу","Нужна отдельная проверка","yellow","unknown")}]
    elif pr=="headwear":
        q=["garmentConstruction","material"]; sc=[{"label":"Текстильный/трикотажный головной убор","when":{"material":{"eq":"Текстиль"}},"output":output("6505 00","Декларация по ТР ТС 017/2011")},{"label":"Из иного материала","when":{"material":{"in":["Натуральная кожа","Искусственная кожа","Пластик","Комбинированный","Иное"]}},"output":output("6506 99 / иная позиция 65","Обязательная оценка после классификации")}]
    elif pr=="gaiter":
        q=["integratedSole","material"]; sc=[{"label":"Без подошвы","when":{"integratedSole":{"eq":"no"}},"output":output("6406 90 900 0","Обязательная оценка после идентификации")},{"label":"Фактически обувь","when":{"integratedSole":{"eq":"yes"}},"output":output("группа 64","Обязательная оценка как обуви")}]
    elif pr=="natural_fur": q=["naturalFur"]; sc=[{"label":"Натуральный мех/меховая подкладка","when":{"naturalFur":{"eq":"yes"}},"output":output("4303","Декларация по ТР ТС 017/2011")}]
    elif pr=="fur_accessory":
        q=["naturalFur","finishedArticle"]; sc=[{"label":"Натуральный мех — материал изделия","when":{"naturalFur":{"eq":"yes"},"finishedArticle":{"eq":"yes"}},"output":output("4303 либо иная меховая позиция","Декларация по ТР ТС 017/2011")},{"label":"Без натурального меха","when":{"naturalFur":{"eq":"no"}},"output":output("6117 / 6214 / 6217 / иные","Декларация по ТР ТС 017/2011")}]
    else:
        q=["garmentConstruction","garmentLayer","sexGroup"]; sc=[{"label":"Трикотажное/вязаное изделие","when":{"garmentConstruction":{"eq":"Трикотажное/вязаное"}},"output":output(tn,"Обязательная оценка соответствия; точная форма после идентификации","red",mark)},{"label":"Тканое/нетрикотажное изделие","when":{"garmentConstruction":{"eq":"Тканое/нетрикотажное"}},"output":output(tn,"Обязательная оценка соответствия; точная форма после идентификации","red",mark)}]
    return {"questionIds":q,"scenarios":sc}

def shard_name(pid):
    start=((pid-1)//500)*500+1
    return f"{start:05d}-{start+499:05d}.json"

def main():
    products=[]
    for path in sorted(SRC.glob("*.json")):
        obj=json.loads(path.read_text(encoding="utf-8")); checked=obj.get("checkedAt",CHECKED_DATE)
        for p in obj.get("products",[]): p["_checked"]=checked; products.append(p)
    seen=set()
    for p in products:
        if p["id"] in seen: raise SystemExit(f"Duplicate product id: {p['id']}")
        seen.add(p["id"])
    summary={}; detail_shards={}; rule_shards={}; stats={"green":0,"yellow":0,"red":0}
    for p in products:
        d,flags=detail(p,p["_checked"]); result="yellow" if p["mode"]=="ambiguous" else "red"; stats[result]+=1
        summary[str(p["id"]) ]={"result":result,"markingCurrent":p["mark"],"markingFuture":"no","experiment":"no","documentFlags":flags,"tnvedCodes":codes(p["tn"]),"lastChecked":p["_checked"]}
        shard=shard_name(p["id"]); detail_shards.setdefault(shard,{})[str(p["id"])]=d; rule_shards.setdefault(shard,{})[str(p["id"])]=rule(p)
    (DATA/"compliance/details").mkdir(parents=True,exist_ok=True); (DATA/"rules/products").mkdir(parents=True,exist_ok=True)
    (DATA/"compliance-summary.json").write_text(json.dumps(summary,ensure_ascii=False,separators=(",",":")),encoding="utf-8")
    for name,obj in detail_shards.items(): (DATA/"compliance/details"/name).write_text(json.dumps(obj,ensure_ascii=False,separators=(",",":")),encoding="utf-8")
    for name,obj in rule_shards.items(): (DATA/"rules/products"/name).write_text(json.dumps(obj,ensure_ascii=False,separators=(",",":")),encoding="utf-8")
    meta_path=DATA/"meta.json"; meta=json.loads(meta_path.read_text(encoding="utf-8")); meta["complianceStatus"]="partial" if products else "pending"; meta["checkedProducts"]=len(products); meta["screeningStats"]=stats; meta["lastComplianceBuild"]=CHECKED_DATE; meta_path.write_text(json.dumps(meta,ensure_ascii=False,indent=2),encoding="utf-8")
    print(f"Built {len(products)} products: {stats}")

if __name__=="__main__": main()
