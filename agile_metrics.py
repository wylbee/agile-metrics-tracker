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

       where column_name not in ('[Resources]')

       """
   )

df['date_hour'] = pd.to_datetime(df['date_hour'])


# Set theme
alt.themes.enable('latimes')


# Define navigation structure


def main():

    # Multi-select category filter
    categories = list(df['column_name'].unique())
    
    filter_categories = st.multiselect('Which categories should be excluded?', options=categories, default= ['Archived', 'Done'])

    # Timeframe slider filter
    max_date_hour = df['date_hour'].max() + pd.DateOffset(days=2)
    min_date_hour = df['date_hour'].min()
    week_lag = 6
    week_lag_date_hour = max_date_hour + pd.DateOffset(days=(-7*week_lag))
    
    filter_min_date = st.date_input('From:', min_value=min(min_date_hour, week_lag_date_hour), max_value=max_date_hour, value=week_lag_date_hour)
    filter_max_date = st.date_input('To:', min_value=min_date_hour, max_value=max_date_hour, value=max_date_hour)

    # Apply filters
    
    filter_dates_df = df[
        (df['date_hour'] >= pd.to_datetime(filter_min_date)) & 
        (df['date_hour'] <= pd.to_datetime(filter_max_date))
        ]
    filter_dates_categories_df = filter_dates_df.query(f'column_name != {filter_categories}')
    

    # WIP Graph

    st.altair_chart(
        alt.Chart(filter_dates_categories_df, width=(140*5)).mark_area().encode(
            x= alt.X("date_hour:T", title=""),
            y= alt.Y("count()", title="# of work items by Kanban column"),
            tooltip=[
                alt.Tooltip("date_hour:T", title= 'Date/time'),
                alt.Tooltip("column_name:N", title='Kanban column'),
                alt.Tooltip("count()", title='# of work items')
            ],
            color= alt.Color(
                "column_name:O", 
                sort=alt.SortField("hierarcy", order="descending"),
                scale=alt.Scale(
                    domain=['Archived', 'Backlog', 'Analysis', 'Ready for Work', 'Execute', 'Verify', 'Done'],
                    range=['#4d4d4d', '#c4c4c4', '#f87f2c', '#9d9d9d', '#86bcdc', '#3887c0', '#757575']
                ),
                title='Kanban column'
            ),
            order= alt.Order('hierarchy', sort='descending')
        ).properties(
            title='WIP area chart'
        ).configure_legend(
            orient='bottom'
        )
    )

    # CFD Graph

    st.altair_chart(
        alt.Chart(filter_dates_df, width=(140*5)).mark_area().encode(
            x= alt.X("date_hour:T", title=""),
            y= alt.Y("count()", title="# of work items by Kanban column"),
            tooltip=[
                alt.Tooltip("column_name:N", title='Kanban column'),
                alt.Tooltip("count()", title='# of work items')
            ],
            color= alt.Color(
                "column_name:O", 
                sort=alt.SortField("hierarcy", order="descending"),
                scale=alt.Scale(
                    domain=['Archived', 'Backlog', 'Analysis', 'Ready for Work', 'Execute', 'Verify', 'Done'],
                    range=['#4d4d4d', '#c4c4c4', '#f87f2c', '#9d9d9d', '#86bcdc', '#3887c0', '#757575']
                ),
                title='Kanban column'
            ),
            order= alt.Order('hierarchy', sort='descending')
        ).properties(
            title='Cumulative Flow Diagram'
        ).configure_legend(
            orient='bottom'
        )
    )

# Initialize app
if __name__ == "__main__":
    main()
