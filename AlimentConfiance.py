# -*- coding: utf-8 -*-
"""
Created on Thu Dec 10 13:37:42 2020

@author: Mc Zie
"""
# Start with loading all necessary libraries
import numpy as np
import pandas as pd
import seaborn as sns
from os import path
import os
from PIL import Image
from wordcloud import WordCloud, STOPWORDS, ImageColorGenerator
import matplotlib.pyplot as plt
from datetime import date
from datetime import datetime
import plotly.express as px
import plotly
from flask import Flask, render_template
from flask import Flask, flash, request, redirect, url_for
from werkzeug.utils import secure_filename


today = datetime.now()

#displaythe dataset in JSon format in the browser (for a given town) from a URL.

#https://data.opendatasoft.com/explore/dataset/export_alimconfiance%40dgal/api/?disjunctive.app_libelle_activite_etablissement&disjunctive.filtre&disjunctive.ods_type_activite&q=&rows=10000&refine.libelle_commune=Rouen

#Start the python programming

print("enter the Town/City :")
City=input()
City = City[0].upper() + City[1:].lower()
print("\n")

import json
import requests

data= requests.get('https://dgal.opendatasoft.com/api/records/1.0/search/?dataset=export_alimconfiance&rows=10000&facet=filtre&facet=app_libelle_activite_etablissement&facet=libelle_commune&facet=synthese_eval_sanit&facet=date_inspection&facet=ods_type_activite&refine.libelle_commune=' + City)


#Formate json file
json_data_formate=json.dumps(data.json(),indent=4)

#Save the json file  after formate
#file=open("data.json",'w')
#file.writelines(json_data_formate)
#file.close()
    
# Display the correctly formatted data set on the screen (with line breaks and (indentations)  
file = open ("data.json",'r')
json_data = json.load(file) 
json_data_formated=json.dumps(json_data,indent=4) #with 4 indentations
file.close()
print(json_data_formated)



#Create a subfolder called “data” without error if it already exists
os.makedirs("./data",exist_ok=True)

#Save the data as a JSon file on the hard disk drive, in the “data” folder that you  created previously
if json_data_formated:
    with open("./data/data.json","w") as file :
        file.writelines(json_data_formated)
else:
    print("the json file is empty")
    print("\n")
        
# extraction and display information from the “description” part on the screen (refer to the description section)

print("|"+"-"*123+"|")
print("| "+"Welcome to" +"   "+City+" !"+" "*95+"|")
print("| "+"the date and hour for to day , is",today,", The list of official sanitary controls since is:"+" "*62+"|")
print("|"+"-"*123+"|")
print("| "+"Business name"+                       " | "+"Type                           "+" | "+"Zip_Code              "+" | "+"Résult    ")
print("|"+"-"*123+"|")

n=0
while n < json_data["nhits"]:
    print("|",json_data["records"][n]["fields"]["app_libelle_etablissement"]," "*(17-len(json_data["records"][n]["fields"]["app_libelle_etablissement"])),"|",json_data["records"][n]["fields"]["app_libelle_activite_etablissement"]," "*(30-len(json_data["records"][n]["fields"]["app_libelle_activite_etablissement"])),"|",json_data["records"][n]["fields"]["code_postal"]," "*(17-len(json_data["records"][n]["fields"]["code_postal"])),"|",json_data["records"][n]["fields"]["synthese_eval_sanit"]," "*(10-len(json_data["records"][n]["fields"]["synthese_eval_sanit"])),"|")
    n += 1
print("|"+"-"*123+"|") 

#**********************************************************************************************************************************************************************************************************************************************************************************************************************************************************************************************************************************************************************************************************************************************
#Display additional information of your choice(siret is our additionnal choice)

print("|"+"-"*123+"|")
print("| "+"Welcome to" +"  "+  City+" !"+" "*95+"|")
print("| "+"the date and hour for to day , is",today,", The list of official sanitary controls since is:"+" "*62+"|")
print("|"+"-"*123+"|")
print("| "+"Business name"+                       " | "+"Type                           "+" | "+"Zip_code         "+" | "+"Résult        "+" | "+"Siret ")
print("|"+"-"*123+"|")

n=0
while n < json_data["nhits"]:
    
    print("|",json_data["records"][n]["fields"]["app_libelle_etablissement"]," "*(17-len(json_data["records"][n]["fields"]["app_libelle_etablissement"])),"|",json_data["records"][n]["fields"]["app_libelle_activite_etablissement"]," "*(30-len(json_data["records"][n]["fields"]["app_libelle_activite_etablissement"])),"|",json_data["records"][n]["fields"]["code_postal"]," "*(17-len(json_data["records"][n]["fields"]["code_postal"])),"|",json_data["records"][n]["fields"]["synthese_eval_sanit"]," "*(10-len(json_data["records"][n]["fields"]["synthese_eval_sanit"])),"|",json_data["records"][n]["fields"]["siret"]," "*(10-len(json_data["records"][n]["fields"]["siret"])),"|")
    n += 1
