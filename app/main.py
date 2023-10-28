"""Frontend app to get insights from BigQuery data."""

from datetime import datetime
from datetime import timezone

import pandas as pd
import streamlit as st

from tabular_data import get_tabular_data


def convert_df(df: pd.DataFrame) -> bytes:
    """Convert a pandas DataFrame to a CSV.

    Args:
    ----
        df (pandas.DataFrame): The DataFrame to convert.

    Returns:
    -------
        bytes: The CSV.
    """
    return df.to_csv().encode("utf-8")


st.title("Get insights from your BigQuery data")
st.write("This app will help you to get insights from your data.")

if "messages" not in st.session_state:
    st.session_state.messages = []

st.write(st.session_state.messages)

for message in st.session_state.messages:
    with st.chat_message(message.get("role")):
        if message.get("role") == "assistant":
            if message.get("content").get("was_query_successfull"):
                st.write(message.get("content").get("output_message"))
                st.write(message.get("content").get("table"))
                st.download_button(
                    label="Pobierz tabele",
                    data=convert_df(message.get("content").get("table")),
                    mime="text/csv",
                    help="Pobierz powyższą tabele",
                    key=f"download_button_{message.get('id')}",
                )
            else:
                st.error(message.get("content").get("output_message"))
                st.error(f"Baza danych zwraca:\n{message.get('content').get('table')}")
            on = st.toggle(label="Zapytanie SQL", key=f"toggle_{message.get('id')}")
            if on:
                st.code(message.get("content").get("sql_query"))
        else:
            st.write(message.get("content"))

prompt = st.chat_input("What do you want to know?")

if prompt:
    # Add to storage
    st.session_state.messages.append({"role": "user", "content": prompt})

    # display message
    with st.chat_message("user"):
        st.write(prompt)

    was_query_successfull, output_message, table, sql_query = get_tabular_data(prompt)

    message_id = datetime.now(timezone.utc).strftime("%Y%m%d%H%M%S%f")

    st.session_state.messages.append(
        {
            "id": message_id,
            "role": "assistant",
            "content": {
                "was_query_successfull": was_query_successfull,
                "output_message": output_message,
                "table": table,
                "sql_query": sql_query,
            },
        },
    )

    with st.chat_message("assistant"):
        if was_query_successfull:
            st.write(output_message)
            st.write(table)
            st.download_button(
                label="Pobierz tabele",
                data=convert_df(table),
                mime="text/csv",
                help="Pobierz powyższą tabele",
                key=f"download_button_{id}",
            )
        else:
            st.error(output_message)
            st.error(table)
        on = st.toggle(label="Zapytanie SQL", key=f"toggle_{id}")
        if on:
            st.code(sql_query)
