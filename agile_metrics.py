# %%
import streamlit as st
import pandas as pd
import altair as alt
import psycopg2
import os


# Connect to database and enable running of queries
# %%
db_host = os.getenv("SWA_DB_HOST")
db_port = os.getenv("SWA_DB_PORT")
db_db = os.getenv("SWA_DB_DB")
db_user = os.getenv("SWA_DB_USER")
db_pass = os.getenv("SWA_DB_PASS")


#@st.cache
#def create_df_from_query(sql_query):
#    """
#    Uses stored credentials to open a connection to the database, run a provided query, then close the connection. Returns a data frame of results.
#    """
#    conn = psycopg2.connect(host=db_host, port=db_port, database=db_db, user=db_user, password=db_pass)
#    cur = conn.cursor()
#    df = pd.read_sql_query(sql_query, conn)
#    cur.close()
#    conn.close()
#    return df

# Import data
#df = create_df_from_query(
#        """
#        select
#             *
#
#        from dev_wbrown.kanban_column_status_by_minute
#        """
#    )

# Visualizations
#wip_area_chart = alt.Chart(df).mark_area().encode(
#    x="date_minute",
#    y="count()",
#    tooltip="count()",
#    color="column_name"
#)
#
# Define navigation structure

def main():
    
    #st.text(df)
    #st.altair_chart(wip_area_chart)
    st.write(db_host)
# %% 
# Initialize app
if __name__ == "__main__":
    main()
