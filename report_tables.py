import pandas as pd

def write_missing_data(s):
    which = s[s.isnull()].index.values
    return ", ".join(which)

def count_missing_data(s):
    return s.isnull().sum()

def report_missing_data(df):
    report = pd.DataFrame()

    report["nb_missing"]=df.apply(count_missing_data,axis=1)  
    report["missing_data"]=df.apply(write_missing_data,axis=1)
    report  = report.ix[report["nb_missing"]>0,:]

    return report.sort_values(by="nb_missing")
    
