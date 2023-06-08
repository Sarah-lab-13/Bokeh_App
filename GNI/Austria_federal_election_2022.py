#!/usr/bin/env python
# coding: utf-8

# # Austrian federal presidential election

# In[166]:


import pandas as pd
import geopandas as gpd
import json
import matplotlib as mpl
import pylab as plt

from bokeh.io import output_file, show, output_notebook, export_png, curdoc
from bokeh.models import ColumnDataSource, GeoJSONDataSource, LinearColorMapper, CategoricalColorMapper, ColorBar, HoverTool, WheelZoomTool, ResetTool, PanTool, Select, Title
from bokeh.plotting import figure
from bokeh.palettes import brewer
from bokeh.layouts import widgetbox, row, column


# In[125]:


austria_shp = 'C:/Users/sarah/Desktop/GNI/data/OGDEXT_GEM_1_STATISTIK_AUSTRIA_20230101/STATISTIK_AUSTRIA_GEM_20230101.shp'
austria = gpd.read_file(austria_shp, encoding='utf8')
austria['g_id'] = austria['g_id'].astype(int)


# In[127]:


austria_bul_shp = 'C:/Users/sarah/Desktop/GNI/data/OGDEXT_NUTS_1_STATISTIK_AUSTRIA_NUTS2_20160101/STATISTIK_AUSTRIA_NUTS2_20160101.shp'
austria_bul = gpd.read_file(austria_bul_shp, encoding='utf8')


# In[128]:


austria_bul.rename(columns = {'ID':'g_id', 'NAME':'g_name'}, inplace = True)
austria_bul['g_name'] = austria_bul['g_name'].str.capitalize()
austria_bul.replace('Burgenland (at)', 'Burgenland', inplace = True)
austria_bul.replace(['AT11', 'AT12', 'AT13', 'AT21', 'AT22', 'AT31', 'AT32', 'AT33','AT34'],['10000', '30000', '90000', '20000', '60000', '40000', '50000', '70000', '80000'], inplace = True)
#austria_bul['g_id'].dtypes


# ## Now we have our shapefiles ready! 

# In[136]:


election_data = 'C:/Users/sarah/Desktop/GNI/data/endgueltiges_Gesamtergebnis_inkl_Briefwahl_BPW22_20221028.xlsx'
austria_election_2022 = pd.read_excel(election_data)
#austria_election_2022.head()


# ## Data cleaning

# Dropping columns i don't need, simplifying the df

# In[137]:


# dropped first line
austria_election_2022.drop(index = austria_election_2022.index [0], axis = 0, inplace = True)

#I decided to drop the rows with Wahlkarten, in order to add them in the 'votes' column directly - a terrible workaround, but 
# I found no better solution
wahlkarten = austria_election_2022[austria_election_2022['Gebietsname'].str.contains('Wahlkarten')]
austria_election_2022 = austria_election_2022[-austria_election_2022['Gebietsname'].str.contains('Wahlkarten')]


# In[138]:


#changing the GKZ code for the Wahlkarten-Stimmen in order to later add them by district-code again
wahlkarten['GKZ'] = wahlkarten.loc[:,'GKZ'].str.replace('999', '901')
wahlkarten['GKZ'] = wahlkarten.loc[:,'GKZ'].str.replace('99', '01')
#wahlkarten.head()


# In[139]:


#creating a new dataframe with the columns that i need - plus the added Wahlkarten-votes for accurate votes 
#decided to drop the columns with percents add efficiency - if we want to, we could compute the percent ourselves later
df = pd.concat([austria_election_2022, wahlkarten])
election_22 = df.groupby(['GKZ'], as_index = False).agg({'Gebietsname': 'first', 'Wahl-\nberechtigte': 'first', 'Stimmen': 'sum', 
                                                    'Unnamed: 5': 'sum', 'Dr. Michael Brunner': 'sum', 'Gerald Grosz': 'sum', 
                                                   'Dr. Walter Rosenkranz': 'sum', 'Heinrich Staudinger': 'sum', 
                                                   'Dr. Alexander Van der Bellen':'sum', 'Dr. Tassilo Wallentin':'sum',
                                                   'Dr. Dominik Wlazny': 'sum'})
#election_22.head()


# In[140]:


#adding a column for Wahlbeteiligung, since I thought that could be interesting
election_22 = election_22[-election_22['Gebietsname'].str.contains('Wahlkarten')]
election_22['Wahlbeteiligung'] = election_22.apply(lambda x: x['Stimmen'] / x['Wahl-\nberechtigte'] * 100, axis=1)
#election_22.head()


# In[141]:


