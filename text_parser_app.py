import streamlit as st
import pandas as pd
import re
from io import StringIO, BytesIO
import plotly.express as px
import openpyxl

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


# --- Функція-парсер для вставлених даних ---
def parse_pasted_data(text_data):
    """
    Розбирає вставлений текст, витягуючи дані з кожної заявки.
    """
    records = re.split(r'(A-\d{6,})', text_data)
    records = [records[i] + records[i+1] for i in range(1, len(records), 2)]

    parsed_data = []

    for record in records:
        record = record.replace('\n', '')

        id_match = re.search(r'^(A-\d{6,})', record)
        if not id_match:
            continue
        id_val = id_match.group(1)

        remaining_text = record[len(id_val):].strip()
        type_val = ""
        status_val = ""
        date_time_exec_val = ""
        time_diff_val = ""
        downtime_val = ""
        description_val = ""
        report_val = ""
        цех_val = ""
        department_val = ""
        line_val = ""
        equipment_val = ""
        date_time_create_val = ""
        author_val = ""
        service_val = ""
        executor_val = ""

        # Вид заявки та Статус
        match_type_status = re.search(r'^(.*?)(?:-Відмінено|-Відхилено|Виконано|Чекає підтвердження|В роботі)', remaining_text)
        if match_type_status:
            type_val = match_type_status.group(1).strip()
            if type_val.startswith("Простій РЦ"): type_val = "Простій РЦ"
            elif type_val.startswith("Простій"): type_val = "Простій"
            remaining_text = remaining_text[len(match_type_status.group(0)):].strip()
            status_match = re.search(r'(-Відмінено|-Відхилено|Виконано|Чекає підтвердження|В роботі)', match_type_status.group(0))
            status_val = status_match.group(1).strip() if status_match else ""

        # Дата і час виконання
        date_time_exec_match = re.search(r'(\d{2}\.\d{2}\.\d{4},\s\d{2}:\d{2})', remaining_text)
        date_time_exec_val = date_time_exec_match.group(1) if date_time_exec_match else ""

        # Час заявки та Простій
        time_diff_match = re.search(r'-([\d\s\w]+)', remaining_text)
        time_diff_val = time_diff_match.group(1).strip() if time_diff_match else ""
        downtime_match = re.search(r'(\d+\sхв|\d+\sгод\s\d+\sхв)', remaining_text)
        downtime_val = downtime_match.group(1) if downtime_match else ""

        # Решта інформації
        full_info_match = re.search(r'(?:Виконано|Відмінено|Відхилено|Чекає підтвердження|В роботі)(.*?)(\d{2}\.\d{2}\.\d{4},\s\d{2}:\d{2})', record)
        if full_info_match:
            middle_part = full_info_match.group(1).strip()
            цех_match = re.search(r'(Цех [^\s]+)', middle_part)
            цех_val = цех_match.group(1) if цех_match else ""
            
            description_and_report_match = re.search(r'(?:хв|\w{2,})(.*?)(Цех [^\s]+)', middle_part)
            if description_and_report_match:
                description_and_report_text = description_and_report_match.group(1).strip()
                report_match = re.search(r'Ревізія|Заміна|Налаштування|Усунено|Перевірка|Відновлення|Перезавантажили|Видалення|Змащення|Пошук|Перероблено|Поміч|Допомога', description_and_report_text)
                if report_match:
                    description_val = description_and_report_text[:report_match.start()].strip()
                    report_val = description_and_report_text[report_match.start():].strip()
                else:
                    description_val = description_and_report_text
                    report_val = ""
            
            department_match = re.search(r'(Дільниця [^\s]+)', middle_part)
            department_val = department_match.group(1) if department_match else ""
            line_match = re.search(r'(Лінія [^\s]+)', middle_part)
            line_val = line_match.group(1) if line_match else ""
            equipment_match = re.search(r'(Машина|Металодетектор|Транспортер|Пакувальна машина|Кліпсатор|Конвеєр|Ваги)[^,]+', middle_part)
            equipment_val = equipment_match.group(0).strip() if equipment_match else ""
            date_time_create_match = re.search(r'(\d{2}\.\d{2}\.\d{4},\s\d{2}:\d{2})', record)
            date_time_create_val = date_time_create_match.group(1) if date_time_create_match else ""
            author_match = re.search(r'(\d{2}:\d{2})(\s*[А-ЯЇЄІҐ][а-яїєіґ]+(?:\s+[А-ЯЇЄІҐ][а-яїєіґ]+)?)', remaining_text)
            author_val = author_match.group(2).strip() if author_match else ""
            service_match = re.search(r'(Служба [^\s]+(?: [^\s]+)*)', remaining_text)
            service_val = service_match.group(1).strip() if service_match else ""
            executor_match = re.search(r'(?:Служби?.*?)(\s*[А-ЯЇЄІҐ][а-яїєіґ]+(?:\s+[А-ЯЇЄІҐ][а-яїєіґ]+)?)', remaining_text)
            executor_val = executor_match.group(1).strip() if executor_match else ""
            
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


# --- Основний інтерфейс ---
pasted_data = st.text_area("📋 Вставте дані сюди", height=300, help="Виділіть і скопіюйте дані зі сторінки, а потім вставте сюди.")

if pasted_data:
    try:
        df = parse_pasted_data(pasted_data)
        
        if df.empty:
            st.warning("⚠️ Не вдалося розпізнати жодної заявки. Перевірте, чи дані скопійовані правильно.")
        else:
            st.success(f"✅ Успішно розпізнано {len(df)} заявок.")

            # Обробка даних для аналізу
            df['Дата і час створення'] = pd.to_datetime(df['Дата і час створення'], format='%d.%m.%Y, %H:%M', errors='coerce')
            df['Дата і час виконання'] = pd.to_datetime(df['Дата і час виконання'], format='%d.%m.%Y, %H:%M', errors='coerce')
            df['Час до виконання (хв)'] = (df['Дата і час виконання'] - df['Дата і час створення']).dt.total_seconds() / 60

            # Видалення порожніх стовпців для чистоти
            df.dropna(axis=1, how='all', inplace=True)
            
            # --- Виведення таблиці ---
            st.subheader("📋 Розпізнана таблиця")
            st.dataframe(df, use_container_width=True)

            # --- Виведення аналітики ---
            st.subheader("📊 Аналітика даних")
            
            # Середній час до виконання
            avg_execution_time = df['Час до виконання (хв)'].mean()
            if pd.notna(avg_execution_time):
                st.metric("Середній час до виконання", f"{avg_execution_time:.1f} хв")
            
            # Графік заявок по цехах
            if 'Цех' in df.columns:
                department_counts = df['Цех'].value_counts().reset_index()
                fig_departments = px.bar(
                    department_counts, 
                    x='Цех', 
                    y='count',
                    title='Кількість заявок по цехах',
                    labels={'count': 'Кількість заявок'}
                )
                st.plotly_chart(fig_departments, use_container_width=True)
            
            # --- Кнопка для завантаження ---
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
