#Functions
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import pprint 
import pandas as pd 
from matplotlib import pyplot as plt
import imapclient
import smtplib, ssl
import email
import numpy as np
from email.mime.multipart import MIMEMultipart
from email.mime.image import MIMEImage
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email import encoders
import os 
from  matplotlib.colors import LinearSegmentedColormap
import matplotlib.ticker as ticker
import time
from scipy.ndimage.filters import gaussian_filter1d

# Define all necessary functions
def get_journal_df(creds_path, scope, sheet):
    #Load in Data from Google Sheets
    creds = ServiceAccountCredentials.from_json_keyfile_name(creds_path, scope)
    gc = gspread.authorize(creds)
    j2020 = gc.open(sheet).get_worksheet(1)
    #Set data from Sheet in DataFrame
    df = pd.DataFrame(j2020.get_all_records())
    #Turn numeric data in DF into floats (from str)
    for column in df.columns:
        if column not in ['Day', 'Date', 'Journal']:
            df[column] = pd.to_numeric(df[column], errors='coerce')
    return df

def get_iMax(df):
    return len([len(item) for item in df["Journal"] if len(item) != 0]) #Num datapoints by looking at journal column

def int_columns(df):
    for column in df.columns:
        if column not in ['Day', 'Date', 'Journal']:
            df[column] = pd.to_numeric(df[column], errors='coerce')
    return df

def get_y(df, column1, column2):
    return (gaussian_filter1d(df[column1][:get_iMax(df)], sigma=1.7), gaussian_filter1d(df[column2][:get_iMax(df)], sigma=1.7))

def remove_string_columns(df):
    df_clean = df.copy()
    try:
        del df_clean["Day"]
        del df_clean["Date"]
        del df_clean["Journal"]
        return df_clean
    except:
        return df_clean

def df_no_str_cols(df):
    df_clean = df.copy()
    try:
        del df_clean["Day"]
        del df_clean["Date"]
        del df_clean["Journal"]
        return df_clean
    except:
        return df_clean

def get_xlabels(df):
    xlabels =[]
    vecka = 21
    for i in range(get_iMax(df)):
        if df["Day"][i] == "måndag":
            xlabels.append(df["Date"][i] + "\n Mån v: " + str(vecka))
            vecka += 1
    return xlabels

def create_group_data(df, group, groups):
    return df[groups[group]].mean(axis=1)[:get_iMax(df)]

def create_group_plot(df, attatchment_path, group, groups, show):
    group_data = create_group_data(df, group, groups)
    # Background cmap definined manually 
    cmap = LinearSegmentedColormap.from_list('krg',["#008702","#7fe393", "#f4f4f4","#F6BCB6", "#B23131"], N=256)
    #Plot and save the graphs
    iMax = get_iMax(df)
    aspect = iMax/14
    fig, line = plt.subplots(figsize=(8.8,5), sharex=True, sharey=True)
    line.imshow([[0,0],[1,1]], cmap=cmap, interpolation='bicubic', extent=[0,iMax,0.7,5.3], aspect=aspect)
    # x_values = [datetime.datetime.strptime(d,"%Y-%m-%d").date() for d in df["Date"][:iMax]]
    x_values = df["Date"][:iMax]
    y_values1 = gaussian_filter1d(group_data, sigma=1.7)
    
    linestyle = "-"
    linecolor = "black"
    for col in groups[group]:
        y_values_col = gaussian_filter1d(df[col][:get_iMax(df)], sigma=1.7)
        line.plot_date(x_values, y_values_col, linewidth="1", linestyle=linestyle, marker=None, label=col)
    line.plot_date(x_values, y_values1, linewidth="3", color=linecolor, linestyle=linestyle, marker=None, label=group)
    line.set_ylim(0.7, 5.3)
    
    xlabels = get_xlabels(df)
    line.set_xticks([df["Date"][i] for i in range(iMax) if df["Day"][i] == "måndag"])
    line.set_xticks([df["Date"][i] for i in range(iMax) if df["Day"][i] != "måndag"], minor=True)
    line.set_xticklabels(xlabels, rotation=90)
    line.set_yticks([1,2,3,4,5])
    line.tick_params(axis='y', which='major', labelsize=10)

    line.grid(axis = "y", linestyle="-", color="darkgray")    
    line.legend()
    line.set_title(group) 
    fig.tight_layout()
    plt.savefig(attatchment_path+"y_"+str(group)+"_plot", facecolor="#f4f4f4", transparent=True, pad_inches=6, dpi=300)
    if show: 
        plt.show()
    else: 
        plt.clf()

