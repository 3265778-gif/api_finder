"""
API Finder Bot — AI-агент для пошуку активних фармацевтичних інгредієнтів
=========================================================================
Автор: Pharmasel QA Team
Залежності: pip install -r requirements.txt
Запуск:     python agent.py
"""

import os
import json
import httpx
import asyncio
from datetime import datetime
from pathlib import Path
from typing import Optional
from dotenv import load_dotenv

from langchain_anthropic import ChatAnthropic
from langchain.agents import AgentExecutor, create_tool_calling_agent
from langchain.tools import tool
from langchain_core.prompts import ChatPromptTemplate

load_dotenv()

# ─── Конфігурація ────────────────────────────────────────────────────────────

ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY", "")
TAVILY_API_KEY    = os.getenv("TAVILY_API_KEY", "")
REPORTS_DIR       = Path("reports")
REPORTS_DIR.mkdir(exist_ok=True)

# ─── Інструменти агента ──────────────────────────────────────────────────────

@tool
def search_pubchem(query: str) -> str:
    """
    Шукає дані про АФІ в базі PubChem.
    Повертає: CAS-номер, молекулярна формула, IUPAC-назва, молекулярна маса,
    ліцензійний статус. Приймає назву речовини або CAS-номер.
    """
    try:
        url = f"https://pubchem.ncbi.nlm.nih.gov/rest/pug/compound/name/{query}/JSON"
        resp = httpx.get(url, timeout=15, follow_redirects=True)
        if resp.status_code != 200:
            return f"PubChem: речовину '{query}' не знайдено (HTTP {resp.status_code})"

        data = resp.json()
        compound = data["PC_Compounds"][0]
        props = compound.get("props", [])

        result = {
            "cid": compound.get("id", {}).get("id", {}).get("cid"),
            "molecular_formula": None,
            "molecular_weight": None,
            "iupac_name": None,
            "inchi_key": None,
        }

        for p in props:
            urn = p.get("urn", {})
            val = p.get("value", {})
            label = urn.get("label", "")
            name  = urn.get("name", "")

            if label == "Molecular Formula":
                result["molecular_formula"] = val.get("sval")
            elif label == "Molecular Weight":
                result["molecular_weight"] = val.get("fval") or val.get("sval")
            elif label == "IUPAC Name" and name == "Preferred":
                result["iupac_name"] = val.get("sval")
            elif label == "InChIKey":
                result["inchi_key"] = val.get("sval")

        # Отримати CAS окремим запитом
        cas_url = f"https://pubchem.ncbi.nlm.nih.gov/rest/pug/compound/cid/{result['cid']}/property/IUPACName/JSON"
        syn_url = f"https://pubchem.ncbi.nlm.nih.gov/rest/pug/compound/cid/{result['cid']}/synonyms/JSON"
        syn_resp = httpx.get(syn_url, timeout=10)
        if syn_resp.status_code == 200:
            synonyms = syn_resp.json().get("InformationList", {}).get("Information", [{}])[0].get("Synonym", [])
            cas_numbers = [s for s in synonyms if _is_cas(s)]
            result["cas_numbers"] = cas_numbers[:3]
            result["other_names"] = [s for s in synonyms if not _is_cas(s)][:5]

        return json.dumps(result, ensure_ascii=False, indent=2)

    except Exception as e:
        return f"PubChem помилка: {str(e)}"


@tool
def search_fda_api(drug_name: str) -> str:
    """
    Шукає інформацію про реєстрацію лікарського засобу в FDA (США).
    Повертає: торгові назви, спосіб введення, форму випуску, виробника,
    статус маркетингу, дату затвердження.
    """
    try:
        url = "https://api.fda.gov/drug/ndc.json"
        params = {
            "search": f'generic_name:"{drug_name}"',
            "limit": 5
        }
        resp = httpx.get(url, params=params, timeout=15)
        if resp.status_code == 200:
            results = resp.json().get("results", [])
            if not results:
                return f"FDA NDC: '{drug_name}' не знайдено"

            output = []
            for r in results:
                entry = {
                    "brand_name":        r.get("brand_name", "—"),
                    "generic_name":      r.get("generic_name", "—"),
                    "labeler_name":      r.get("labeler_name", "—"),
                    "dosage_form":       r.get("dosage_form", "—"),
                    "route":             r.get("route", []),
                    "marketing_status":  r.get("marketing_status", "—"),
                    "product_ndc":       r.get("product_ndc", "—"),
                }
                output.append(entry)

            return json.dumps(output, ensure_ascii=False, indent=2)

        # Запасний пошук по brand_name
        params["search"] = f'brand_name:"{drug_name}"'
        resp2 = httpx.get(url, params=params, timeout=15)
        if resp2.status_code == 200:
            results2 = resp2.json().get("results", [])
            if results2:
                return json.dumps(results2[:3], ensure_ascii=False, indent=2)

        return f"FDA: '{drug_name}' не знайдено (HTTP {resp.status_code})"

    except Exception as e:
        return f"FDA API помилка: {str(e)}"


