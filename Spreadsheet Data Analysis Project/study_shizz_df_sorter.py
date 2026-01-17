from dotenv import load_dotenv
import pandas as pd
import gspread 
import os 
import json

load_dotenv('.env') 
load_creds = os.getenv("credentials")
credentials = json.loads(load_creds)
gc = gspread.service_account_from_dict(credentials)
sheet_name = os.getenv("sheet_name")
subsheet_name = os.getenv("subsheet_name")


study_data = gc.open(sheet_name)
wksht = study_data.worksheet(subsheet_name) 
data = wksht.get_all_records() 
df = pd.DataFrame(data)



#def





#Debuging tools
def print_head_and_classes(df):
    print(df.head(), '\n')
    df['Current Classes:'] = df['Current Classes:'].str.split(', ') 
    print(df['Current Classes:'].head())



print_head_and_classes(df)