def create_all_group_plots(df, attatchment_path, groups, show=False):
    for group in groups.keys():
        create_group_plot(df, attatchment_path, group, groups, show)

def compare_plot(df, attatchment_path, column1, column2):
    """In: two of: Average, Experience, Harmony, Social, Motivation, Physique, Creativity, ER, Diet, Discipline, Sleep, Productivity, Meditation, Training&Strech
    Out: Graph with both columns """
    iMax = get_iMax(df)
    # Init
    cmap = LinearSegmentedColormap.from_list('krg',["#31B247","#B6F6BE", "#f4f4f4","#F6BCB6", "#B23131"], N=256)
    fig, line = plt.subplots(figsize=(8.8,5), sharex=True, sharey=True)
    line.imshow([[0,0],[1,1]], cmap=cmap, interpolation='bicubic', extent=[0,iMax,0.7,5.3], aspect=iMax/14)

    x_values = df["Date"][:get_iMax(df)]
    y_values1, y_values2 = get_y(df, column1, column2)
    # Lines
    line.plot_date(x_values, y_values1, linewidth="2", color="black", linestyle="-", marker=None, label=column1)
    line.plot_date(x_values, y_values2, linewidth="2", color="blue", linestyle="-", marker=None, label=column2)

    line.set_ylim(0.7, 5.3)
    xlabels =[]
    vecka = 21
    for i in range(get_iMax(df)):
        if df["Day"][i] == "måndag":
            xlabels.append(df["Date"][i] + "\n Mån v: " + str(vecka))
            vecka += 1
    line.set_xticks([df["Date"][i] for i in range(get_iMax(df)) if df["Day"][i] == "måndag"])
    line.set_xticks([df["Date"][i] for i in range(get_iMax(df)) if df["Day"][i] != "måndag"], minor=True)
    line.set_xticklabels(xlabels, rotation=90)
    line.set_yticks([1,2,3,4,5])
    line.tick_params(axis='y', which='major', labelsize=10)
    line.grid(axis = "y", linestyle="-", color="darkgray")
    line.legend()
    line.set_title(column1 + " & " + column2) 
    fig.tight_layout()
    fig.savefig(attatchment_path+ "/plotcomp/"+str(column1)+ "_and_" + str(column2) +"_plot", facecolor="#f4f4f4", transparent=True, pad_inches=6, dpi=300)

# Plot functions
def create_data_plot(df, column, attatchment_path, show=False):
    # Background cmap definined manually 
    cmap = LinearSegmentedColormap.from_list('krg',["#008702","#7fe393", "#f4f4f4","#F6BCB6", "#B23131"], N=256)
    # Plot and save the graphs
    iMax = get_iMax(df)
    aspect = iMax/14
    fig, line = plt.subplots(figsize=(8.8,5), sharex=True, sharey=True)
    line.imshow([[0,0],[1,1]], cmap=cmap, interpolation='bicubic', extent=[0,iMax,0.7,5.3], aspect=aspect)

    # x_values = [datetime.datetime.strptime(d,"%Y-%m-%d").date() for d in df["Date"][:iMax]]
    x_values = df["Date"][:iMax]
    y_values1 = gaussian_filter1d(df[column][:iMax], sigma=1.7)
    y_values2 = gaussian_filter1d(df[column][:iMax], sigma=1)
    y_values3 = df[column][:iMax]

    linestyle = "-"
    line.plot_date(x_values, y_values2, linewidth="1", color="gray", linestyle=linestyle, marker=None)
    line.plot_date(x_values, y_values3, linewidth="0.5", color="lightgray", linestyle=linestyle, marker=None)
    line.plot_date(x_values, y_values1, linewidth="3", color="black", linestyle=linestyle, marker=None)

    line.plot_date(x_values, df[column][:iMax], "kx", color="#494949" ,label=column)
    line.set_ylim(0.7, 5.3)
    
    xlabels = get_xlabels(df)
    line.set_xticks([df["Date"][i] for i in range(iMax) if df["Day"][i] == "måndag"])
    line.set_xticks([df["Date"][i] for i in range(iMax) if df["Day"][i] != "måndag"], minor=True)
    line.set_xticklabels(xlabels, rotation=90)
    line.set_yticks([1,2,3,4,5])
    line.tick_params(axis='y', which='major', labelsize=10)

    line.grid(axis = "y", linestyle="-", color="darkgray")    
    line.legend()
    line.set_title(column) 
    fig.tight_layout()
    plt.savefig(attatchment_path+str(column)+"_plot", facecolor="#f4f4f4", transparent=True, pad_inches=6, dpi=300)
    if show: 
        plt.show()
    else: 
        plt.clf()