# making sure that the g_id and GKZ are the same, for the later concatenation of dfs
election_22['GKZ'] = election_22['GKZ'].str.slice(1)
election_22.rename(columns = {'GKZ':'g_id', 'Gebietsname':'g_name', 'Stimmen': 'Haben_Gewählt','Unnamed: 5':'Stimmen_gesamt', 'Wahl-\nberechtigte':'Wahlberechtigte'}, inplace = True)
election_22['g_id'] = election_22['g_id'].astype(int)
election_22.to_csv(r'C:/Users/sarah/Desktop/GNI/election_22.csv', sep=',', index=False, encoding='utf-8')


# In[142]:


#rounding the numbers to integers
election_22[['Wahlberechtigte', 'Haben_Gewählt', 'Stimmen_gesamt', 'Dr. Michael Brunner', 'Gerald Grosz', 'Dr. Walter Rosenkranz', 'Heinrich Staudinger', 'Dr. Alexander Van der Bellen', 'Dr. Tassilo Wallentin', 'Dr. Dominik Wlazny', 'Wahlbeteiligung' ]] = election_22[['Wahlberechtigte', 'Haben_Gewählt', 'Stimmen_gesamt', 'Dr. Michael Brunner', 'Gerald Grosz', 'Dr. Walter Rosenkranz', 'Heinrich Staudinger', 'Dr. Alexander Van der Bellen', 'Dr. Tassilo Wallentin', 'Dr. Dominik Wlazny', 'Wahlbeteiligung']].round(0).astype(int)
#election_22.head()


# In[143]:


# this is the basis for the mapping - but we could add some more analysis
merged_ds = austria.merge(election_22, on = 'g_id', how = 'inner')
merged_ds = merged_ds.drop(merged_ds.columns[3], axis = 1)
#merged_ds.head()
#merged_ds.to_csv(r'C:/Users/sarah/Desktop/GNI/merged_ds.csv', sep=',', index=False, encoding='utf-8')


# In[153]:


# for example, the winner of the district
District_Winner = merged_ds.copy()
District_Winner = District_Winner[['Dr. Michael Brunner','Gerald Grosz', 'Dr. Walter Rosenkranz', 'Heinrich Staudinger','Dr. Alexander Van der Bellen','Dr. Tassilo Wallentin','Dr. Dominik Wlazny']].copy()
District_Winner['Winner'] = District_Winner.idxmax(axis = 1)
District_Winner['Winners_votes'] = District_Winner.max(axis = 1, numeric_only=True)


# In[154]:


import numpy as np

District_Second = merged_ds.copy()
District_Second = District_Second[['Dr. Michael Brunner','Gerald Grosz', 'Dr. Walter Rosenkranz', 'Heinrich Staudinger','Dr. Alexander Van der Bellen','Dr. Tassilo Wallentin','Dr. Dominik Wlazny']].copy()

District_Second = District_Second.apply(lambda row: row.replace(max(row),0), axis=1)

District_Second['2nd_Winner'] = District_Second.idxmax(axis = 1)
District_Second['2_most_votes'] = District_Second.max(axis = 1, numeric_only=True)


# In[155]:


District_Third = merged_ds.copy()
District_Third = District_Third[['Dr. Michael Brunner','Gerald Grosz', 'Dr. Walter Rosenkranz', 'Heinrich Staudinger','Dr. Alexander Van der Bellen','Dr. Tassilo Wallentin','Dr. Dominik Wlazny']].copy()
District_Third = District_Third.dropna()
District_Third = District_Third.astype(int)

District_Third = District_Third.apply(lambda row: row.replace(max(row),0), axis=1)
District_Third = District_Third.apply(lambda row: row.replace(max(row),0), axis=1)

District_Third['3rd_Winner'] = District_Third.idxmax(axis = 1)
District_Third['3_most_votes'] = District_Third.max(axis = 1, numeric_only=True)


# In[156]:


District_Fourth = merged_ds.copy()
District_Fourth = District_Fourth[['Dr. Michael Brunner','Gerald Grosz', 'Dr. Walter Rosenkranz', 'Heinrich Staudinger','Dr. Alexander Van der Bellen','Dr. Tassilo Wallentin','Dr. Dominik Wlazny']].copy()
District_Fourth = District_Fourth.dropna()
District_Fourth = District_Fourth.astype(int)

District_Fourth = District_Fourth.apply(lambda row: row.replace(max(row),0), axis=1)
District_Fourth = District_Fourth.apply(lambda row: row.replace(max(row),0), axis=1)
District_Fourth = District_Fourth.apply(lambda row: row.replace(max(row),0), axis=1)

District_Fourth['4th_Winner'] = District_Fourth.idxmax(axis = 1)
District_Fourth['4_most_votes'] = District_Fourth.max(axis = 1, numeric_only=True)


# In[157]:


merged_ds['Meiste_Stimmen'] = District_Winner['Winner']
merged_ds['1_most_votes'] = District_Winner['Winners_votes']

merged_ds['Zweitmeiste_Stimmen'] = District_Second['2nd_Winner']
merged_ds['2_most_votes'] = District_Second['2_most_votes']

