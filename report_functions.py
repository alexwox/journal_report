# Functions
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

def int_columns(df):
    """
    In: 
        df: All of the data (Pandas DataFrame)
    Returns:
        The columns that are not Day, Date or Journal (df)
    """
    for column in df.columns:
        if column not in ['Day', 'Date', 'Journal']:
            df[column] = pd.to_numeric(df[column], errors='coerce')
    return df

def get_journal_df(creds_path, scope, sheet):
    """
    In: 
        creds_path: path to json file with gspread credentials (str)
        scope: list with api scope (list)
        sheet: string with name of sheet that has the data 

    Does: API call to get data. Initial processing of data. 
    Returns:
        All of the data (Pandas DataFrame)
    """
    # Load in Data from Google Sheets
    creds = ServiceAccountCredentials.from_json_keyfile_name(creds_path, scope)
    gc = gspread.authorize(creds)
    j2020 = gc.open(sheet).get_worksheet(1)

    # Set data from Sheet in DataFrame
    df = pd.DataFrame(j2020.get_all_records())
    
    # Turn numeric data in DF into floats (from str)
    return int_columns(df)

def get_iMax(df):
    """
    In: 
        df: All of the data (Pandas DataFrame) 
    Does: Uses journal entries to get max index. (number of entries - 1)
    Returns: 
        Max index (int) 
    """
    return len([len(item) for item in df["Journal"] if len(item) != 0]) #Num datapoints by looking at journal column

def get_y(df, column1, column2):
    """
    In: 
        df: All of the data (Pandas DataFrame)   
        columns
    Returns: 
        Gaussian smoothed data in Tuple. (Tuple with Pandas Series)
    """
    return (gaussian_filter1d(df[column1][:get_iMax(df)], sigma=1.7), gaussian_filter1d(df[column2][:get_iMax(df)], sigma=1.7))

def remove_string_columns(df):
    """
    In: 
        df: All of the data (Pandas DataFrame)
    Returns: 
        All data without the three generic columns Day, Date, Journal (Pandas DataFrame)
    """
    df_clean = df.copy()
    try:
        del df_clean["Day"]
        del df_clean["Date"]
        del df_clean["Journal"]
        return df_clean
    except:
        return df_clean

def get_xlabels(df):
    """
    In:
        df: All of the data (Pandas DataFrame)
    Does: Uses data to create xlabels every monday with week number. 
    Returns: 
        xlabels (list)
    """
    xlabels =[]
    vecka = 21
    for i in range(get_iMax(df)):
        if df["Day"][i] == "måndag":
            xlabels.append(df["Date"][i] + "\n Mån v: " + str(vecka))
            vecka += 1
    return xlabels

def create_group_data(df, groups, group):
    """
    In: 
        df: All of the data (Pandas DataFrame)
        groups: All of the groups (list)
        group: Specific group (str)
    Does: Creates y data for a specific group by taking the mean of group entries
    Returns:
        Pandas DataFrame 
    """
    return df[groups[group]].mean(axis=1)[:get_iMax(df)]

def create_group_plot(df, attatchment_path, group, groups, show):
    """
    In: 
        df: All of the data (Pandas DataFrame)
        attatchment_path: Path where plots will be saved (str)
        group: Specific group name (str)
        groups: List of all group names (list)
        show: Decides if plot is shown or not (Boolean)
    Does: Creates background and then plots all group entries and group mean
    Returns: 
        None 
    """
    # Load group data
    group_data = create_group_data(df, groups, group)
    x_values = df["Date"][:iMax]

    # Initialize figure and plot, use cmap as background
    iMax = get_iMax(df)
    aspect = iMax/14
    fig, line = plt.subplots(figsize=(8.8,5), sharex=True, sharey=True)
    cmap = LinearSegmentedColormap.from_list('krg',["#008702","#7fe393", "#f4f4f4","#F6BCB6", "#B23131"], N=256)
    line.imshow([[0,0],[1,1]], cmap=cmap, interpolation='bicubic', extent=[0,iMax,0.7,5.3], aspect=aspect)
    
    # Plot group members
    linestyle = "-"
    linecolor = "black"
    for col in groups[group]:
        y_values_col = gaussian_filter1d(df[col][:get_iMax(df)], sigma=1.7)
        line.plot_date(x_values, y_values_col, linewidth="1", linestyle=linestyle, marker=None, label=col)
    
    # Plot group mean
    y_values1 = gaussian_filter1d(group_data, sigma=1.7)
    line.plot_date(x_values, y_values1, linewidth="3", color=linecolor, linestyle=linestyle, marker=None, label=group)
    
    # Plot configs
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
    
    # Use show argument to decide wheter to plot or not 
    if show: 
        plt.show()
    else: 
        plt.clf()

def create_all_group_plots(df, attatchment_path, groups, show=False):
    """
    In: 
        df: All of the data (Pandas DataFrame)
        attatchment_path: Path where plots will be saved (str)
        groups: List of all group names (list)
        show: Decides if plot is shown or not (Boolean)
    Does: Calls create_group_plot on every group.
    Returns: 
        None 
    """
    for group in groups.keys():
        create_group_plot(df, attatchment_path, group, groups, show)

