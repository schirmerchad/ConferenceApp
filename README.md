# Fullstack-project4
Project #4 for the Udacity FSND. An app and API created with Python and Google Cloud Endpoints.

This project uses Python and Google App Engine to develop a conference management app and API. Data management is provided using the Google Cloud Datastore and OAuth2 is used as the authentication framework. Google Cloud Endpoints provides the tools, libraries, and capabilities for the API backend.

<h1>Description</h1>
This app/API allows a logged in user to organize conferences and conference sessions. Conferences are stored in a database and can be queried and filtered as per the user’s discretion. The app also has built in functionality to allow users to register for conferences and store upcoming conferences in a wish list.

<h1>Run the Code</h1>
<b>Requirements for running the code:</b>
<ul>Google account</ul>
<ul>A new Google App Engine (GAE) project</ul>
<ul>The API Keys</ul>
<ul>GAE and the Google Cloud Python SDK</ul>

<b>Steps to run the code:</b>
<ul>Create a new Google App Engine (GAE) project using the Google Developers Console</ul>
<ul>Generate the Credentials for the project. For this project, the only Application Key you need is the Browser Key</ul>
<ul>Download this repo to your local machine</ul>
<ul>Replace the application ID in settings.py and app.yaml with the generated Application ID from GAE</ul>
<ul>Run the code locally using Google's Development Server</ul>

<h1>Get the Code</h1>
git clone https://github.com/schirmerchad/fullstack-project3

<h1>Dependencies</h1>
<ul>Python v2.7.6</ul>
<ul>oauth2client</ul>
<ul>Flask v0.10.1 and all Flask dependencies</ul>
<ul>SQLite 3</ul>
<ul>SQLalchemy v1.0</ul>
<ul>Boostrap 3</ul>

<h1>Run</h1>
<ol>Install Vagrant and Virtual Box</ol>
<ol>Launch Vagrant VM</ol>
<ol>Create the database by running 'python database_setup.py'</ol>
<ol>Populate the database with one meal and one user by running 'python mealdatabase.py'</ol>
<ol>Start webserver by running 'python project.py'</ol>

<h1>JSON enpoints</h1>
JSON enpoints are available. To access them, visit the following URLs.
<ol>'/meals/json' for simple details on all the meals in the database</ol>
<ol>'/meals/<int:meal_id>/json' for more detailed information on one meal</ol>
