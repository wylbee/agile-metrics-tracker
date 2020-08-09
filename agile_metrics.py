# %%
import streamlit as st
import pandas as pd
import altair as alt
import psycopg2
import os
import datetime

# Connect to database and enable running of queries
# %%
db_host = os.getenv("SWA_DB_HOST")
db_port = os.getenv("SWA_DB_PORT")
db_db = os.getenv("SWA_DB_DB")
db_user = os.getenv("SWA_DB_USER")
db_pass = os.getenv("SWA_DB_PASS")

# %%
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

# Import data
df = create_df_from_query(
       """
       select
            *
       from dev_wbrown.kanban_column_status_by_hour 

       where 
        column_name not in ('[Resources]')

       """
   )

df['date_hour'] = pd.to_datetime(df['date_hour'])


# Define navigation structure


def main():

    # Multi-select category filter
    categories = list(df['column_name'].unique())
    
    filter_categories = st.multiselect('Which categories should be excluded??', options=categories, default= ['Archived', 'Done'])

    # Timeframe slider filter
    max_date_hour = df['date_hour'].max()
    min_date_hour = df['date_hour'].min()
    week_lag = 6
    week_lag_date_hour = max_date_hour + pd.DateOffset(days=(-7*week_lag))
    

    filter_min_date = st.date_input('From:', min_value=min(min_date_hour, week_lag_date_hour), max_value=max_date_hour, value=week_lag_date_hour)
    filter_max_date = st.date_input('To:', min_value=min_date_hour, max_value=max_date_hour, value=max_date_hour)

    #filtered_df = df[~df.column_name.isin(filter_categories) & df.date_hour >= filter_min_date & df.date_hour < filter_max_date]
    
    filtered_df = df.query(f'column_name != {filter_categories}')
    filtered_df = filtered_df[
        (filtered_df['date_hour'] >= pd.to_datetime(filter_min_date)) & (filtered_df['date_hour'] < pd.to_datetime(filter_max_date))
        ]

    st.altair_chart(
        alt.Chart(filtered_df, width=(140*5)).mark_area().encode(
            x="date_hour:T",
            y="count()",
            tooltip=["column_name:N","count()"],
            color="column_name:N",
            order= "hierarchy:N"
        ).properties(
            title='WIP Area Chart'
        )
    )

# Initialize app
if __name__ == "__main__":
    main()