print("|"+"-"*123+"|") 

#********************************************************************************************************************************************************************************************************************************************************************************************************************************************************************************************************************************************************************************************************************************************************************************


#display the data

print('............................................................................')
print("Total number of restorant :", str(json_data["nhits"]))
maximum=int(input("show how many restaurant we have?"))

records=json_data['records'][:maximum]

print("\n")

#creat a empty data to save data

columns=["Business name","Type","Zip_Code","Result"]
df=pd.DataFrame(columns=columns)

#Manage exception when extracting data (try: except: keywords)
try:

   for records  in records :
    business_name=records['fields'].get('app_libelle_etablissement','missing_name')
    Zip_code=records['fields'].get('code_postal','missing_name')
    Type=records['fields'].get('filtre',records['fields'].get('app_libelle_activite_etablissement','missing_name'))
    Résult=records['fields'].get('synthese_eval_sanit','missing_name')
    df.loc[len(df)]=[business_name,Type,Zip_code,Résult]
    print(df)


except KeyError:

    print(f"{df}'data is empty.")

#*******************************************************************************************************************************************************************************************************************************************************************************************************************************************************************************************************************************************************************************************
#collect the data in csv extension
"""
for records  in records :
    business_name=records['fields'].get('app_libelle_etablissement','missing_name')
    adress=records['fields'].get('code_postal','missing_name')
    Type=records['fields'].get('filtre',records['fields'].get('app_libelle_activite_etablissement','missing_name'))
    Résult=records['fields'].get('synthese_eval_sanit','missing_name')
    df.loc[len(df)]=[business_name,Type,adress,Résult]
print(df)
"""
#save_df=df.to_csv('data.csv')
    
#print(save_df)  
#************************************************************************************************************************************************************************************************************************************************************************************************************************************************************************************************************

#Display a wordcloud and download

# Extract the plain text content of the page
text = " ".join(review for review in df["Business name"])
print ("There are {} words in the combination of all review.".format(len(text)))

# Create stopword list:
stopwords = set(STOPWORDS)
stopwords.update(["drink", "now", "wine", "flavor", "flavors"])

# Generate a word cloud image
wordcloud = WordCloud(stopwords=stopwords, background_color="white").generate(text)

# Display the generated image:
# the matplotlib way:
plt.imshow(wordcloud, interpolation='bilinear')
plt.axis("off")
plt.show()

sns.catplot(x="Result", kind="count", palette="ch:.25", data=df)



#*********************************************************************************************************************************************************************************************************************************************************************************************************************************************************************************************************************
#Create a CSV file (for this, create a str with “;” and “\n” as resp. columns/line separators) and then save it on the hard disk drive,in the “data” folder previously created

save_df=df.to_csv("./data/data.csv",sep= "\n" )
save_df2=df.to_csv("./data/data.csv",sep= ";" )
    
print(save_df) 
print(save_df2)

"""
app = Flask(__name__)
@app.route('/')
def home():
   
    text = " ".join(review for review in df["Business name"]) 
    print ("There are {} words in the combination of all review.".format(len(text)))

# Create stopword list: 
    stopwords = set(STOPWORDS)
    stopwords.update(["drink", "now", "wine", "flavor", "flavors"])

# Generate a word cloud image 
    wordcloud = WordCloud(stopwords=stopwords, background_color="white").generate(text)

# Display the generated image:
# the matplotlib way:
    plt.imshow(wordcloud, interpolation='bilinear')
    plt.axis("off")
    plt.show()

    sns.catplot(x="Result", kind="count", palette="ch:.25", data=df)
    print(df)
    return render_template('home.html') 
    

if __name__ == '__main__': 
            app.run(debug = False)
    
#print(home())    

"""

UPLOAD_FOLDER = "./data/"
ALLOWED_EXTENSIONS = {'htlm','pdf'}

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route('/', methods=['GET', 'POST'])
def upload_file():
    if request.method == 'POST':
        # check if the post request has the file part
        if 'file' not in request.files:
            flash('No file part')
            return redirect(request.url)
        file = request.files['file']
        # if user does not select file, browser also
        # submit an empty part without filename
        if file.filename == '':
            flash('No selected file')
            return redirect(request.url)
        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
            return redirect(url_for('uploaded_file',
                                    filename=filename))
    return '''
    <!doctype html>
    <title>Upload new File</title>
    <h1>Upload new File</h1>
    <form method=post enctype=multipart/form-data>
      <input type=file name=file>
      <input type=submit value=Upload>
    </form>
    '''
    
from flask import send_from_directory

@app.route('/python/')
def uploaded_file(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'],
                               filename)

from werkzeug.middleware.shared_data import SharedDataMiddleware
app.add_url_rule('/python/AlimentConfiance.py', 'uploaded_file',
                 build_only=True)
app.wsgi_app = SharedDataMiddleware(app.wsgi_app, {
    '/uploads':  app.config['UPLOAD_FOLDER']
})   


app = Flask(__name__)
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024

print(upload_file())