@tool
def search_chembl(compound_name: str) -> str:
    """
    Шукає фармакологічні дані в базі ChEMBL (EBI):
    механізм дії, терапевтичні мішені, клас молекули, максимальна фаза КВ.
    """
    try:
        url = "https://www.ebi.ac.uk/chembl/api/data/molecule.json"
        params = {
            "pref_name__icontains": compound_name,
            "limit": 3,
            "format": "json"
        }
        resp = httpx.get(url, params=params, timeout=15)
        if resp.status_code != 200:
            return f"ChEMBL: помилка HTTP {resp.status_code}"

        molecules = resp.json().get("molecules", [])
        if not molecules:
            return f"ChEMBL: '{compound_name}' не знайдено"

        output = []
        for m in molecules:
            output.append({
                "chembl_id":      m.get("molecule_chembl_id"),
                "pref_name":      m.get("pref_name"),
                "molecule_type":  m.get("molecule_type"),
                "max_phase":      m.get("max_phase"),
                "oral":           m.get("oral"),
                "parenteral":     m.get("parenteral"),
                "injectables":    m.get("injectables"),
                "therapeutic_flag": m.get("therapeutic_flag"),
                "mol_formula":    m.get("molecule_properties", {}).get("full_molformula"),
                "mw_freebase":    m.get("molecule_properties", {}).get("mw_freebase"),
            })

        return json.dumps(output, ensure_ascii=False, indent=2)

    except Exception as e:
        return f"ChEMBL помилка: {str(e)}"


@tool
def search_web(query: str) -> str:
    """
    Виконує веб-пошук для знаходження постачальників АФІ, цін, новин.
    Використовує Tavily API. Ідеально для пошуку B2B-постачальників,
    DMF-файлів, новин ринку.
    """
    if not TAVILY_API_KEY:
        return (
            "Tavily API ключ не налаштовано. "
            "Додайте TAVILY_API_KEY у файл .env. "
            f"Запит: {query}"
        )
    try:
        url = "https://api.tavily.com/search"
        payload = {
            "api_key": TAVILY_API_KEY,
            "query": query,
            "search_depth": "advanced",
            "max_results": 5,
            "include_answer": True,
        }
        resp = httpx.post(url, json=payload, timeout=20)
        if resp.status_code != 200:
            return f"Tavily помилка HTTP {resp.status_code}"

        data = resp.json()
        results = []

        if data.get("answer"):
            results.append(f"📌 Відповідь Tavily: {data['answer']}\n")

        for r in data.get("results", []):
            results.append(
                f"🔗 {r.get('title', '—')}\n"
                f"   URL: {r.get('url', '—')}\n"
                f"   {r.get('content', '')[:300]}..."
            )

        return "\n\n".join(results) if results else "Результатів не знайдено"

    except Exception as e:
        return f"Web search помилка: {str(e)}"


@tool
def search_drugbank_open(drug_name: str) -> str:
    """
    Шукає базові дані в відкритій частині DrugBank через PubChem SDF API.
    Повертає інформацію про фармакологічний клас, маршрут введення.
    """
    try:
        # Через PubChem Classification
        url = f"https://pubchem.ncbi.nlm.nih.gov/rest/pug/compound/name/{drug_name}/classification/JSON"
        resp = httpx.get(url, timeout=15)
        if resp.status_code != 200:
            return f"DrugBank/Classification: '{drug_name}' не знайдено"

        data = resp.json()
        hierarchies = data.get("Hierarchies", {}).get("Hierarchy", [])

        classes = []
        for h in hierarchies:
            if "DrugBank" in h.get("SourceName", "") or "ATC" in h.get("SourceName", ""):
                nodes = h.get("Node", [])
                for node in nodes[:5]:
                    name = node.get("Information", {}).get("Name", "")
                    if name:
                        classes.append(f"{h.get('SourceName')}: {name}")

        return "\n".join(classes) if classes else f"Класифікацію для '{drug_name}' не знайдено"

    except Exception as e:
        return f"Classification помилка: {str(e)}"


# ─── Допоміжні функції ───────────────────────────────────────────────────────

def _is_cas(s: str) -> bool:
    """Перевіряє чи рядок є CAS-номером (формат: XXXXXXX-XX-X)"""
    import re
    return bool(re.match(r"^\d{2,7}-\d{2}-\d$", s))


