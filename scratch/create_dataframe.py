import pandas as pd
from dateutil.parser import parse
import os

        
def create_dataframe():

    with open("scratch/applied_8_9_2022.txt", "r", encoding="utf-8") as file:
        text = file.readlines()
    
    # filter job lines
    date_dict = {}

    for line in text:
        try: 
            date = parse(line)
            date_dict[date] = []
        except:
            if ":" in line:
                date_dict[date].append(line)

    jobs_by_date = [item for sublist in [list(map(lambda vv: (k, vv), v)) for k, v in date_dict.items()] for item in sublist]


    DOW_dict = {"Monday": 0,
               "Tuesday": 1,
               "Wednesday": 2,
               "Thursday": 3,
               "Friday": 4,
               "Saturday": 5,
               "Sunday": 6}

    df = pd.DataFrame(jobs_by_date, columns=["Date_Applied", "Line"])
    df["Company"] = df["Line"].str.strip().str.split(":").apply(lambda l: l[0].strip())
    df["Title"] = df["Line"].str.strip().str.split(":|w.+\$$|==>", regex=True).apply(lambda l: l[1].strip().title())
    df["Result"] = df["Line"].str.strip().str.split("==>").apply(lambda l: l[1].strip().title() if len(l) > 1 else "No Response")
    df["DOW"] = df["Date_Applied"].apply(lambda d: d.day_name())
    df["year_month"] = df["Date_Applied"].dt.to_period("M").astype(str)

    df_title = df["Title"]

    dse_match = "(?i)Data Scientist|Data Science|Science|Scientist"
    da_match = "(?i)Data Analyst|Data Analytics|Analytics|Analyst"
    ml_match = "(?i)Machine Learning Engineer|Machine Learning"
    de_match = "(?i)Data Engineer|Engineer|Engineering|Database"

    # fixing overlaps
    dse_series = df_title[df_title.str.contains(dse_match)]

    ml_series = df_title[df_title.str.contains(ml_match)]
    de_series = df_title[df_title.str.contains(de_match)]
    de_series = de_series[(~de_series.isin(ml_series)) & (~de_series.isin(dse_series))]

    da_series = df_title[df_title.str.contains(da_match)]
    da_series = da_series[(~da_series.isin(dse_series)) & (~da_series.isin(de_series)) & (~da_series.isin(ml_series))]

    other_series = df_title[~((df_title.str.contains(dse_match)) | (df_title.str.contains(da_match)) | (df_title.str.contains(ml_match)) | (df_title.str.contains(de_match)))]

    df["Broad_Role"] = pd.Series("Data Scientist", dse_series.index).combine_first(pd.Series("Data Analyst", da_series.index)) \
        .combine_first(pd.Series("Data Engineer", de_series.index)) \
        .combine_first(pd.Series("ML Engineer", ml_series.index)) \
        .combine_first(pd.Series("Other", other_series.index))

    df.drop(["Line", "Title", "Company"], axis=1).to_csv("scratch/Application_Results_12_31_2022.csv")
    return