def create_all_data_plots(df, attatchment_path, show=False):
    for column in df_no_str_cols(df):
        create_data_plot(df, column, attatchment_path, show)

def rank_columns_std_plot(df, attatchment_path, show=False):
    fig, line = plt.subplots(figsize=(8.8,6), sharex=True, sharey=True)
    line.bar(remove_string_columns(df).columns, df[0:get_iMax(df)].std(), label = "Standard Deviation")
    line.grid(axis = "y", linestyle="-", color="darkgray")
    line.legend()
    line.set_ylim(0, 2)
    line.tick_params(axis='x', labelrotation=90)
    line.set_facecolor("#F4F4F4")
    fig.set_facecolor("white")
    fig.tight_layout()
    line.set_title("Standard deviations") 
    fig.savefig(attatchment_path+"z_std"+"_plot", facecolor="#f4f4f4", transparent=True, pad_inches=6, dpi=300)
    if show: 
        plt.show()
    else: 
        plt.clf()

def rank_columns_mean_plot(df, attatchment_path, show=False):
    fig, line = plt.subplots(figsize=(8.8,6), sharex=True, sharey=True)
    line.bar(remove_string_columns(df).columns, df[0:get_iMax(df)].mean(), label = "Mean", color="green")
    line.grid(axis = "y", linestyle="-", color="darkgray")
    line.legend()
    line.set_ylim(0.7, 5.3)
    line.tick_params(axis='x', labelrotation=90)
    line.set_facecolor("#F4F4F4")
    fig.set_facecolor("white")
    fig.tight_layout()
    line.set_title("Means") 
    fig.savefig(attatchment_path+"z_means"+"_plot", facecolor="#f4f4f4", transparent=True, pad_inches=6, dpi=300)
    if show: 
        plt.show()
    else: 
        plt.clf()

def rank_columns_correlation_plot(df, attatchment_path, show=False):
    so = df[0:get_iMax(df)].corr().abs().unstack().sort_values(kind="quicksort").drop_duplicates()[:-1]
    x = [so.index[i][0] + ", " + so.index[i][1] for i in range(len(so.index))]
    fig, line = plt.subplots(figsize=(50,10), sharex=True, sharey=True)
    line.bar(x, so, label = "Correlations", color="lightblue", edgecolor="black")
    for i, v in enumerate(so):
        line.text(i-0.3, v+0.03, "- "+  str(round(v,4)), fontweight="bold", color='black', rotation=90)
    line.grid(axis = "y", linestyle="-", color="darkgray")
    line.set_aspect("auto")
    line.legend(loc="upper left", markerscale="4")
    line.set_ylim(0, 1)
    line.tick_params(axis='x', labelrotation=90)
    line.set_facecolor("#F4F4F4")
    fig.set_facecolor("white")
    line.set_title("Correlations") 
    fig.tight_layout()
    fig.savefig(attatchment_path+"z_correlations"+"_plot", facecolor="#f4f4f4", transparent=True, pad_inches=6, dpi=300)
    if show: 
        plt.show()
    else: 
        plt.clf()
