"""
web_app.py — Streamlit веб-приложение для API Finder
===================================================
Запуск: streamlit run web_app.py
Доступно: http://localhost:8501
"""

import os
import re
import json
import streamlit as st
from pathlib import Path
from datetime import datetime
from dotenv import load_dotenv

# Импортируем функции из api_finder
from api_finder import (
    parse_input,
    pubchem_by_cas,
    pubchem_by_name,
    ai_search_suppliers,
    generate_filename,
    generate_excel,
)

load_dotenv()

# ─── КОНФИГУРАЦИЯ ────────────────────────────────────────────────────────────

HISTORY_DIR = Path("history")
HISTORY_DIR.mkdir(exist_ok=True)
HISTORY_FILE = HISTORY_DIR / "search_history.json"
REPORTS_DIR = Path("reports")
REPORTS_DIR.mkdir(exist_ok=True)

# Настройка страницы
st.set_page_config(
    page_title="API Finder",
    page_icon="🔍",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Кастомный CSS для лучшего вида
st.markdown("""
<style>
    .main {
        max-width: 1400px;
    }
    .success-box {
        background-color: #d4edda;
        border-left: 4px solid #1a6b3a;
        padding: 15px;
        border-radius: 4px;
        margin: 10px 0;
    }
    .info-box {
        background-color: #cfe2ff;
        border-left: 4px solid #0d47a1;
        padding: 15px;
        border-radius: 4px;
        margin: 10px 0;
    }
    .supplier-card {
        background-color: #f9f9f9;
        border-left: 4px solid #2E86AB;
        padding: 15px;
        border-radius: 4px;
        margin: 10px 0;
    }
</style>
""", unsafe_allow_html=True)

# ─── ФУНКЦИИ ДЛЯ РАБОТЫ С ИСТОРИЕЙ ──────────────────────────────────────────

def load_history():
    """Загружает историю из JSON файла"""
    if HISTORY_FILE.exists():
        try:
            with open(HISTORY_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except:
            return []
    return []


def save_to_history(search_data):
    """Сохраняет результат поиска в историю"""
    history = load_history()
    search_data["timestamp"] = datetime.now().isoformat()
    history.append(search_data)
    with open(HISTORY_FILE, "w", encoding="utf-8") as f:
        json.dump(history, f, ensure_ascii=False, indent=2)


def get_history_summary():
    """Возвращает краткую информацию об истории поисков"""
    history = load_history()
    return sorted(history, key=lambda x: x.get("timestamp", ""), reverse=True)


# ─── ГЛАВНЫЙ ИНТЕРФЕЙС ──────────────────────────────────────────────────────

# Заголовок приложения
st.markdown("# 🔍 API Finder")
st.markdown("### Поиск поставщиков фармацевтических субстанций и сырья для БАДов")
st.divider()

# Создаём две вкладки: Поиск и История
tab_search, tab_history = st.tabs(["🔎 Поиск", "📜 История"])

# ═══════════════════════════════════════════════════════════════════════════════
# ВКЛ. 1: ПОИСК
# ═══════════════════════════════════════════════════════════════════════════════

with tab_search:
    
    # Боковое меню
    st.sidebar.markdown("## ⚙️ Настройки")
    category = st.sidebar.radio(
        "Выберите режим поиска:",
        ["Фарма (АФИ)", "БАД (сырьё)"],
        help="""
        **Фарма (АФИ)** — активные фармацевтические ингредиенты
        Проверяет: CEP (EDQM) и GMP сертификаты
        
        **БАД (сырьё)** — сырьё для диетических добавок  
        Проверяет: ISO 22000, FSSC 22000, GMP (опционально)
        """
    )
    
    category_key = "bad" if "БАД" in category else "api"
    
    st.sidebar.divider()
    st.sidebar.markdown("### ℹ️ Информация")
    if category_key == "api":
        st.sidebar.info("""
        **Режим: Фарма (АФИ)**
        
        Проверяемые сертификаты:
        - **CEP** — Certificate of Suitability от EDQM
        - **GMP** — Good Manufacturing Practice
        """)
    else:
        st.sidebar.info("""
        **Режим: БАД (сырьё)**
        
        Проверяемые сертификаты:
        - **ISO 22000** — система менеджмента безопасности
        - **FSSC 22000** — расширенная сертификация пищевой безопасности
        - **GMP** — опциональный бонус
        """)
    
    # Основной интерфейс
    col1, col2 = st.columns([3, 1])
    
    with col1:
        st.markdown("### Введите субстанции для поиска")
        input_text = st.text_area(
            "Одна субстанция на строку (поддерживаются разные форматы):",
            placeholder="""Примеры:
• Caffeine
• CAS 58-08-2
• Caffeine (CAS 58-08-2)
• 17050-09-8
• Creatine""",
            height=150,
            label_visibility="collapsed"
        )
    
    with col2:
        st.markdown("### Поддерживаемые форматы:")
        st.markdown("""
        ✓ Просто название:
        `Caffeine`
        
        ✓ Просто CAS:
        `58-08-2`
        
        ✓ Название + CAS:
        `Caffeine (58-08-2)`
        
        ✓ С пояснением:
        `CAS 58-08-2`
        """)
    
    st.divider()
    
    # Кнопка поиска
    col_btn1, col_btn2, col_btn3 = st.columns(3)
    
    with col_btn1:
        search_button = st.button("🔍 Начать поиск", use_container_width=True, type="primary")
    
    with col_btn2:
        clear_button = st.button("🗑️ Очистить", use_container_width=True)
    
    with col_btn3:
        pass
    
    if clear_button:
        st.rerun()
    
    # ───────────────────────────────────────────────────────────────────────────
    # ОБРАБОТКА ПОИСКА
    # ───────────────────────────────────────────────────────────────────────────
    
    if search_button:
        
        if not input_text.strip():
            st.error("❌ Пожалуйста, введите хотя бы одну субстанцию!")
        else:
            
            # Парсим ввод
            substances = parse_input(input_text)
            
            if not substances:
                st.error("❌ Не удалось распознать введённые данные. Проверьте формат.")
            else:
                
                st.markdown(f"### ✅ Распознано субстанций: **{len(substances)}**")
                
                # Показываем распознанные субстанции
                with st.expander("📋 Распознанные субстанции", expanded=True):
                    for i, s in enumerate(substances, 1):
                        cas_text = f"CAS: {s['cas']}" if s['cas'] else "CAS: не указан"
                        st.markdown(f"**{i}.** {s['name']} — {cas_text}")
                
                st.divider()
                
                # Прогресс-бар и начало поиска
                st.markdown("### ⏳ Обработка...")
                progress_bar = st.progress(0)
                status_text = st.empty()
                
                all_data = []
                errors = []
                
                for i, substance in enumerate(substances):
                    # Обновляем статус
                    status_text.text(f"⏳ Обработка {i+1}/{len(substances)}: {substance['name']}")
                    
                    try:
                        # Получаем данные с PubChem
                        if substance['cas']:
                            pubchem_data = pubchem_by_cas(substance['cas'])
                        else:
                            pubchem_data = pubchem_by_name(substance['name'])
                        
                        if not pubchem_data:
                            pubchem_data = {}
                        
                        # Обновляем CAS если не был указан
                        if not substance['cas'] and pubchem_data.get('cas'):
                            substance['cas'] = pubchem_data['cas']
                        
                        # Ищем поставщиков через Claude
                        suppliers = ai_search_suppliers(
                            substance['name'],
                            substance.get('cas', '-'),
                            pubchem_data.get('formula', ''),
                            category_key
                        )
                        
                        all_data.append({
                            'name': substance['name'],
                            'cas': substance.get('cas', '-'),
                            'formula': pubchem_data.get('formula', '-'),
                            'mw': pubchem_data.get('mw', '-'),
                            'suppliers': suppliers
                        })
                        
                    except Exception as e:
                        errors.append(f"{substance['name']}: {str(e)}")
                        all_data.append({
                            'name': substance['name'],
                            'cas': substance.get('cas', '-'),
                            'formula': '-',
                            'mw': '-',
                            'suppliers': []
                        })
                    
                    # Обновляем прогресс
                    progress_bar.progress((i + 1) / len(substances))
                
                status_text.empty()
                progress_bar.empty()
                
                st.divider()
                
                # Показываем результаты
                st.markdown("### ✅ Поиск завершён!")
                
                # Статистика
                total_suppliers = sum(len(e.get('suppliers', [])) for e in all_data)
                
                if category_key == "bad":
                    iso_count = sum(1 for e in all_data for s in e.get('suppliers', []) if s.get('iso22000') is True)
                    fssc_count = sum(1 for e in all_data for s in e.get('suppliers', []) if s.get('fssc22000') is True)
                    
                    col1, col2, col3, col4 = st.columns(4)
                    with col1:
                        st.metric("Найдено субстанций", len(substances))
                    with col2:
                        st.metric("Всего поставщиков", total_suppliers)
                    with col3:
                        st.metric("С ISO 22000", iso_count)
                    with col4:
                        st.metric("С FSSC 22000", fssc_count)
                else:
                    cep_count = sum(1 for e in all_data for s in e.get('suppliers', []) if s.get('cep') is True)
                    gmp_count = sum(1 for e in all_data for s in e.get('suppliers', []) if s.get('gmp') is True)
                    
                    col1, col2, col3, col4 = st.columns(4)
                    with col1:
                        st.metric("Найдено субстанций", len(substances))
                    with col2:
                        st.metric("Всего поставщиков", total_suppliers)
                    with col3:
                        st.metric("С CEP", cep_count)
                    with col4:
                        st.metric("С GMP", gmp_count)
                
                if errors:
                    st.warning(f"⚠️ Обнаружено {len(errors)} ошибок:")
                    for err in errors:
                        st.caption(f"• {err}")
                
                st.divider()
                
                # Результаты поиска
                st.markdown("### 📊 Результаты поиска")
                
                for entry in all_data:
                    suppliers = entry.get('suppliers', [])
                    
                    if suppliers:
                        with st.expander(
                            f"🧪 **{entry['name']}** (CAS: {entry['cas']}) — {len(suppliers)} поставщиков",
                            expanded=False
                        ):
                            # Информация о субстанции
                            col1, col2 = st.columns(2)
                            with col1:
                                st.caption(f"📐 Молекулярная формула: `{entry.get('formula', '-')}`")
                            with col2:
                                st.caption(f"⚖️ Молекулярная масса: `{entry.get('mw', '-')}`")
                            
                            st.markdown("---")
                            
                            # Таблица поставщиков
                            suppliers_data = []
                            for sup in suppliers:
                                if category_key == "bad":
                                    suppliers_data.append({
                                        "Поставщик": sup.get('name', '-'),
                                        "Страна": sup.get('country', '-'),
                                        "Контакт": sup.get('contact', '-'),
                                        "ISO 22000": "✅" if sup.get('iso22000') is True else ("❌" if sup.get('iso22000') is False else "❓"),
                                        "GMP": "✅" if sup.get('gmp') is True else ("❌" if sup.get('gmp') is False else "❓"),
                                        "FSSC 22000": "✅" if sup.get('fssc22000') is True else ("❌" if sup.get('fssc22000') is False else "❓"),
                                    })
                                else:
                                    suppliers_data.append({
                                        "Поставщик": sup.get('name', '-'),
                                        "Страна": sup.get('country', '-'),
                                        "Контакт": sup.get('contact', '-'),
                                        "CEP": "✅" if sup.get('cep') is True else ("❌" if sup.get('cep') is False else "❓"),
                                        "GMP": "✅" if sup.get('gmp') is True else ("❌" if sup.get('gmp') is False else "❓"),
                                    })
                            
                            st.dataframe(suppliers_data, use_container_width=True, hide_index=True)
                    else:
                        st.warning(f"❌ **{entry['name']}** — поставщики не найдены")
                
                st.divider()
                
                # Скачивание файлов
                st.markdown("### 📥 Скачивание отчётов")
                
                # Генерируем Excel
                filename = generate_filename(substances, category_key)
                output_path = REPORTS_DIR / filename
                
                try:
                    generate_excel(all_data, str(output_path), category_key)
                    
                    with open(output_path, 'rb') as f:
                        excel_data = f.read()
                    
                    # Генерируем JSON
                    json_data = json.dumps(all_data, ensure_ascii=False, indent=2).encode('utf-8')
                    
                    col1, col2, col3 = st.columns(3)
                    
                    with col1:
                        st.download_button(
                            label="📊 Скачать Excel отчёт",
                            data=excel_data,
                            file_name=filename,
                            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                            use_container_width=True
                        )
                    
                    with col2:
                        st.download_button(
                            label="📄 Скачать JSON",
                            data=json_data,
                            file_name=filename.replace('.xlsx', '.json'),
                            mime="application/json",
                            use_container_width=True
                        )
                    
                    with col3:
                        # Сохраняем в историю
                        search_data = {
                            "category": category,
                            "substances": substances,
                            "results": all_data,
                            "filename": filename,
                            "total_suppliers": total_suppliers
                        }
                        save_to_history(search_data)
                        st.success("✅ Результат сохранён в историю")
                    
                except Exception as e:
                    st.error(f"❌ Ошибка при генерации файлов: {str(e)}")


# ═══════════════════════════════════════════════════════════════════════════════
# ВКЛ. 2: ИСТОРИЯ
# ═══════════════════════════════════════════════════════════════════════════════

with tab_history:
    
    st.markdown("### 📜 История поисков")
    
    history = get_history_summary()
    
    if not history:
        st.info("📭 История пока пуста. Выполните поиск на вкладке 'Поиск'.")
    else:
        st.markdown(f"**Всего поисков:** {len(history)}")
        st.divider()
        
        # Опция для очистки истории
        col1, col2 = st.columns([3, 1])
        with col2:
            if st.button("🗑️ Очистить историю", use_container_width=True):
                with open(HISTORY_FILE, 'w', encoding='utf-8') as f:
                    json.dump([], f)
                st.rerun()
        
        # Показываем историю в обратном порядке (самые свежие первыми)
        for idx, search in enumerate(history):
            timestamp = search.get('timestamp', 'Unknown')
            category = search.get('category', 'Unknown')
            substances = search.get('substances', [])
            results = search.get('results', [])
            total_suppliers = search.get('total_suppliers', 0)
            
            # Парсим дату
            try:
                dt = datetime.fromisoformat(timestamp)
                date_str = dt.strftime("%d.%m.%Y %H:%M:%S")
            except:
                date_str = timestamp
            
            with st.expander(
                f"📅 {date_str} — **{category}** ({len(substances)} субстанций, {total_suppliers} поставщиков)",
                expanded=False
            ):
                # Информация о поиске
                col1, col2, col3 = st.columns(3)
                with col1:
                    st.metric("Субстанций", len(substances))
                with col2:
                    st.metric("Поставщиков", total_suppliers)
                with col3:
                    st.metric("Файл", search.get('filename', '-')[:30])
                
                st.markdown("---")
                
                # Список субстанций
                st.markdown("**Субстанции в этом поиске:**")
                for sub in substances:
                    st.caption(f"• {sub['name']} (CAS: {sub.get('cas', '-')})")
                
                st.markdown("---")
                
                # Результаты
                st.markdown("**Результаты:**")
                for entry in results:
                    suppliers = entry.get('suppliers', [])
                    suppliers_text = ", ".join([s.get('name', 'Unknown')[:30] for s in suppliers])
                    st.caption(f"🧪 **{entry['name']}** → {suppliers_text or 'нет поставщиков'}")
        
        st.divider()
        st.info("💡 Нажмите на любой поиск выше, чтобы развернуть полную информацию")

# ─── ПОДВАЛ ──────────────────────────────────────────────────────────────────

st.divider()

col1, col2, col3 = st.columns(3)

with col1:
    st.caption("🔍 API Finder v1.0")

with col2:
    st.caption(f"📊 Всего поисков: {len(get_history_summary())}")

with col3:
    st.caption(f"⏰ {datetime.now().strftime('%d.%m.%Y %H:%M')}")