def compare_plot(df, attatchment_path, column1, column2):
    """
    In: 
        df: All of the data (Pandas DataFrame)
        attatchment_path: Path where plots will be saved (str)
        column1, column2: Two of: Average, Experience, Harmony, Social, Motivation, Physique, Creativity, \
                                  ER, Diet, Discipline, Sleep, Productivity, Meditation, Training&Strech (str)
    Does: Creates a plot with two different columns. 
    Returns: 
        None     
    """
    # Init
    iMax = get_iMax(df)
    cmap = LinearSegmentedColormap.from_list('krg',["#31B247","#B6F6BE", "#f4f4f4","#F6BCB6", "#B23131"], N=256)
    fig, line = plt.subplots(figsize=(8.8,5), sharex=True, sharey=True)
    line.imshow([[0,0],[1,1]], cmap=cmap, interpolation='bicubic', extent=[0,iMax,0.7,5.3], aspect=iMax/14)

    # Get axis valeues and plot the two lines
    x_values = df["Date"][:get_iMax(df)]
    y_values1, y_values2 = get_y(df, column1, column2)
    line.plot_date(x_values, y_values1, linewidth="2", color="black", linestyle="-", marker=None, label=column1)
    line.plot_date(x_values, y_values2, linewidth="2", color="blue", linestyle="-", marker=None, label=column2)

    # Plot configs
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

def create_data_plot(df, column, attatchment_path, show=False):
    """
    In: 
        df: All of the data (Pandas DataFrame)
        attatchment_path: Path where plots will be saved (str)
        column: One of thw following columns: 
            Average, Experience, Harmony, Social, Motivation, Physique, Creativity, 
            ER, Diet, Discipline, Sleep, Productivity, Meditation, Training&Strech (str)
        show: Decides if plot is shown or not (Boolean) 
    Does: Creates a plot with the column. 
    Returns: 
        None  
    """
    # Initalize figure and plot, background cmap definined manually 
    iMax = get_iMax(df)
    aspect = iMax/14
    fig, line = plt.subplots(figsize=(8.8,5), sharex=True, sharey=True)
    cmap = LinearSegmentedColormap.from_list('krg',["#008702","#7fe393", "#f4f4f4","#F6BCB6", "#B23131"], N=256)
    line.imshow([[0,0],[1,1]], cmap=cmap, interpolation='bicubic', extent=[0,iMax,0.7,5.3], aspect=aspect)
    
    # Prepare data
    x_values = df["Date"][:iMax]
    y_values1 = gaussian_filter1d(df[column][:iMax], sigma=1.7)
    y_values2 = gaussian_filter1d(df[column][:iMax], sigma=1)
    y_values3 = df[column][:iMax]

    # Plot the data 
    linestyle = "-"
    line.plot_date(x_values, y_values2, linewidth="1", color="gray", linestyle=linestyle, marker=None)
    line.plot_date(x_values, y_values3, linewidth="0.5", color="lightgray", linestyle=linestyle, marker=None)
    line.plot_date(x_values, y_values1, linewidth="3", color="black", linestyle=linestyle, marker=None)
    line.plot_date(x_values, df[column][:iMax], "kx", color="#494949" ,label=column)

    # Plot configurations
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
   
    # Use show argument to decide wheter to plot or not 
    if show: 
        plt.show()
    else: 
        plt.clf()

def create_all_data_plots(df, attatchment_path, show=False):
    """
    In: 
        df: All of the data (Pandas DataFrame)
        attatchment_path: Path where plots will be saved (str)
        show: Decides if plot is shown or not (Boolean)
    Does: Calls create_data_plot on all columns. 
    Returns: 
        None 
    """
    # Use create_data_plot on all 
    for column in remove_string_columns(df):
        create_data_plot(df, column, attatchment_path, show)

def rank_columns_std_plot(df, attatchment_path, show=False):
    """
    In: 
        df: All of the data (Pandas DataFrame)
        attatchment_path: Path where plots will be saved (str)
        show: Decides if plot is shown or not (Boolean)
    Does: Creates a plot with all stds of all columns. 
    Returns: 
        None     
    """
    # Plot 
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
    
    # Use show argument to decide wheter to plot or not 
    if show: 
        plt.show()
    else: 
        plt.clf()

def rank_columns_mean_plot(df, attatchment_path, show=False):
    """
    In: 
        df: All of the data (Pandas DataFrame)
        attatchment_path: Path where plots will be saved (str)
        show: Decides if plot is shown or not (Boolean)
    Does: Creates a plot with all means of all columns. 
    Returns: 
        None     
    """
    #Plot figure 
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
    
    # Use show argument to decide wheter to plot or not     
    if show: 
        plt.show()
    else: 
        plt.clf()

def rank_columns_correlation_plot(df, attatchment_path, show=False):
    """
    In: 
        df: All of the data (Pandas DataFrame)
        attatchment_path: Path where plots will be saved (str)
        show: Decides if plot is shown or not (Boolean)
    Does: Creates a plot with all correlations.  
    Returns: 
        None     

    """
    # Get the correlation data and remove duplicates. 
    so = df[0:get_iMax(df)].corr().abs().unstack().sort_values(kind="quicksort").drop_duplicates()[:-1]
    x = [so.index[i][0] + ", " + so.index[i][1] for i in range(len(so.index))]

    #Create plot 
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
    
    # Use show argument to decide wheter to plot or not 
    if show: 
        plt.show()
    else: 
        plt.clf()
