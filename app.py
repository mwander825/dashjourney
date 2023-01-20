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

    pie_fig.update_layout(height=850, title_text='Overall Results of Applications', font=dict(size=10), plot_bgcolor=bg_color, paper_bgcolor=bg_color)
    
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

# figures
role_fig, role_group = create_role_fig(df)
time_series_fig = create_time_series_fig(df)
month_fig = create_month_fig(df)
dow_fig = create_dow_fig(df)
pie_fig = create_pie_fig(df, role_group)

figs = ((role_fig, "role_fig"), 
        (time_series_fig, "time_series_fig"), 
        (month_fig, "month_fig"), 
        (dow_fig, "dow_fig"), 
        (pie_fig, "pie_fig"))

# for output
output_static_figures = True

# dash app
app = Dash(__name__)

app.title = "Journey to an Entry-Level Job"  

app.layout = html.Div(children=[
    html.H1(children='Journey to an Entry-Level Job'),

    html.Div(children=[
        html.H2("""Background"""),
        
        html.P("""I graduated with an M.S. in Data Science and Engineering in May of 2022, the same month that I started my internship as a Data Scientist at Cigna. In August I started to apply to jobs, attempting to land my first entry-level full-time job in the field, or related ones. Once my internship ended in September, I aimed to apply almost every day while working on my resume. To search for jobs, I used mainly LinkedIn, Indeed, Google, and SimplyHired."""),
        
        html.P(["""One thing is important to note: when I say "entry-level", I really mean a job that requires 0-1 years of prior experience, or a "new grad" position in other words. As I came to learn, "entry-level" usually requires 1-5 years of experience (based on listings from aggregators), and sometimes specifically excludes any internship or part-time experience. This isn't really """,
              html.A("news", href="https://www.cbsnews.com/news/say-goodbye-to-the-entry-level-job/", 
                     title="(pun intended)", 
                     target="_blank",
                     rel="noopener noreferrer",
                     className="linkline"),
              """ to any job seekers, but I figured I would mention its prevalence in my 2022 job search."""]),
    
    ], className="page-container"),
    
    html.Div(children=[
        html.H2("""Examining Applications over Time"""),
        
        html.P("""The date range of applications I will look at is 08/09/2022 to 12/31/2022, during which I applied to 273 jobs. Before my internship ended on September 9th, I was applying to jobs and updating / reformatting my resume in order to bypass the ATS. It may or may not be a coincidence then that after the last resume update my applications began to result in interviews. Either way, August was an experimental period for the effectiveness of my applications and resume, apart from one of the applications made on August 12th which is an anomaly (more on that later). Interestingly, the date with the most applications (September 27th) resulted in no interviews, as well as the date with the second-most (August 31st). The first application(s) that resulted in interviews came after about 70 total applications. I tried to apply to at least one job per day, though there were stretches of time where I didn't apply daily, for one reason or another. This is mostly due to having exhausted the new listings on the job aggregators, which meant I could wait until more were posted each week."""),
                
        dcc.Graph(
            id='time-series',
            figure=time_series_fig
        )
    
    ], className="page-container"),
    
    html.Div(children=[
        html.H2("""Examining Applications by Month"""),
        
        html.P(""" This graph below is where the results of each application become visible and stratified. Looking more broadly at each month, there was at least one application per month which resulted in an interview. October and December both have the most applications at 67, and October has the most resulting interviews at 4. About half or more of each month's applications have no responses as of yet. Generally, August and December are slow months for hiring and recruiting, due to the summer and holiday season respectively, and the fall is generally a good time to apply for jobs."""),
        
        # "error loading layout": plotly doesn't like Period type for time?
        dcc.Graph(
            id='month-groups',
            figure=month_fig
        )
    ], className="page-container"),
    
    html.Div(children=[
        html.H2("""Examining Applications by Days of the Week"""),
        
         html.P("""This is more of a curiosity and behavioral analysis rather than anything to do with success rates of applications, as grouping my applications based on which day of the week I submitted them doesn't really provide too much insight into the process. I won't be superstitious from now on and never apply to a job on a Tuesday or Sunday (probably). It mainly shows that I applied more on weekdays, especially Tuesdays, Wednesdays, and Fridays, as well as the recurring statistic that over half of the applications each day of the week resulted in no response as of yet."""),
        
        dcc.Graph(
            id='dow-groups',
            figure=dow_fig
        ),
        
       
    ], className="page-container"),
    
    html.Div(children=[
        html.H2("""Examining Applications by Role"""),

        html.P("""The graph below splits all 273 applications into broad categories describing the title of the role applied for. This was done very roughly by just matching substrings in the title that went along with each job listing, but should give a good idea of the results based on fields. As I mentioned above that I have a degree in data science and completed a data science internship, I mainly searched and applied for entry-level data science roles. However, as is evident from the graph, and as I have learned afterwards, new grad data scientist jobs don't really exist, and entry-level data scientist jobs require quite a bit of experience (as they probably should). Thus, the way to break into the field is to go for a data analyst or data engineering position first. This is reflected in the data, since most of the interviews I have had (or have been contacted for) were for data analyst positions."""),
        
        dcc.Graph(
            id='role-groups',
            figure=role_fig
        )
        
    ], className="page-container"),
    
    html.Div(children=[
        html.H2("""Overall Results of Applications"""),
        
        html.P("""This final graph shows the results of all applications in donut chart form, and is also split by roles to give a different perspective of the above graph. Here we can make sense of the percentages that were evident in the grouped bar charts, as 61.9% of all applications resulted in no response, while 31.5% resulted in rejections. Disregarding application responses that were scams, just about 5.1% of all applications resulted in being contacted by someone from a company for a reason other than a rejection. This seems to line up with expectations, as I've seen many posts mentioning sending anywhere from 100 to 500 applications before actually securing a role. I can imagine it being more saturated in other computer science adjacent fields like software development or web development than in data analysis and data science."""),
        
        
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
            figure=pie_fig
        )
        
    ], className="page-container"),
        
    html.Div(children=[
        html.H2("""In Conclusion..."""),
        
        html.P("""I got one offer out of the 273 applications, which was the anomaly I mentioned before. This application was one of the two internal applications I made during my internship. The original name for this role was "Data Analyst Lead", but changed to "Junior Data Engineer" months later. Despite sending this application in early August, I was contacted by the recruiter in mid-November. It may seem like the rest of my applications were futile if the 16th one I sent eventually led to an offer, but all the interviews I had before November prepared me for the three I had for this role."""),
        
        html.H3("Takeaways"),
        
        html.Ul(children=[
        
            html.Li([
                
                html.B("Internships"),
                
                html.P("""With the death of the entry-level job came the rise of the internship, and its importance cannot be overstated. A minimum of one internship is crucial for gaining experience, and the fact that companies like to hire prior employees makes it even more important. Make sure to internally apply during an internship if you can.""")
            ]),
            
            html.Li([
                html.B("Response Rates"),
                
                html.P("""This will most likely differ depending on how much experience you have, but if you had < 1 year like me, expect no responses to at least half of all of your applications. Applicant tracking systems (ATS) automate the hiring process quite a bit, so you'd think companies would have some sort of auto-rejection set up once your resume gets filtered on the first pass, but this doesn't seem to be the case.""")
            ]),
            
            html.Li([
                html.B("Job Aggregators"),
                
                html.Br(),
                
                html.P("""Some postings on LinkedIn and Indeed already do this, but if you see a job posting that you're really eager to apply to, try to find the listing on the company site's careers page and apply there instead. That way, you can be sure that your application went directly to the company's hiring team. This is also a good way to make sure you aren't being scammed by a fraudulent posting.""")
            ])
            
        ]),
        
        
        html.P("""In the end, this is a small sample size of only one tech employment field, so these results should not be taken too seriously, but I think they give a good example of the job search process for a recent graduate in 2022.""")
        
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

# write figures to .html files
if output_static_figures:
    for fig, name in figs:
        fig.write_html("docs\\" + name + ".html")

if __name__ == '__main__':
    app.run_server()