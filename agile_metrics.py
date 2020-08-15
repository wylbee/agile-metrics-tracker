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


df_cfd = create_df_from_query(
    """
    select
        *
    from dev_wbrown.snap_kanban_daily_flow

    where date_day >= '2020-07-06'
    """
)

df_cfd['date_day'] = pd.to_datetime(df_cfd['date_day'])

# Set theme
alt.themes.enable('latimes')


# Define navigation structure


def main():

    st.title('Agile Metrics for Personal Kanban')
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
    
    filter_dates_df_cfd = df_cfd[
        (df_cfd['date_day'] >= pd.to_datetime(filter_min_date)) & 
        (df_cfd['date_day'] <= pd.to_datetime(filter_max_date))
        ]

    # Stability calc
    mean_arrival_rate = filter_dates_df_cfd['num_arrivals'].mean()
    mean_inventory = filter_dates_df_cfd['num_inventory'].mean()
    mean_lead_time = mean_inventory/mean_arrival_rate

    # Text explanation
    st.markdown(
        f"""
        The Average Lead Time for this system is {mean_lead_time:.2f}.
        """
    )

    # Lead time

    lead_time_graph = alt.Chart(filter_dates_df_cfd, width=(140*5)).mark_line(color='#5ba3cf').encode(
            x= alt.X('date_day:T', title=''),
            y= alt.Y('avg_lead_time:Q', title='Rolling 2 week average by date'),
            tooltip=[
                alt.Tooltip("date_day:T", title='Date'),
                alt.Tooltip("avg_lead_time:Q", title= 'Avg lead time (2 week rolling)', format='.2f')
            ]
        ).transform_calculate(
            avg_lead_time='(datum.avg_daily_inventory_past_two_weeks/datum.avg_daily_arrival_past_two_weeks)'
        ).properties(
            title='Average lead time'
        )
    
    cumulative_avg_lead_time = alt.Chart(filter_dates_df_cfd).mark_rule(color='grey').encode(
        y='cumulative_avg_lead_time:Q',
        size = alt.value(2),
        tooltip= alt.Tooltip("cumulative_avg_lead_time:Q", format='.2f')
    ).transform_aggregate(
        num_records= 'distinct(date_day)',
        total_arrivals= 'sum(num_arrivals)',
        total_inventory= 'sum(num_inventory)'
    ).transform_calculate(
        cumulative_avg_lead_time = '(datum.total_inventory/datum.total_arrivals)'
    )

    st.altair_chart(lead_time_graph + cumulative_avg_lead_time)


    # WIP Graph

    wip_graph = alt.Chart(filter_dates_categories_df, width=(140*5)).mark_area().encode(
            x= alt.X("date_hour:T", title=""),
            y= alt.Y("count()", title="# of work items in Kanban column by date"),
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
                legend=alt.Legend(orient='bottom',
                title='Kanban column')
            ),
            order= alt.Order('hierarchy', sort='descending')
        ).properties(
            title='WIP area chart'
        )

    arrival_rate = alt.Chart(filter_dates_df_cfd, width=(140*5)).mark_line(interpolate='step-after', strokeDash=[1,1], color='#a778cb').encode(
            x='date_day:T',
            y='num_arrivals'
        )
    
    avg_arrival_rate = arrival_rate.mark_line(strokeDash=[10,1], color='#a778cb').transform_window(
        rolling_mean = 'mean(num_arrivals)',
        frame=[-7]
    ).encode(
        x='date_day:T',
        y='rolling_mean:Q'
    )

    inventory = alt.Chart(filter_dates_df_cfd).mark_line(interpolate='step-after', color='#f8608f', strokeDash=[1,1]).encode(
            x='date_day:T',
            y='num_inventory'
        )
    
    avg_inventory = inventory.mark_line(strokeDash=[10,1], color='#f8608f').transform_window(
        rolling_mean = 'mean(num_inventory)',
        frame=[-7]
    ).encode(
        x='date_day:T',
        y='rolling_mean:Q'
    )
    
    st.altair_chart(wip_graph + arrival_rate + avg_arrival_rate + inventory + avg_inventory)

    # CFD Graph

    st.altair_chart(alt.Chart(filter_dates_df, width=(140*5)).mark_area().encode(
            x= alt.X("date_hour:T", title=""),
            y= alt.Y("count()", title="# of work items in Kanban column by date"),
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
            title='Cumulative flow diagram'
        ).configure_legend(
            orient='bottom'
        )
    )

# Initialize app
if __name__ == "__main__":
    main()
