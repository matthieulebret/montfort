import pandas as pd
import numpy as np

import re

import datetime as dt

import plotly.express as px
import plotly.graph_objs as go

from bs4 import BeautifulSoup
import requests
from requests import get

import streamlit as st

st.beta_set_page_config('Download tool',layout='wide')


st.title('Montfort real estate')

## Import data
df1 = pd.read_csv(r'78420_0000F.csv',sep=';',thousands=',')
df2 = pd.read_csv(r'78420_0000D.csv',sep=';',thousands=',')
df3 = pd.read_csv(r'78420_0000E.csv',sep=';',thousands=',')

df = pd.concat([df1,df2,df3],ignore_index=True)

#df['date_mutation']=pd.to_datetime(df['date_mutation'],infer_datetime_format=True)

#df['date_mutation']=df['date_mutation'].map(dt.datetime.toordinal)

def rightformat(item):
    if ',' in item:
        return item.replace(',','')
    else:
        return item

df['valeur_fonciere'] = pd.to_numeric(df['valeur_fonciere'])
df['surface_terrain'] = pd.to_numeric(df['surface_terrain'])
df['surface_reelle_bati'] = pd.to_numeric(df['surface_reelle_bati'])

def priceperm2(type,surfacebati,surfaceterrain,valeur):
    if type=='Maison':
        return valeur / surfacebati
    else:
        return valeur / surfaceterrain

df['prix_m2'] = df.apply(lambda x: priceperm2(x['type_local'],x['surface_reelle_bati'],x['surface_terrain'],x['valeur_fonciere']),axis=1)

df['Year']=pd.to_datetime(df['date_mutation']).dt.year

showdata = st.checkbox('Show data')
if showdata:
    shortdf = df[['date_mutation','prix_m2','valeur_fonciere','type_local','surface_reelle_bati','surface_terrain','nombre_pieces_principales','nature_culture_speciale']]
    shortdf['valeur_fonciere'] = pd.to_numeric(shortdf['valeur_fonciere'])
    shortdf['surface_terrain'] = pd.to_numeric(shortdf['surface_terrain'])
    shortdf['surface_reelle_bati'] = pd.to_numeric(shortdf['surface_reelle_bati'])
    shortdf['nombre_pieces_principales'] = pd.to_numeric(shortdf['nombre_pieces_principales'])
    st.write(shortdf.style.format({'valeur_fonciere':'{:,.2f}','surface_reelle_bati':'{:,.2f}','nombre_pieces_principales':'{:,.2f}','surface_terrain':'{:,.2f}','prix_m2':'{:,.2f}'}))

yearfilter = st.slider('Select years',min_value=2015,max_value=2019,value=(2015,2019),step=1)

df = df[(df['Year'] >= yearfilter[0]) & (df['Year'] <= yearfilter[1])]


fig = px.scatter_mapbox(df,lat='latitude',lon='longitude',hover_name='adresse_nom_voie', color = 'type_local',color_continuous_scale='Inferno',hover_data={'date_mutation':True,'valeur_fonciere':':,.2f','type_local':True,'surface_reelle_bati':':,.2f','surface_terrain':':,.2f','prix_m2':':,.2f'},size='valeur_fonciere',zoom=13,size_max=20,height=600)
fig.update_layout(mapbox_style='open-street-map',title='Real estate prices',legend=dict(orientation='h',title='Type de local'))
st.plotly_chart(fig,use_container_width=True)

##Sunburst charts

st.header('Transactions by type')

fig = px.sunburst(df,path=['type_local','nature_culture_speciale','adresse_nom_voie','id_mutation'],values='valeur_fonciere')
st.plotly_chart(fig,use_contained_width=True)

## Distplot

st.header('Distribution of transactions')

selectassets = st.multiselect('Select type_local',['Maison','None','Local industriel. commercial ou assimilé'],default=['Maison','None','Local industriel. commercial ou assimilé'])
df = df[df['type_local'].isin(selectassets)]

fig = px.box(df,x='Year',y='valeur_fonciere',hover_data={'date_mutation':True,'adresse_nom_voie':True,'valeur_fonciere':':,.2f','type_local':True,'surface_reelle_bati':':,.2f','surface_terrain':':,.2f','prix_m2':':,.2f'},color='Year',points='all')
fig.update_layout(showlegend=False)
st.plotly_chart(fig,use_contained_width=True)


### WEB SCRAPING

st.header('Latest ads')

location = []
postcode = []
area = []
price = []

page = requests.get(r'''https://www.terrain-construction.com/search/terrain-a-vendre/Montfort-l%27Amaury-78490?rayon=5&terrain=1%252C0&ordre=proximite''')

soup = BeautifulSoup(page.text,'html.parser')

mytext = soup.text


mylist = re.findall('^.*[7][8][0-9]{3} Terrain de.*',mytext,re.MULTILINE)

for ad in mylist:
    location.append(ad.split(' ',1)[0])
    postcode.append(ad.split(' ',2)[1])
    area.append(ad.split('Terrain de ',1)[1].split(' ',1)[0])
    price.append(ad.split('à ',1)[1])

mylist = pd.DataFrame([location,postcode,area,price]).transpose()
mylist.columns=['Commune','Code postal','Surface','Prix']
mylist['Surface']=pd.to_numeric(mylist['Surface'])

def prixnum(item):
    item = item.replace(' €','')
    item = item.replace(' ','')
    return item

mylist['Prix']=mylist['Prix'].apply(prixnum)
mylist['Prix']=pd.to_numeric(mylist['Prix'])

mylist['Prix_m2']= mylist['Prix']/mylist['Surface']
mylist.drop_duplicates(keep='first',inplace=True)

mylist_format = mylist.style.format({'Surface':'{:,.2f}','Prix':'{:,.2f}','Prix_m2':'{:,.2f}'})

st.table(mylist_format)
