# dash and plotly
from dash import Dash, html, dcc, Input, Output
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots

# data
import pandas as pd
import numpy as np
from dateutil.parser import parse

DOW_dict = {"Monday": 0,
           "Tuesday": 1,
           "Wednesday": 2,
           "Thursday": 3,
           "Friday": 4,
           "Saturday": 5,
           "Sunday": 6}

# Result color map
result_colors = {
              "Total": "blue",
              "No Response": "salmon",  
              "Rejected": "crimson",
              "Contacted": "gold",
              "First Interview": "seagreen",
              "Second Intervew": "mediumseagreen",
              "Third Interview": "mediumaquamarine",
              "Offer": "lime",
              "Scam": "purple"
}

# read in data
df = pd.read_csv("scratch/Application_Results_12_31_2022.csv", index_col=0)

# vertical lines for time series
resume_dates = ["2022-08-12", "2022-08-19", "2022-08-31", "2022-09-05"]
interview_dates = df["Date_Applied"][df["Result"].str.contains("(?i)Interview")].values
offer_dates = df["Date_Applied"][df["Result"].str.contains("Offer")].values

# convert Date_Applied column to datetime
df["Date_Applied"] = pd.to_datetime(df["Date_Applied"])

date_count = df.groupby("Date_Applied").size().reindex(pd.date_range(df["Date_Applied"].min(), df["Date_Applied"].max()), fill_value=0)

def create_role_fig(dff):
    # bar graph role groupby
    role_group = dff.groupby(["Broad_Role", "Result"]).size().unstack()

    role_group["Total"] = role_group.sum(axis=1)

    role_group_to_bar = role_group.assign(temp_sum=role_group.sum(axis=1)) \
        .sort_values(by="temp_sum", ascending=False).iloc[:,:-1] \
        .reindex(role_group.mean(axis=0).sort_values(ascending=False).index, axis=1)

    role_group_fig = px.bar(role_group_to_bar,
                barmode="group",
                color_discrete_map=result_colors,
                labels=dict(Broad_Role="Broad Role Category", 
                            value="# of Applications"),
                title="Application Results by Role Category"
                )
    
    role_group_fig.update_layout(plot_bgcolor=bg_color, paper_bgcolor=bg_color)
    
    return role_group_fig, role_group_to_bar
    
def create_time_series_fig(dff):    
    
    time_series_fig = make_subplots(specs=[[{"secondary_y": True}]])

    time_series_fig.add_bar(x=date_count.index, y=date_count.values, name="Daily Count", secondary_y=False)

    time_series_fig.add_scatter(x=date_count.cumsum().index, y=date_count.cumsum().values, name="Cumulative Count", fillcolor="orange", secondary_y=True)

    time_series_fig.update_layout(yaxis_range=[date_count.min(),date_count.max()+1], title_text="Applications Over Time",plot_bgcolor=bg_color, paper_bgcolor=bg_color)
    time_series_fig.update_yaxes(title_text="# of Applications Per Day", secondary_y=False)
    time_series_fig.update_yaxes(title_text="Cumulative # of Applications", secondary_y=True)

    for i, x in enumerate(resume_dates):
    #time_series_fig.add_vline(x=str(x), line_width=1, line_dash="dash", line_color="red")
        time_series_fig.add_trace(go.Scatter(x=[str(x),str(x)], 
                             y=[date_count.min(),date_count.max()+1], 
                             mode='lines', 
                             line=dict(color='red', width=2, dash='dash'),
                             name="Resume Updated",
                             legendgroup="Resume Updated",
                             showlegend=False if i > 0 else True))

    for i, x in enumerate(interview_dates):
    #time_series_fig.add_vline(x=str(x), line_width=1, line_dash="dashdot", line_color="green")
        time_series_fig.add_trace(go.Scatter(x=[str(x),str(x)], 
                             y=[date_count.min(),date_count.max()+1], 
                             mode='lines', 
                             line=dict(color='green', width=1, dash='dashdot'),
                             name="Application(s) Led to Interview",
                             legendgroup="Application(s) Led to Interview",
                             showlegend=False if i > 0 else True))

    for i, x in enumerate(offer_dates):
    #time_series_fig.add_vline(x=str(x), line_width=1, line_dash="longdashdot", line_color="black")
        time_series_fig.add_trace(go.Scatter(x=[str(x),str(x)], 
                         y=[date_count.min(),date_count.max()+1], 
                         mode='lines', 
                         line=dict(color='black', width=1, dash='longdashdot'),
                         name="Application(s) Led to Offer",
                         legendgroup="Application(s) Led to Offer",
                         showlegend=False if i > 0 else True))
    
    
    
    return time_series_fig
    
def create_pie_fig(dff, rgroup):  
    cats = ["Overall"] + list(rgroup.index)

    pie_fig = make_subplots(2, 3, subplot_titles=[cat + " Applications" for cat in cats], specs=[[{'type':'domain'}]*(len(cats) // 2), [{'type':'domain'}]*(len(cats) // 2)])

    s = pd.Series(result_colors).drop("Total").reindex(rgroup.drop("Total", axis=1).columns)

    i, j = 1, 1
    for pie_category in cats:

        pie_category = pie_category if pie_category is not None else "Overall"

        if pie_category == "Overall":
            pie_fig.add_trace(go.Pie(values=dff["Result"].value_counts(), 
                        labels=dff["Result"].value_counts().index,
                        marker=dict(colors=s.reindex(dff["Result"].value_counts().index)),
                        scalegroup='one',
                        hole=0.4,
                        name=""), i, j) 
        else:
            pie_cat_dff = dff[dff["Broad_Role"] == pie_category]

            pie_fig.add_trace(go.Pie(values=pie_cat_dff["Result"].value_counts(), 
                    labels=pie_cat_dff["Result"].value_counts().index,
                    scalegroup='one',
                    marker=dict(colors=s.reindex(pie_cat_dff["Result"].value_counts().index)),
                    hole=0.4,
                    name=""), i, j) # donut

        # update text labels on pie slices
        pie_fig.update_traces(textinfo="value+percent", texttemplate="(%{value})<br>%{percent}")

        i = i if j < 3 else 2
        j = j + 1 if j < 3 else 1

    pie_fig.update_layout(height=800, title_text='Overall Results of Applications', font=dict(size=10), plot_bgcolor=bg_color, paper_bgcolor=bg_color)
    
    #pie_fig = px.pie(dff, values=dff["Result"].value_counts(), names=dff["Result"].value_counts().index,
    #                color=dff["Result"].value_counts().index,
    #                color_discrete_map=result_colors)    

    #pie_fig.update_layout(title=dict(text="Overall Applications", xanchor="center", x=0.5), font=dict(size=12))

    return pie_fig
    
# dow
def create_dow_fig(dff):       
    dow_group = dff.groupby(["DOW", "Result"]).size().unstack() \
                .sort_index(key=lambda d: d.map(DOW_dict)) \

    dow_group["Total"] = dow_group.sum(axis=1)

    dow_group = dow_group.reindex(dow_group.mean(axis=0) \
                .sort_values(ascending=False).index, axis=1)

    dow_fig = px.bar(dow_group,
                barmode="group",
                color_discrete_map=result_colors,
                labels=dict(DOW="Day of Application", 
                            value="# of Applications"),
                title="Application Results by Day of the Week"
                )   
    
    dow_fig.update_layout(plot_bgcolor=bg_color, paper_bgcolor=bg_color)
    
    return dow_fig

# month
def create_month_fig(dff):
    month_group = dff.groupby(["year_month", "Result"]).size().unstack()

    month_group["Total"] = month_group.sum(axis=1)

    month_group = month_group.reindex(month_group.mean(axis=0) \
                  .sort_values(ascending=False).index, axis=1)

    month_fig = px.bar(month_group,
                barmode="group",
                color_discrete_map=result_colors,
                labels=dict(year_month="Month", 
                            value="# of Applications"),
                title="Application Results by Month"
                )  

    month_fig.update_xaxes(
    dtick="M1",
    tickformat="%b %Y")  
    
    month_fig.update_layout(plot_bgcolor=bg_color, paper_bgcolor=bg_color)
    
    return month_fig

# use background color from App.css
bg_color = "#DDC3F8"

role_fig, role_group = create_role_fig(df)

app = Dash(__name__)

app.title = "Journey to an Entry-Level Job"  

app.layout = html.Div(children=[
    html.H1(children='Journey to an Entry-Level Job'),

    html.Div(children=[
        html.H2("""Background"""),
        
        html.P("""bigman""")
    
    ], className="page-container"),
    
    html.Div(children=[
        html.H2("""Examining Applications over Time"""),
        
        html.P("""The date range of applications I will look at is 08/09/2022 to 12/31/2022, bigman"""),
        
        dcc.Graph(
            id='time-series',
            figure=create_time_series_fig(df)
        )
    
    ], className="page-container"),
    
    html.Div(children=[
        html.H2("""Examining Applications by Month"""),
        
        # "error loading layout": plotly doesn't like Period type for time?
        dcc.Graph(
            id='month-groups',
            figure=create_month_fig(df)
        )
    ], className="page-container"),
    
    html.Div(children=[
        html.H2("""Examining Applications by Days of the Week"""),
        
        dcc.Graph(
            id='dow-groups',
            figure=create_dow_fig(df)
        )
    ], className="page-container"),
    
    html.Div(children=[
        html.H2("""Examining Applications by Role"""),

        dcc.Graph(
            id='role-groups',
            figure=role_fig
        )
    ], className="page-container"),
    
    html.Div(children=[
        html.H2("""Overall Results of Applications"""),
        
        html.P("""guy"""),
        
        
        #html.Div(children=[
        #    html.H4("""Role Category Dropdown"""),

            #dcc.Dropdown(
            #    ["Overall"] + list(role_group.index),
            #    'Overall',
            #    id='pie-cats'
            #),
                        
        #], style={'width': '25%'}),
        
        dcc.Graph(
            id='results-pie',
            figure=create_pie_fig(df, role_group)
        )
    ], className="page-container"),
        
    html.Div(children=[
        html.H2("""In Conclusion..."""),
        
        html.P(""" """)
    ], className="page-container")
])

# callback decorator
# callback not available for static page
#@app.callback(
#    Output('results-pie', 'figure'),
#    Input('pie-cats', 'value'))
#def update_pie(pie_category):   
#    pie_category = pie_category if pie_category is not None else "Overall"
#    
#    # default to overall if clearing the dropdown
#    if pie_category == "Overall":
#        fig = px.pie(df, values=df["Result"].value_counts(), names=df["Result"].value_counts().index,
#                color=df["Result"].value_counts().index,
#                color_discrete_map=result_colors,
#                hole=0.4) # donut
#    else:
#        pie_cat_df = df[df["Broad_Role"] == pie_category]
#    
#        fig = px.pie(pie_cat_df, values=pie_cat_df["Result"].value_counts(), names=pie_cat_df["Result"].value_counts().index,
#                color=pie_cat_df["Result"].value_counts().index,
#                color_discrete_map=result_colors,
#                hole=0.4) # donut
#    
#    # update text labels on pie slices
#    fig.update_traces(textinfo="value+percent", texttemplate="(%{value})<br>%{percent}")
#    
#    # update title
#    fig.update_layout(title=dict(text=f"{pie_category} Applications", xanchor="center", x=0.5), font=dict(size=12))
#    
#    return fig
        
if __name__ == '__main__':
    app.run_server()