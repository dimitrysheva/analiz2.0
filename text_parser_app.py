import streamlit as st
import pandas as pd
import re
from io import StringIO, BytesIO
import plotly.express as px
import openpyxl
import numpy as np

st.set_page_config(layout="wide", page_title="Аналізатор даних з тексту", page_icon="📝")

st.title("📝 Аналізатор даних з тексту")

st.markdown("""
    Ця програма призначена для швидкого аналізу даних з заявок, скопійованих
    прямо зі сторінки.

    **Інструкція:**
    1. Перейдіть на сторінку з даними заявок.
    2. Виділіть весь вміст сторінки (наприклад, натиснувши **`Ctrl+A`**).
    3. Скопіюйте виділений вміст у буфер обміну (**`Ctrl+C`**).
    4. Вставте текст у поле нижче (**`Ctrl+V`**).

    Програма автоматично розпізнає та структурує дані у таблицю для аналізу.
""")

def convert_downtime_to_minutes(downtime_text):
    if not isinstance(downtime_text, str) or downtime_text.strip() == "":
        return np.nan
    
    total_minutes = 0
    downtime_text = downtime_text.strip()
    
    days_match = re.search(r'(\d+)\s*день', downtime_text)
    hours_match = re.search(r'(\d+)\s*год', downtime_text)
    minutes_match = re.search(r'(\d+)\s*хв', downtime_text)
    
    if days_match:
        total_minutes += int(days_match.group(1)) * 24 * 60
    if hours_match:
        total_minutes += int(hours_match.group(1)) * 60
    if minutes_match:
        total_minutes += int(minutes_match.group(1))
        
    return total_minutes

def parse_pasted_data(text_data):
    records = re.split(r'(A-\d{6,})', text_data)
    records = [records[i] + records[i+1] for i in range(1, len(records), 2)]
    
    parsed_data = []

    for record in records:
        record = record.replace('\n', ' ')

        # ID
        id_match = re.search(r'^(A-\d{6,})', record)
        if not id_match:
            continue
        id_val = id_match.group(1)
        remaining_text = record[len(id_val):].strip()

        # Статус
        status_val = ""
        status_match = re.search(r'(-Відмінено|-Відхилено|Виконано|Чекає підтвердження|В роботі)', remaining_text)
        if status_match:
            status_val = status_match.group(1).strip()
            
        # Вид заявки
        type_val = ""
        type_match = re.search(r'^(.*?)(?:-Відмінено|-Відхилено|Виконано|Чекає підтвердження|В роботі)', remaining_text)
        if type_match:
            type_val = type_match.group(1).strip()
            if type_val.startswith("Простій РЦ"): type_val = "Простій РЦ"
            elif type_val.startswith("Простій"): type_val = "Простій"
        
        # Дати
        dates_match = re.findall(r'(\d{2}\.\d{2}\.\d{4},\s\d{2}:\d{2})', record)
        date_time_exec_val = dates_match[0] if len(dates_match) > 0 else ""
        date_time_create_val = dates_match[-1] if len(dates_match) > 1 else ""

        # Простій (текст)
        downtime_val = ""
        # Шукаємо час простою, який йде після іншого часу
        downtime_match = re.search(r'(?:-[\d\s\w]+хв)?\s*?([\d\s\w]+хв)', remaining_text)
        if downtime_match:
            downtime_val = downtime_match.group(1).strip()
        else:
            # Якщо простій один, то витягуємо його
            downtime_match = re.search(r'([\d\s\w]+хв)', remaining_text)
            if downtime_match:
                downtime_val = downtime_match.group(1).strip()
        
        # Опис та Звіт виконання (витягуємо блок між часом і цехом)
        description_and_report = ""
        start_index = record.find(downtime_val) + len(downtime_val) if downtime_val else 0
        end_index = record.find('Цех')
        if start_index < end_index:
            description_and_report = record[start_index:end_index].strip()
        
        description_val = ""
        report_val = ""
        report_keywords = "Ревізія|Заміна|Налаштування|Усунено|Перевірка|Відновлення|Перезавантажили|Видалення|Змащення|Пошук|Перероблено|Поміч|Допомога"
        report_match = re.search(report_keywords, description_and_report)
        if report_match:
            description_val = description_and_report[:report_match.start()].strip()
            report_val = description_and_report[report_match.start():].strip()
        else:
            description_val = description_and_report

        # Пошук ключових слів
        цех_val = ""
        цех_match = re.search(r'(Цех [^\s]+|Кулінарний цех)', record)
        if цех_match:
            цех_val = цех_match.group(0).strip()
        
        department_val = ""
        department_match = re.search(r'(Дільниця [^\s]+(?: [^\s]+)*)', record)
        if department_match:
            department_val = department_match.group(0).strip()

        line_val = ""
        line_match = re.search(r'(Лінія [^\s]+(?: [^\s]+)*)', record)
        if line_match:
            line_val = line_match.group(0).strip()

        equipment_val = ""
        equipment_match = re.search(r'(Машина|Металодетектор|Транспортер|Пакувальна машина|Кліпсатор|Конвеєр|Ваги)[^,]+', record)
        if equipment_match:
            equipment_val = equipment_match.group(0).strip()
        
        author_val = ""
        author_match = re.search(r'(\d{2}:\d{2})([\sА-ЯІЄЇҐ][а-яіїєґ]+(?:\s[А-ЯІЄЇҐ][а-яіїєґ]+)?)', record)
        if author_match:
            author_val = author_match.group(2).strip()

        service_val = ""
        service_match = re.search(r'Служба\s*?(Служба [^\s]+(?: [^\s]+)*)', record)
        if service_match:
            service_val = service_match.group(1).strip()
        
        executor_val = ""
        executor_match = re.search(r'Виконавець\s*?([\sА-ЯІЄЇҐ][а-яіїєґ]+(?:\s+[А-ЯІЄЇҐ][а-яіїєґ]+)*)', record)
        if executor_match:
            executor_val = executor_match.group(1).strip()
        
        parsed_data.append({
            "Ідентифікатор": id_val,
            "Вид заявки": type_val,
            "Дата і час виконання": date_time_exec_val,
            "Статус": status_val,
            "Опис": description_val,
            "Звіт виконання": report_val,
            "Простій (текст)": downtime_val,
            "Цех": цех_val,
            "Дільниця": department_val,
            "Лінія": line_val,
            "Обладнання": equipment_val,
            "Дата і час створення": date_time_create_val,
            "Автор": author_val,
            "Служба": service_val,
            "Виконавець": executor_val,
        })
    return pd.DataFrame(parsed_data)

