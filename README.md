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

<h1>Design Description</h1>
<b>Task 1: Add Sessions to a Conference</b>
To fulfill task #1, a session class was created as well several methods to support Session actions, such as creating and removing sessions. The Session class is defined in models.py. I did not go ahead and create a Speaker class. I chose to make the speaker attribute of eash session a ndb.StringProperty and structure my queries in that way. I would like to implement a Speaker class sometime in the future. I structured the Session class methods after the Conference methods and made sure that each Session is implemented as a child to a Conference. TypeOfSession uses the Enum property, like the t-shirt size in the Profile object, to store the value as an integer.
dateTime is modeled as a dateTime property to allow for chronological and date oriented ordering. The startTime is represented as a Time property to allow for similar sorting in natural chronological order. 
The supporting methods are defined in conferences.py. They are described briefly below:
<ul>getConferenceSessions(websafeConferenceKey: Given a conference, return all sessions</ul>
<ul>getConferenceSessionsByType(websafeConferenceKey, typeOfSession): Given a conference, return all sessions of a specified type (eg lecture, keynote, workshop)</ul>
<ul>getSessionsBySpeaker(speaker): Given a speaker, return all sessions given by this particular speaker, across all conferences</ul>
<ul>createSession(SessionForm, websafeConferenceKey): Creates a session and relates it to the parent Conference</ul>

<b>Task 2: Add Sessions to User's Wishlist</b>
To fulfill Task #2, multiple methods were designed that allow a logged in user to add or delete Sessions from a wishlist and view that wishlist. A new property, sessionWishList had to be added to the Profile class to accomodate the new functionality.
The method that adds or deletes a Session was modeled after the Conference method that registers or unregisters a user for a conference. It simply checks that the User and Session exists and appends or removes the Session from that User's wishlist. The methods are briefly explained below:
<ul>addToWishlist(): Add the Session from the User's list of Sessions</ul>
<ul>deleteFromWishlist(): Delete the Session from the User's list of Sessions</ul>
<ul>getSessionsInWishlist(): Query for all the Sessions in a User's wishlist</ul>

<b>Task 3: Indexes and Queries</b>
To fulfill Task #3, the autogeneration funcationality of index.yaml was tested and then two additional query endpoints were designed and implemeneted. The two additional queries and their endpoints are described below:
<ul>lessThanFiveSeats(): Returns a list of all the Conferences that only have 4 or less seats remaining</ul>
<ul>sessionIsWorkshop(): Returns all sessions that are workshops</ul>

The second part of Task #3 asks for a written answer to a specific query problem. The problem with the requested query is that, according to the Datastore Python Queries documentation "inequality filters are limited to at most one property." The proposed query has two inequality operators. To solve this issue one would need to query all sessions that are not Workshops and then iterate over the query results to filter out Sessions after 7pm. 

<b>Task 4: Add a Task</b>
To fulfill Task #4, a method was written to determine if a Speaker is speaking at more than one conference and if that is true, add a Memcache entry that features the Speaker's name. Everytime a Session is created the code checks whether or not the Session Speaker should be added as the newest featured Speaker.
First, an endpoint method was implemented:
<ul>getFeaturedSpeaker(): Returns the featured speaker and stores it in the Memcache</ul>
Second, a handler for Memcache and task queue was created in main.py:
<ul>SetFeaturedSpeakerHandler()</ul>

<h1>Documentation</h1>
<ul>https://cloud.google.com/appengine/docs/python/</ul>
<ul>https://cloud.google.com/appengine/downloads#Google_App_Engine_SDK_for_Python</ul>
<ul>https://cloud.google.com/appengine/docs/python/datastore/queries?hl=en#Python_Restrictions_on_queries</ul>
