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
To fulfill task #1, a session class was created as well several methods to support Session actions, such as creating and removing sessions. The Session class is defined in models.py.
The supporting methods are defined in conferences.py. They are described briefly below:
<ul>getConferenceSessions(websafeConferenceKey: Given a conference, return all sessions</ul>
<ul>getConferenceSessionsByType(websafeConferenceKey, typeOfSession): Given a conference, return all sessions of a specified type (eg lecture, keynote, workshop)</ul>
<ul>getSessionsBySpeaker(speaker): Given a speaker, return all sessions given by this particular speaker, across all conferences</ul>
<ul>createSession(SessionForm, websafeConferenceKey): Creates a session and relates it to the parent Conference it is part of</ul>

<b>Task 2</b>
Requirement 3 defines the notion of a Session Wishlist for a user. The idea is that a user can put various Sessions on their wishlist to help them remember the sessions they are interested in.
To support this functionality, the Profile (represents a user in the system) class required modification:

add field sessionKeysWishList as a list (repeated=True) of Session keys the user has added to their wishlist.
Further, two Endpoints methods were required to support operations:

addSessionToWishlist(SessionKey)
adds the session to the user's list of sessions they are interested in attending
getSessionsInWishlist()
query for all the sessions in a conference that the user is interested in
Requirement 4 specified that two new queries (of the student's choice) be created and that a specific query "problem" be solved by the student.
4.1 To satisfy the first part of the requirement, the following two queries and their associated Endpoint methods were created:

getAllSpeakers()
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
