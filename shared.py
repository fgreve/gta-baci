import pandas as pd
import json
import os
from pathlib import Path
from google.oauth2 import service_account
from google.cloud import storage

app_dir = Path(__file__).parent 

credentials = service_account.Credentials.from_service_account_file(app_dir / 'gta-baci-credentials.json')
storage_client = storage.Client(credentials=credentials)


def clean_string(string):
    if string=='none': return ""
    if string=='nan': return ""
    return string


def get_country_code_df():
    app_dir = Path(__file__).parent
    df = pd.read_csv(app_dir / "country_code.csv")  

    df['country_code'] = df['country_code'].astype(str)
    df['country_code'] = df['country_code'].map(lambda x: x.replace('.0', ''))
    return df


def get_baci_exporter_df(exporter):
    # app_dir = Path(__file__).parent
    # df = pd.read_csv(app_dir / "baci_exporter" / str("exporter_" + exporter + ".csv"))
    df = pd.read_csv('gs://bucket-gta-baci/baci_exporter/exporter_' + exporter + '.csv', 
                    storage_options={"token": "gta-baci-credentials.json"})  

    df['year'] = df['year'].astype(str)
    
    df['exporter'] = df['exporter'].astype(str)
    
    df['importer'] = df['importer'].astype(str)
    
    df['product'] = df['product'].astype(str)
    df['product'] = df['product'].map(lambda x: x.zfill(6))

    return df


def get_gta_df():
    # app_dir = Path(__file__).parent
    # df = pd.read_csv(app_dir / "GTA.csv")
    df = pd.read_csv('gs://bucket-gta-baci/GTA.csv', 
                    storage_options={"token": "gta-baci-credentials.json"})
    
    df['State Act ID'] = df['State Act ID'].astype(str)
    df['State Act ID'] = df['State Act ID'].map(lambda x: x.replace('.0', ''))

    df['Intervention ID'] = df['Intervention ID'].astype(str)
    df['Intervention ID'] = df['Intervention ID'].map(lambda x: x.replace('.0', ''))

    df['Announcement Date']= pd.to_datetime(df['Announcement Date'])
    df['Inception Date']= pd.to_datetime(df['Inception Date'])
    df['Removal Date']= pd.to_datetime(df['Removal Date'])

    df['Announcement Date']= df['Announcement Date'].dt.date
    df['Inception Date']= df['Inception Date'].dt.date
    df['Removal Date']= df['Removal Date'].dt.date

    df['Affected Jurisdiction'] = df['Affected Jurisdiction'].astype(str)
    df['Affected Jurisdiction'] = df['Affected Jurisdiction'].map(lambda string: clean_string(string))

    df['Implementing Jurisdiction'] = df['Implementing Jurisdiction'].astype(str)
    df['Implementing Jurisdiction'] = df['Implementing Jurisdiction'].map(lambda string: clean_string(string))

    df = df.drop(columns=["Unnamed: 0"])
    df = df.sort_values(by='Announcement Date')

    return df



def affected_products(key):
    # path = os.path.join(wd, 'AffectedProducts')
    # dir_list = os.listdir(path)
    bucket_name = 'bucket-gta-baci'
    bucket = storage_client.bucket(bucket_name)

    folder_name = "AffectedProducts"
    prefix = folder_name + "/"

    dir_list = []
    blobs = bucket.list_blobs(prefix=prefix)
    for blob in blobs:
        dir_list.append(blob.name)

    dir_list = [file.replace('AffectedProducts/', '') for file in dir_list]


    df = pd.DataFrame()
    df['low_number'] = [int(file.split('_')[1]) for file in dir_list]
    df['json_file'] = dir_list
    df = df.sort_values(by='low_number')
    
    jsonfiles_list = list(df['json_file'])
    json_file = jsonfiles_list[key // 100_000]
    # json_file = jsonfiles_list[key // 10_000]

    # path_file = os.path.join(path, json_file)
    # with open(path_file) as f:
    #     affected_products_dict = json.load(f) 

    bucket = storage_client.get_bucket('bucket-gta-baci')
    blob = bucket.blob('AffectedProducts/' + json_file)
    affected_products_dict = json.loads(blob.download_as_string(client=None))
    
    return affected_products_dict



gta_df = get_gta_df()

with open('product_description_dict.json') as f:
    product_description_dict = json.load(f) 

country_code_df = get_country_code_df()


if __name__ == "__main__": 
    # print(list(product_description_dict.keys())[:10])
    # key = 150_000
    # print(list(affected_sectors(key).keys())[:10])

    # key = 730419
    # affected_products(key)

    # country_code_df = get_country_code_df()
    # print(country_code_df.head(5))

    # exporter = "156"
    # importer = "842"
    # product = "400110"
    # baci_exporter_df = get_baci_exporter_df(exporter)
    # baci_exporter_df = baci_exporter_df[baci_exporter_df['importer']==importer]
    # baci_exporter_df = baci_exporter_df[baci_exporter_df['product']==product]
    # print(baci_exporter_df.head(5))
    # print(baci_exporter_df.dtypes)

    print(gta_df.dtypes)
    print(gta_df.head(2))
    print(gta_df['Announcement Date'].iloc[:10])