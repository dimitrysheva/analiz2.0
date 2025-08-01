import streamlit as st
import pandas as pd
import re
from collections import Counter
from io import StringIO

st.set_page_config(page_title="Аналізатор заявок", layout="wide")
st.title("📋 Аналіз аварійних заявок")

st.markdown("""
### 🔽 Встав текст таблиці (Ctrl+V з екрану)
*Скопіюй всю таблицю заявок з браузера (Ctrl+C) та встав сюди:* 
""")

raw_text = st.text_area("Встав сюди текст", height=400)

if st.button("🔍 Проаналізувати") and raw_text:
    
    # Розбиття на рядки та простий парсинг
    lines = [line.strip() for line in raw_text.splitlines() if line.strip() and 'A-' in line]
    records = []

    for line in lines:
        try:
            id_match = re.search(r'(A-\d{7})', line)
            id_ = id_match.group(1) if id_match else ""
            status = "Виконано" if "Виконано" in line else ("Відхилено" if "Відхилено" in line else ("Відмінено" if "Відмінено" in line else "Інше"))
            description = re.findall(r'\t([^\t]+)\t', line)
            
            records.append({
                "ID": id_,
                "Статус": status,
                "Опис": description[-5] if len(description) >= 5 else "",
                "Обладнання": description[-2] if len(description) >= 2 else "",
                "Виконавець": description[-1] if len(description) >= 1 else "",
            })
        except Exception as e:
            st.warning(f"Помилка парсингу рядка: {line}")

    df = pd.DataFrame(records)

    st.success(f"Знайдено {len(df)} заявок")

    col1, col2, col3 = st.columns(3)

    with col1:
        st.metric("Виконано", (df['Статус'] == "Виконано").sum())
    with col2:
        st.metric("Відхилено", (df['Статус'] == "Відхилено").sum())
    with col3:
        st.metric("Відмінено", (df['Статус'] == "Відмінено").sum())

    # ТОП-5
    def top_counts(series):
        return pd.DataFrame(Counter(series).most_common(5), columns=['Значення', 'Кількість'])

    st.markdown("### 📌 ТОП проблем / обладнання / виконавців")
    col1, col2, col3 = st.columns(3)

    with col1:
        st.write("**ТОП проблем**")
        st.dataframe(top_counts(df['Опис']))

    with col2:
        st.write("**ТОП обладнання**")
        st.dataframe(top_counts(df['Обладнання']))

    with col3:
        st.write("**ТОП виконавців**")
        st.dataframe(top_counts(df['Виконавець']))

    st.markdown("### 📄 Повна таблиця")
    st.dataframe(df, use_container_width=True)

    # Експорт
    csv = df.to_csv(index=False).encode('utf-8')
    st.download_button(
        label="📥 Завантажити CSV",
        data=csv,
        file_name='analyzed_zayavky.csv',
        mime='text/csv'
    )
