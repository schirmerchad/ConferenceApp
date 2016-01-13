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
The supporting methods are defined in conferences.py. They are described briefly below:
<ul>getConferenceSessions(websafeConferenceKey: Given a conference, return all sessions</ul>
<ul>getConferenceSessionsByType(websafeConferenceKey, typeOfSession): Given a conference, return all sessions of a specified type (eg lecture, keynote, workshop)</ul>
<ul>getSessionsBySpeaker(speaker): Given a speaker, return all sessions given by this particular speaker, across all conferences</ul>
<ul>createSession(SessionForm, websafeConferenceKey): Creates a session and relates it to the parent Conference</ul>

<b>Task 2: Add Sessions to User's Wishlist</b>
To fulfill Task #2, two methods were designed that allow a logged in user to add or delete Sessions from a wishlist and view that wishlist. A new property, sessionWishList had to be added to the Profile class to accomodate the new functionality.
The method that adds or deletes a Session was modeled after the Conference method that registers or unregisters a user for a conference. It simply checks that the User and Session exists and appends or removes the Session from that User's wishlist. The two methods are briefly explained below:
<ul>addSessionToWishlist(SessionKey): add/delete the Session from the User's list of Sessions</ul>
<ul>getSessionsInWishlist(): query for all the Sessions in a User's wishlist<ul>

<b>Task 3: Indexes and Queries</b>
To fulfill Task #3, the autogeneration funcationality of index.yaml was tested and then two additional query endpoints were designed and implemeneted. The two additional queries and their endpoints are described below:
<ul>getAllSpeakers()
Returns a list of all the Speakers for all Conferences and Sessions
sessionsByTimeAndType(startTime,typeOfSession)
Returns all Sessions that begin before the time specified by startTime (represented in 24 hour format as HH:MM) and constrained to MATCH the type of Session as specified by the typeOfSession parameter.
4.2 The 2nd part of the requirement posed a specific query-related problem to solve along with a description of how the solution was derived. The problem itself is as follows:

Let’s say that you don't like workshops and you don't like sessions after 7 pm. How would you handle a query for all non-workshop sessions before 7 pm?
What is the problem for implementing this query?
What ways to solve it did you think of?
The main problem in implementing this query is that Datastore will not allow you to do a query with two different inequality operators in the query. For this problem, the query would require that typeOfSession does NOT equal 'workshop' and startTime is less than 19:00:00. Datastore will not allow that sort of query.

To solve this, you could either query for all sessions that do NOT match the session type and then iterate over the results in Python and test the session startTime against the request startTime OR the exact opposite.

I chose to implement it the "first" way described above as I believe that filtering by session type may produce FEWER results than starting out with all the sessions before a given time and then iterating from there.

Requirement #5 specifies that a Featured Speaker capability is to be added to the system. Specifically, some sort of logic is to be created to identify the criteria for a Speaker to be the Featured Speaker and then appropriate code must be written to implement that logic using App Engine's Task Queue capability.
SetFeaturedSpeakerHandler()
Method to determine if there are any featured speakers in the system and if so, set up a MemCache key to hold the list of those speakrers.
Defined in main.py.
getFeaturedSpeaker()
Method to retrieve the list of Featured Speakers that is stored in MemCache so it can be displayed. Defined inconference.py.
Called any time a change of Speakers or Sessions is made.

<h1>Documentation</h1>
<ul>Python v2.7.6</ul>
<ul>oauth2client</ul>
<ul>Flask v0.10.1 and all Flask dependencies</ul>
<ul>SQLite 3</ul>
<ul>SQLalchemy v1.0</ul>
<ul>Boostrap 3</ul>