def save_report(content: str, drug_name: str) -> Path:
    """Зберігає звіт у текстовий файл"""
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    safe_name = drug_name.replace(" ", "_").replace("/", "-")[:30]
    path = REPORTS_DIR / f"report_{safe_name}_{ts}.txt"
    path.write_text(content, encoding="utf-8")
    return path


# ─── Агент ───────────────────────────────────────────────────────────────────

def build_agent() -> AgentExecutor:
    """Збирає LangChain агента з інструментами"""

    llm = ChatAnthropic(
        model="claude-sonnet-4-20250514",
        anthropic_api_key=ANTHROPIC_API_KEY,
        temperature=0,
        max_tokens=4096,
    )

    tools = [
        search_pubchem,
        search_fda_api,
        search_chembl,
        search_web,
        search_drugbank_open,
    ]

    system_prompt = """Ти — спеціалізований AI-асистент для пошуку активних фармацевтичних інгредієнтів (АФІ/API).

Твоя спеціалізація: стерильні ін'єкційні форми, поліетиленові ампули, BFS-технологія.
Компанія-клієнт: Pharmasel (Україна), виробник стерильних ін'єкцій у поліетиленових ампулах.

При отриманні запиту про АФІ обов'язково:
1. Визнач CAS-номер та молекулярну формулу (PubChem)
2. Перевір реєстраційний статус FDA (якщо є)  
3. Знайди фармакологічний клас та механізм дії (ChEMBL)
4. Знайди постачальників та ринкову інформацію (Web search)
5. Перевір класифікацію ATC/DrugBank

Формат відповіді — структурований звіт:

═══════════════════════════════════════
ЗВІТ ПО АФІ: [НАЗВА]
═══════════════════════════════════════

📌 ІДЕНТИФІКАЦІЯ
• МНН: ...
• CAS: ...
• Молекулярна формула: ...
• Молекулярна маса: ...
• ChEMBL ID: ...

💊 ФАРМАКОЛОГІЯ
• Клас молекули: ...
• Механізм дії: ...
• Терапевтичні мішені: ...
• Максимальна фаза КВ: ...
• Маршрут введення: ...

🏭 РИНОК ТА ПОСТАЧАЛЬНИКИ
• FDA статус: ...
• Відомі постачальники АФІ: ...
• Ринкова інформація: ...

⚗️ ТЕХНОЛОГІЧНІ НОТАТКИ
• Придатність для BFS-технології: ...
• Особливості виробництва: ...

─────────────────────────────────────

Якщо даних не вистачає — чітко вкажи "Дані відсутні" і не вигадуй інформацію.
Відповідай завжди українською мовою.
"""

    prompt = ChatPromptTemplate.from_messages([
        ("system", system_prompt),
        ("human", "{input}"),
        ("placeholder", "{agent_scratchpad}"),
    ])

    agent = create_tool_calling_agent(llm, tools, prompt)

    return AgentExecutor(
        agent=agent,
        tools=tools,
        verbose=True,
        max_iterations=8,
        handle_parsing_errors=True,
        return_intermediate_steps=False,
    )


# ─── CLI Інтерфейс ───────────────────────────────────────────────────────────

def main():
    print("\n" + "═"*60)
    print("  💊 API FINDER BOT — Пошук АФІ (Pharmasel)")
    print("═"*60)
    print("  Введіть назву АФІ або CAS-номер для пошуку.")
    print("  Команди: 'exit' — вихід, 'help' — довідка")
    print("═"*60 + "\n")

    if not ANTHROPIC_API_KEY:
        print("⚠️  ANTHROPIC_API_KEY не знайдено! Додайте у файл .env")
        return

    agent = build_agent()

    while True:
        try:
            query = input("🔍 Запит: ").strip()

            if not query:
                continue

            if query.lower() in ("exit", "quit", "вихід"):
                print("До побачення!")
                break

            if query.lower() in ("help", "допомога"):
                print("""
Приклади запитів:
  metformin                   → загальний звіт
  CAS 657-24-9                → пошук за CAS
  Знайди постачальників іміпенему для ін'єкцій
  Порівняй vancomycin та teicoplanin
  Знайди АФІ для BFS-ін'єкцій класу антибіотиків
""")
                continue

            print(f"\n⏳ Шукаю інформацію про '{query}'...\n")

            result = agent.invoke({"input": query})
            output = result.get("output", "Відповідь відсутня")

            print("\n" + "─"*60)
            print(output)
            print("─"*60)

            # Зберегти звіт
            report_path = save_report(output, query)
            print(f"\n💾 Звіт збережено: {report_path}\n")

        except KeyboardInterrupt:
            print("\nПерервано користувачем.")
            break
        except Exception as e:
            print(f"\n❌ Помилка: {e}\n")


if __name__ == "__main__":
    main()
