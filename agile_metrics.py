# %%
import streamlit as st
import pandas as pd
import altair as alt
import psycopg2
import os

# Import data
db_host = os.getenv("SWA_DB_HOST")
db_port = os.getenv("SWA_DB_PORT")
db_db = os.getenv("SWA_DB_DB")
db_user = os.getenv("SWA_DB_USER")
db_pass = os.getenv("SWA_DB_PASS")


@st.cache
def create_df_from_query(sql_query):
    """
    Uses stored credentials to open a connection to the database, run a provided query, then close the connection. Returns a data frame of results.
    """
    conn = psycopg2.connect(host=db_host, port=db_port, database=db_db, user=db_user, password=db_pass)
    cur = conn.cursor()
    df = pd.read_sql_query(sql_query, conn)
    cur.close()
    conn.close()
    return df

# %%
# Define navigation structure

def main():
    raw = create_df_from_query(
        """
        select
             *

        from dev_wbrown.fct_kanban_activity

        """
    )
    st.text(raw)
    st.balloons()

# %% 
# Initialize app
if __name__ == "__main__":
    main()