pasted_data = st.text_area("📋 Вставте дані сюди", height=300, help="Виділіть і скопіюйте дані зі сторінки, а потім вставте сюди.")

if pasted_data:
    try:
        df = parse_pasted_data(pasted_data)
        
        if df.empty:
            st.warning("⚠️ Не вдалося розпізнати жодної заявки. Перевірте, чи дані скопійовані правильно.")
        else:
            st.success(f"✅ Успішно розпізнано {len(df)} заявок.")

            st.subheader("📋 Розпізнана таблиця")
            st.dataframe(df, use_container_width=True)

            st.subheader("📊 Аналітика даних (тільки виконані заявки)")
            
            df_executed = df[df['Статус'] == 'Виконано'].copy()
            
            if not df_executed.empty and 'Простій (текст)' in df_executed.columns:
                df_executed['Простій (хв)'] = df_executed['Простій (текст)'].apply(convert_downtime_to_minutes)
                
                avg_downtime = df_executed['Простій (хв)'].mean()
                if pd.notna(avg_downtime):
                    st.metric("Середній час простою", f"{avg_downtime:.1f} хв")
                else:
                    st.info("Недостатньо даних для розрахунку середнього часу простою.")
            else:
                st.info("Немає виконаних заявок для аналітики.")
            
            if 'Цех' in df_executed.columns:
                department_counts = df_executed['Цех'].value_counts().reset_index()
                if not department_counts.empty:
                    fig_departments = px.bar(
                        department_counts, 
                        x='Цех', 
                        y='count',
                        title='Кількість заявок по цехах (тільки виконані)',
                        labels={'count': 'Кількість заявок'}
                    )
                    st.plotly_chart(fig_departments, use_container_width=True)
            
            @st.cache_data
            def convert_df_to_excel(df_to_convert):
                output = BytesIO()
                df_to_convert.to_excel(output, index=False, engine='openpyxl')
                processed_data = output.getvalue()
                return processed_data

            st.download_button(
                label="⬇️ Завантажити дані як Excel",
                data=convert_df_to_excel(df),
                file_name=f'аналіз_заявок_з_тексту_{pd.Timestamp.now().strftime("%Y-%m-%d")}.xlsx',
                mime='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
                help='Завантажити оброблену таблицю у форматі Excel'
            )

    except Exception as e:
        st.error(f"❌ Виникла помилка під час обробки даних: {e}")
        st.info("Будь ласка, перевірте, чи формат вставлених даних відповідає прикладу.")
else:
    st.info("⬆️ Будь ласка, вставте дані, щоб розпочати аналіз.")