merged_ds['Drittmeiste_Stimmen'] = District_Third['3rd_Winner']
merged_ds['3_most_votes'] = District_Third['3_most_votes']

merged_ds['Viertmeiste_Stimmen'] = District_Fourth['4th_Winner']
merged_ds['4_most_votes'] = District_Fourth['4_most_votes']


# In[158]:


format_data = [('Meiste_Stimmen', 'Meiste Stimmen'),
              ('Zweitmeiste_Stimmen', 'Zweitmeiste Stimmen'),
              ('Drittmeiste_Stimmen', 'Drittmeiste Stimmen'),
              ('Viertmeiste_Stimmen', 'Viertmeiste Stimmen')]
df = pd.DataFrame(format_data, columns = ['Wahlergebnis' , 'Name'])
print(df)


# After we created the data we want to use, we have several ways to display it.
# ## Data Mapping

# In[159]:


def get_geodatasource(gdf):  
    json_data = json.dumps(json.loads(gdf.to_json()))
    return json_data


# In[160]:


def update_plot(attr, old, new):
    new_data = get_geodatasource(merged_ds)
    
    c = select.value
    #if c == 'Meiste_Stimmen':
        #newSource = ColumnDataSource(data = {'Meiste_Stimmen': Meiste_Stimmen}) 
    #if c == 'Zweitmeiste_Stimmen':
        #newSource = ColumnDataSource(data = {'Zweitmeiste_Stimmen': Zweitmeiste_Stimmen})
    #input_data.data = newSource 
    
    input_field = df.loc[df['Name'] == c, 'Wahlergebnis'].iloc[0]
    
    p = plot(input_field)
    
    layout = column(p, widgetbox(select))
    curdoc().clear()
    curdoc().add_root(layout)
    
    geosource.geojson = new_data


# In[164]:


def plot(field_name):
    color_mapper = CategoricalColorMapper(factors = ['Dr. Michael Brunner','Gerald Grosz', 'Dr. Walter Rosenkranz', 
                                                     'Heinrich Staudinger','Dr. Alexander Van der Bellen',
                                                     'Dr. Tassilo Wallentin','Dr. Dominik Wlazny'], palette = palette)
    color_bar = ColorBar(color_mapper = color_mapper, label_standoff = 8, width = 900, height = 20,
                     location = (0,0), orientation = 'horizontal', title = 'Winning Candidate')

    p = figure(plot_height = 500 , plot_width = 900, toolbar_location ='right', 
               tools = [hover, WheelZoomTool(), ResetTool(), PanTool()],
               tooltips = [("Gemeinde", "@g_name_x"), ("Meiste Stimmen","@1_most_votes"),
                           ("Zweitmeiste Stimmen", "@2_most_votes"), ("Drittmeiste Stimmen", "@3_most_votes"),
                           ("Viertmeiste Stimmen", "@4_most_votes"),
                           ("Wahlbeteiligung", "@Wahlbeteiligung")])

    p.xaxis.visible = False
    p.yaxis.visible = False
    p.xgrid.grid_line_color = None
    p.ygrid.grid_line_color = None
    p.hover.point_policy = "follow_mouse"

    #Add muncipalities and Bundesländer
    p.patches('xs','ys', source = geosource, fill_alpha = 0.7, line_width = 0.2, line_color ='grey', 
              name = 'Districts',
              fill_color = {'field' : field_name, 'transform': color_mapper})
    p.patches('xs','ys', source = geosource2, fill_alpha = 0, line_width = 0.2, line_color ='black')
    
    p.add_layout(Title(text = 'Ausgang der Präsidentschaftswahlen 2022'), 'above')
    p.add_layout(Title(text = 'Quellen: BMI, Statistik Austria', text_font_style = 'italic', text_font_size = '8pt'), 'below')
    p.add_layout(color_bar, 'below')

    return p


# In[167]:


geosource = GeoJSONDataSource(geojson = get_geodatasource(merged_ds))
geosource2 = GeoJSONDataSource(geojson = get_geodatasource(austria_bul))

#Meiste_Stimmen = merged_ds['Winner']
#Zweitmeiste_Stimmen = merged_ds['2nd_Winner']

input_data = 'Meiste_Stimmen'

###


#####

palette = brewer['OrRd'][7]
palette = palette[::-1]

#hover tool 

hover = HoverTool(names=['Districts'])

### plot
p = plot(input_data)

##select tool 

select = Select(options = ['Meiste Stimmen', 'Zweitmeiste Stimmen', 'Drittmeiste Stimmen', 'Viertmeiste Stimmen'], value = 'Meiste Stimmen', title = 'Wahlergebnis')
select.on_change('value', update_plot)

layout = column(p, widgetbox(select))
curdoc().add_root(layout)

# Use the following code to test in a notebook, comment out for transfer to live site
# Interactive features will not show in notebook
#output_notebook()
#show(p)
#output_file(filename="custom_filename.html", title="Static HTML file")


# In[ ]:





# In[ ]:




