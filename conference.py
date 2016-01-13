#!/usr/bin/env python

"""
conference.py -- Udacity conference server-side Python App Engine API;
    uses Google Cloud Endpoints

$Id: conference.py,v 1.25 2014/05/24 23:42:19 wesc Exp wesc $

created by wesc on 2014 apr 21

"""

__author__ = 'wesc+api@google.com (Wesley Chun)'

from datetime import datetime

import endpoints
from protorpc import messages
from protorpc import message_types
from protorpc import remote

from google.appengine.api import memcache
from google.appengine.api import taskqueue
from google.appengine.ext import ndb

from models import *

from utils import getUserId

from settings import WEB_CLIENT_ID
from settings import ANDROID_CLIENT_ID
from settings import IOS_CLIENT_ID
from settings import ANDROID_AUDIENCE

EMAIL_SCOPE = endpoints.EMAIL_SCOPE
API_EXPLORER_CLIENT_ID = endpoints.API_EXPLORER_CLIENT_ID
MEMCACHE_ANNOUNCEMENTS_KEY = "RECENT_ANNOUNCEMENTS"
MEMCACHE_FEATURED_SPEAKER_KEY = "FEATURED_SPEAKER"
ANNOUNCEMENT_TPL = ('Last chance to attend! The following conferences '
                    'are nearly sold out: %s')
# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

DEFAULTS = {
    "city": "Default City",
    "maxAttendees": 0,
    "seatsAvailable": 0,
    "topics": [ "Default", "Topic" ],
}

SESSION_DEFAULTS = {
    "duration": 60,
    "speaker": "Unknown",
}

OPERATORS = {
            'EQ':   '=',
            'GT':   '>',
            'GTEQ': '>=',
            'LT':   '<',
            'LTEQ': '<=',
            'NE':   '!='
            }

FIELDS =    {
            'CITY': 'city',
            'TOPIC': 'topics',
            'MONTH': 'month',
            'MAX_ATTENDEES': 'maxAttendees',
            }

CONF_GET_REQUEST = endpoints.ResourceContainer(
    message_types.VoidMessage,
    websafeConferenceKey=messages.StringField(1),
)

CONF_POST_REQUEST = endpoints.ResourceContainer(
    ConferenceForm,
    websafeConferenceKey=messages.StringField(1),
)

SESSION_GET_REQUEST = endpoints.ResourceContainer(
    message_types.VoidMessage,
    SessionKey=messages.StringField(1),
)

SESSION_POST_REQUEST = endpoints.ResourceContainer(
    SessionForm,
    websafeConferenceKey=messages.StringField(1),
)

SESSION_TYPE_POST_REQUEST = endpoints.ResourceContainer(
    SessionMiniForm,
    websafeConferenceKey=messages.StringField(1),
    typeOfSession=messages.StringField(2),
)

SESSION_SPEAKER_POST_REQUEST = endpoints.ResourceContainer(
    SessionMiniForm,
    speaker=messages.StringField(1),
)


# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
@endpoints.api(name='conference', version='v1', 
    allowed_client_ids=[WEB_CLIENT_ID, API_EXPLORER_CLIENT_ID, ANDROID_CLIENT_ID, IOS_CLIENT_ID],
    scopes=[EMAIL_SCOPE])
class ConferenceApi(remote.Service):
    """Conference API v0.1"""


# - - - Session objects - - - - - - - - - - - - - - - - - - -
    def _copySessionToForm(self, session, name=None):
        """Copy relevant fields from Session to SessionForm!"""
        sf = SessionForm()
        for field in sf.all_fields():
            if hasattr(session, field.name):
                if field.name == "dateTime":
                    s_date = getattr(session,field.name)
                    if s_date:
                        setattr(sf, 'dateTime', s_date.strftime('%y-%m-%d'))
                        setattr(sf, 'startTime', s_date.strftime('%H:%M'))

                elif field.name == "speaker":
                    speaker = getattr(session,field.name)
                    setattr(sf, 'speaker', speaker)

                elif field.name == "typeOfSession":
                    currentType = getattr(session,field.name)
                    if currentType:
                        setattr(sf, field.name, getattr(SessionType, str(currentType)))
                    else:
                        setattr(sf, field.name, getattr(SessionType, 'NOT_SPECIFIED'))

                else:
                    setattr(sf, field.name, getattr(session,field.name))
        sf.check_initialized()
        return sf


    @endpoints.method(message_types.VoidMessage, SessionForms,
            path='getSessions',
            http_method='POST', name='getSessions')
    def getSessions(self, request):
        """Return all sessions!"""
        # will return all sessions
        sessions = Session.query()
        return SessionForms(items=[self._copySessionToForm(session) 
            for session in sessions])
        
        
    @endpoints.method(SESSION_POST_REQUEST, SessionForms,
            path='getConferenceSessions/{websafeConferenceKey}',
            http_method='POST', name='getConferenceSessions')
    def getConferenceSessions(self, request):
        """Return all sessions in a conference!"""
        # get the conference from the websafeConferenceKey
        wsck = request.websafeConferenceKey
        conf = ndb.Key(urlsafe=wsck).get()
        # query sessions by websafeConferenceKey
        sessions = Session.query(ancestor=conf.key)
        return SessionForms(items=[self._copySessionToForm(session) 
            for session in sessions])
        
        
    @endpoints.method(SESSION_TYPE_POST_REQUEST, SessionForms,
            path='getConferenceSessions/{websafeConferenceKey}/{typeOfSession}',
            http_method='POST', name='getConferenceSessionsByType')
    def getConferenceSessionsByType(self, request):
        """Return sessions in a conference queried by type!"""
        # get the conference from the websafeConferenceKey
        wsck = request.websafeConferenceKey
        conf = ndb.Key(urlsafe=wsck).get()
        # query sessions
        sessions = Session.query(ancestor=conf.key)
        # filter sessions by type
        sessionsbyType = sessions.filter(Session.typeOfSession == request.typeOfSession)
        return SessionForms(items=[self._copySessionToForm(session) 
            for session in sessionsbyType])
        
        
    @endpoints.method(SESSION_SPEAKER_POST_REQUEST, SessionForms,
            path='getSpeakerSessions/{speaker}',
            http_method='POST', name='getSessionsBySpeaker')
    def getSessionsBySpeaker(self, request):
        """Return sessions in a conference queried by speaker!"""
        # get the speaker requested
        speak = request.speaker
        # query sessions by requested speaker
        sessions = Session.query(Session.speaker == speak)
        return SessionForms(items=[self._copySessionToForm(session) 
            for session in sessions])


    def _createSessionObject(self, request):
        """Create or update a Session object, returning SessionForm/request!"""
        user = endpoints.get_current_user()

        # require user to be registered and logged in to add a session
        if not user:
            raise endpoints.UnauthorizedException("Please log in to create a Session!")
        user_id = getUserId(user)

        # session must be given at least a name
        if not request.name:
            raise endpoints.BadRequestException("You must input a Session Name!")

        # fetch and check conference
        conf = ndb.Key(urlsafe=request.websafeConferenceKey).get()

        # check that conference exists
        if not conf:
            raise endpoints.NotFoundException(
                'No conference exists with key: %s' % request.websafeConferenceKey)

        # validate that user is owner of conference
        if user_id != conf.organizerUserId:
            raise endpoints.ForbiddenException(
                'You must be the Conference owner to create a session!')    
        data = {field.name: getattr(request, field.name) for field in request.all_fields()}

        # convert date and time fields to the correct types
        if data['dateTime']:
            s_date = datetime.strptime(data['dateTime'], '%Y-%m-%d %H:%M')
            data['dateTime'] = s_date
            data['startTime'] = datetime.strftime(s_date, '%H:%M')

        # set type of session, if not supplied set it to Lecture
        if data['typeOfSession']:
            data['typeOfSession'] = str(data['typeOfSession'])
        else:
            data['typeOfSession'] = 'Lecture'     
        del data['websafeConferenceKey']  

        # add default values for those missing (both data model & outbound Message)
        for df in SESSION_DEFAULTS:
            if data[df] in (None, []):
                data[df] = SESSION_DEFAULTS[df]
                setattr(request, df, SESSION_DEFAULTS[df])
        
        s_id = Conference.allocate_ids(size=1, parent=conf.key)[0]
        s_key = ndb.Key(Session, s_id, parent=conf.key)
        
        data['key'] = s_key
        
        Session(**data).put()
        # check if the speaker is speaking at more than one session
        # at the conference. If true then add a Memcache entry for them
        sess = Session.query(ancestor=conf.key)
        speakSessions = sess.filter(Session.speaker == data['speaker'])
        sessionCount = speakSessions.count()

        if sessionCount > 1:
            speaker = data['speaker']
            taskqueue.add(
                params={'speakerName': speaker},
                url='/tasks/add_featured_speaker')   
        return request
        
    
    @endpoints.method(SessionForm, SessionForm, 
            path='createSession', http_method='POST', 
            name='createSession')
    def createSession(self, request):
        """Create a new Session!"""
        return self._createSessionObject(request)           

    
# - - - Conference objects - - - - - - - - - - - - - - - - -
    def _copyConferenceToForm(self, conf, displayName):
        """Copy relevant fields from Conference to ConferenceForm"""
        cf = ConferenceForm()
        for field in cf.all_fields():
            if hasattr(conf, field.name):
                # convert Date to date string; just copy others
                if field.name.endswith('Date'):
                    setattr(cf, field.name, str(getattr(conf, field.name)))
                else:
                    setattr(cf, field.name, getattr(conf, field.name))
            elif field.name == "websafeKey":
                setattr(cf, field.name, conf.key.urlsafe())
        if displayName:
            setattr(cf, 'organizerDisplayName', displayName)
        cf.check_initialized()
        return cf


    def _createConferenceObject(self, request):
        """Create or update Conference object, returning ConferenceForm/request."""
        # preload necessary data items
        user = endpoints.get_current_user()
        if not user:
            raise endpoints.UnauthorizedException('Authorization required')
        user_id = getUserId(user)

        if not request.name:
            raise endpoints.BadRequestException("Conference 'name' field required")

        # copy ConferenceForm/ProtoRPC Message into dict
        data = {field.name: getattr(request, field.name) for field in request.all_fields()}
        del data['websafeKey']
        del data['organizerDisplayName']

        # add default values for those missing (both data model & outbound Message)
        for df in DEFAULTS:
            if data[df] in (None, []):
                data[df] = DEFAULTS[df]
                setattr(request, df, DEFAULTS[df])

        # convert dates from strings to Date objects; set month based on start_date
        if data['startDate']:
            data['startDate'] = datetime.strptime(data['startDate'][:10], "%Y-%m-%d").date()
            data['month'] = data['startDate'].month
        else:
            data['month'] = 0
        if data['endDate']:
            data['endDate'] = datetime.strptime(data['endDate'][:10], "%Y-%m-%d").date()

        # set seatsAvailable to be same as maxAttendees on creation
        if data["maxAttendees"] > 0:
            data["seatsAvailable"] = data["maxAttendees"]
        # generate Profile Key based on user ID and Conference
        # ID based on Profile key get Conference key from ID
        p_key = ndb.Key(Profile, user_id)
        c_id = Conference.allocate_ids(size=1, parent=p_key)[0]
        c_key = ndb.Key(Conference, c_id, parent=p_key)
        data['key'] = c_key
        data['organizerUserId'] = request.organizerUserId = user_id

        # create Conference, send email to organizer confirming
        # creation of Conference & return (modified) ConferenceForm
        # Conference(**data).put()
        Conference(**data).put()
        taskqueue.add(params={'email': user.email(),
            'conferenceInfo': repr(request)},
            url='/tasks/send_confirmation_email'
        )
        return request


    @ndb.transactional()
    def _updateConferenceObject(self, request):
        user = endpoints.get_current_user()
        if not user:
            raise endpoints.UnauthorizedException('Authorization required')
        user_id = getUserId(user)

        # copy ConferenceForm/ProtoRPC Message into dict
        data = {field.name: getattr(request, field.name) for field in request.all_fields()}

        # update existing conference
        conf = ndb.Key(urlsafe=request.websafeConferenceKey).get()
        # check that conference exists
        if not conf:
            raise endpoints.NotFoundException(
                'No conference found with key: %s' % request.websafeConferenceKey)

        # check that user is owner
        if user_id != conf.organizerUserId:
            raise endpoints.ForbiddenException(
                'Only the owner can update the conference.')

        # Not getting all the fields, so don't create a new object; just
        # copy relevant fields from ConferenceForm to Conference object
        for field in request.all_fields():
            data = getattr(request, field.name)
            # only copy fields where we get data
            if data not in (None, []):
                # special handling for dates (convert string to Date)
                if field.name in ('startDate', 'endDate'):
                    data = datetime.strptime(data, "%Y-%m-%d").date()
                    if field.name == 'startDate':
                        conf.month = data.month
                # write to Conference object
                setattr(conf, field.name, data)
        conf.put()
        prof = ndb.Key(Profile, user_id).get()
        return self._copyConferenceToForm(conf, getattr(prof, 'displayName'))


    @endpoints.method(ConferenceForm, ConferenceForm, path='conference',
            http_method='POST', name='createConference')
    def createConference(self, request):
        """Create new conference."""
        return self._createConferenceObject(request)


    @endpoints.method(CONF_POST_REQUEST, ConferenceForm,
            path='conference/{websafeConferenceKey}',
            http_method='PUT', name='updateConference')
    def updateConference(self, request):
        """Update conference w/provided fields & return w/updated info."""
        return self._updateConferenceObject(request)


    @endpoints.method(CONF_GET_REQUEST, ConferenceForm,
            path='conference/{websafeConferenceKey}',
            http_method='GET', name='getConference')
    def getConference(self, request):
        """Return requested conference (by websafeConferenceKey)."""
        # get Conference object from request; bail if not found
        conf = ndb.Key(urlsafe=request.websafeConferenceKey).get()
        if not conf:
            raise endpoints.NotFoundException(
                'No conference found with key: %s' % request.websafeConferenceKey)
        prof = conf.key.parent().get()
        # return ConferenceForm
        return self._copyConferenceToForm(conf, getattr(prof, 'displayName'))
        

    @endpoints.method(message_types.VoidMessage, ConferenceForms,
            path='getConferencesCreated',
            http_method='POST', name='getConferencesCreated')
    def getConferencesCreated(self, request):
        """Return conferences created by user."""
        # make sure user is authed
        user = endpoints.get_current_user()
        if not user:
            raise endpoints.UnauthorizedException('Authorization required')
        user_id =  getUserId(user)

        # create ancestor query for all key matches for this user
        confs = Conference.query(ancestor=ndb.Key(Profile, user_id))
        prof = ndb.Key(Profile, user_id).get()
        # return set of ConferenceForm objects per Conference
        return ConferenceForms(items=[self._copyConferenceToForm(conf, 
            getattr(prof, 'displayName')) for conf in confs])


    def _getQuery(self, request):
        """Return formatted query from the submitted filters."""
        q = Conference.query()
        inequality_filter, filters = self._formatFilters(request.filters)

        # If exists, sort on inequality filter first
        if not inequality_filter:
            q = q.order(Conference.name)
        else:
            q = q.order(ndb.GenericProperty(inequality_filter))
            q = q.order(Conference.name)

        for filtr in filters:
            if filtr["field"] in ["month", "maxAttendees"]:
                filtr["value"] = int(filtr["value"])
            formatted_query = ndb.query.FilterNode(filtr["field"], filtr["operator"], filtr["value"])
            q = q.filter(formatted_query)
        return q


    def _formatFilters(self, filters):
        """Parse, check validity and format user supplied filters."""
        formatted_filters = []
        inequality_field = None

        for f in filters:
            filtr = {field.name: getattr(f, field.name) for field in f.all_fields()}

            try:
                filtr["field"] = FIELDS[filtr["field"]]
                filtr["operator"] = OPERATORS[filtr["operator"]]
            except KeyError:
                raise endpoints.BadRequestException("Filter contains invalid field or operator.")

            # Every operation except "=" is an inequality
            if filtr["operator"] != "=":
                # check if inequality operation has been used in previous filters
                # disallow the filter if inequality was performed on a different field before
                # track the field on which the inequality operation is performed
                if inequality_field and inequality_field != filtr["field"]:
                    raise endpoints.BadRequestException('Inequality filter is allowed on only one field.')
                else:
                    inequality_field = filtr["field"]

            formatted_filters.append(filtr)
        return (inequality_field, formatted_filters)


    @endpoints.method(ConferenceQueryForms, ConferenceForms,
            path='queryConferences',
            http_method='POST',
            name='queryConferences')
    def queryConferences(self, request):
        """Query for conferences."""
        conferences = self._getQuery(request)

        # need to fetch organiser displayName from profiles
        # get all keys and use get_multi for speed
        organisers = [(ndb.Key(Profile, conf.organizerUserId)) for conf in conferences]
        profiles = ndb.get_multi(organisers)

        # put display names in a dict for easier fetching
        names = {}
        for profile in profiles:
            names[profile.key.id()] = profile.displayName

        # return individual ConferenceForm object per Conference
        return ConferenceForms(
                items=[self._copyConferenceToForm(conf, 
                    names[conf.organizerUserId]) for conf in conferences])


# - - - Profile objects - - - - - - - - - - - - - - - - - - -
    def _copyProfileToForm(self, prof):
        """Copy relevant fields from Profile to ProfileForm."""
        # copy relevant fields from Profile to ProfileForm
        pf = ProfileForm()
        for field in pf.all_fields():
            if hasattr(prof, field.name):
                # convert t-shirt string to Enum; just copy others
                if field.name == 'teeShirtSize':
                    setattr(pf, field.name, getattr(TeeShirtSize, 
                    getattr(prof, field.name)))
                else:
                    setattr(pf, field.name, getattr(prof, field.name))
        pf.check_initialized()
        return pf


    def _getProfileFromUser(self):
        """Return user Profile from datastore, creating new one if non-existent."""
        # make sure user is authed
        user = endpoints.get_current_user()
        if not user:
            raise endpoints.UnauthorizedException('Authorization required')

        # get Profile from datastore
        user_id = getUserId(user)
        p_key = ndb.Key(Profile, user_id)
        profile = p_key.get()
        # create new Profile if not there
        if not profile:
            profile = Profile(
                key = p_key,
                displayName = user.nickname(),
                mainEmail= user.email(),
                teeShirtSize = str(TeeShirtSize.NOT_SPECIFIED),
            )
            profile.put()

        return profile      # return Profile


    def _doProfile(self, save_request=None):
        """Get user Profile and return to user, possibly updating it first."""
        # get user Profile
        prof = self._getProfileFromUser()

        # if saveProfile(), process user-modifyable fields
        if save_request:
            for field in ('displayName', 'teeShirtSize'):
                if hasattr(save_request, field):
                    val = getattr(save_request, field)
                    if val:
                        setattr(prof, field, str(val))
            prof.put()

        # return ProfileForm
        return self._copyProfileToForm(prof)


    @endpoints.method(message_types.VoidMessage, ProfileForm,
            path='profile', http_method='GET', name='getProfile')
    def getProfile(self, request):
        """Return user profile."""
        return self._doProfile()


    @endpoints.method(ProfileMiniForm, ProfileForm,
            path='profile', http_method='POST', name='saveProfile')
    def saveProfile(self, request):
        """Update & return user profile."""
        return self._doProfile(request)


# - - - Announcements - - - - - - - - - - - - - - - - - - - -             
    @staticmethod
    def _cacheAnnouncement():
        """Create Announcement & assign to memcache; used by
        memcache cron job & putAnnouncement().
        """
        confs = Conference.query(ndb.AND(
            Conference.seatsAvailable <= 5,
            Conference.seatsAvailable > 0)
        ).fetch(projection=[Conference.name])

        if confs:
            # If there are almost sold out conferences,
            # format announcement and set it in memcache
            announcement = ANNOUNCEMENT_TPL % (
                ', '.join(conf.name for conf in confs))
            memcache.set(MEMCACHE_ANNOUNCEMENTS_KEY, announcement)
        else:
            # If there are no sold out conferences,
            # delete the memcache announcements entry
            announcement = ""
            memcache.delete(MEMCACHE_ANNOUNCEMENTS_KEY)

        return announcement


    @endpoints.method(message_types.VoidMessage, StringMessage,
            path='conference/announcement/get',
            http_method='GET', name='getAnnouncement')
    def getAnnouncement(self, request):
        """Return Announcement from memcache."""
        return StringMessage(data=memcache.get(MEMCACHE_ANNOUNCEMENTS_KEY) or "")

        
# - - - Registration - - - - - - - - - - - - - - - - - - - -
    @ndb.transactional(xg=True)
    def _conferenceRegistration(self, request, reg=True):
        """Register/unregister a user for a selected conference"""
        retval = None
        prof = self._getProfileFromUser() # get user Profile

        # check if conf exists given websafeConfKey
        # get conference; check that it exists
        wsck = request.websafeConferenceKey
        conf = ndb.Key(urlsafe=wsck).get()
        if not conf:
            raise endpoints.NotFoundException('No conference found with key: %s' % wsck)

        # register
        if reg:
            # check if user already registered otherwise add
            if wsck in prof.conferenceKeysToAttend:
                raise ConflictException('You have already registered for this conference')

            # check if seats avail
            if conf.seatsAvailable <= 0:
                raise ConflictException(
                    "There are no seats available.")

            # register user, take away one seat
            prof.conferenceKeysToAttend.append(wsck)
            conf.seatsAvailable -= 1
            retval = True

        # unregister
        else:
            # check if user already registered
            if wsck in prof.conferenceKeysToAttend:

                # unregister user, add back one seat
                prof.conferenceKeysToAttend.remove(wsck)
                conf.seatsAvailable += 1
                retval = True
            else:
                retval = False

        # write things back to the datastore & return
        prof.put()
        conf.put()
        return BooleanMessage(data=retval)


    @endpoints.method(message_types.VoidMessage, ConferenceForms,
            path='conferences/attending',
            http_method='GET', name='getConferencesToAttend')
    def getConferencesToAttend(self, request):
        """Get list of conferences that user has registered for."""
        prof = self._getProfileFromUser() # get user Profile
        conf_keys = [ndb.Key(urlsafe=wsck) for wsck in prof.conferenceKeysToAttend]
        conferences = ndb.get_multi(conf_keys)

        # get organizers
        organisers = [ndb.Key(Profile, conf.organizerUserId) for conf in conferences]
        profiles = ndb.get_multi(organisers)

        # put display names in a dict for easier fetching
        names = {}
        for profile in profiles:
            names[profile.key.id()] = profile.displayName

        # return set of ConferenceForm objects per Conference
        return ConferenceForms(items=[self._copyConferenceToForm(conf, 
            names[conf.organizerUserId]) for conf in conferences])


    @endpoints.method(CONF_GET_REQUEST, BooleanMessage,
            path='conference/{websafeConferenceKey}',
            http_method='POST', name='registerForConference')
    def registerForConference(self, request):
        """Register user for selected conference."""
        return self._conferenceRegistration(request)


    @endpoints.method(CONF_GET_REQUEST, BooleanMessage,
            path='conference/{websafeConferenceKey}',
            http_method='DELETE', name='unregisterFromConference')
    def unregisterFromConference(self, request):
        """Unregister user for selected conference."""
        return self._conferenceRegistration(request, reg=False)
        

# - - - Wishlist - - - - - - - - - - - - - - - - - - - - - - -
    @ndb.transactional(xg=True)
    def _manageWishlist(self, request, reg=True):
        """Register/unregister a user for a selected session!"""
        retval = None
        prof = self._getProfileFromUser() # get user Profile
        # check if session exists given the SessionfKey
        sk = request.SessionKey
        sess = ndb.Key(urlsafe=sk).get()
        if not sess:
            raise endpoints.NotFoundException("No session could be found with key: %s" % sk)

        if reg:
            # check if the session is already in the users wishlist
            if sk in prof.sessionWishlist:
                raise ConflictException("You have already registered for this session!")

            prof.sessionWishlist.append(sk)
            retval = True

        else:

            if sk in prof.sessionWishlist:
                prof.sessionWishlist.remove(sk)
                retval = True
            else:
                retval = False

        # write things back to the datastore & return
        prof.put()
        return BooleanMessage(data=retval)


    @endpoints.method(SESSION_GET_REQUEST, BooleanMessage,
            path='session/{SessionKey}',
            http_method='POST', name='addSessionToWishlist')
    def addToWishlist(self, request):
        """Add session to wishlist!"""
        return self._manageWishlist(request)

        
    @endpoints.method(SESSION_GET_REQUEST, BooleanMessage,
            path='session/{SessionKey}',
            http_method='DELETE', name='deleteSessionFromWishlist')
    def deleteFromWishlist(self, request):
        """Delete session from wishlist!"""
        return self._manageWishlist(request, reg=False)

        
    @endpoints.method(message_types.VoidMessage, SessionForms,
            path='wishlist',
            http_method='POST', name='getSessionsInWishlist')
    def getSessionsInWishlist(self, request):
        """Return the wishlist for user!"""
        prof = self._getProfileFromUser() # get user Profile
        session_keys = [ndb.Key(urlsafe=wsck) for wsck in prof.sessionWishlist]
        sessions = ndb.get_multi(session_keys)
        return SessionForms (items=[self._copySessionToForm(session) 
            for session in sessions])


# - - - Indexes and Queries - - - - - - - - - - - - - - - - - - - - - - - 
# This query shows conferences that have less than 5 slots available
    @endpoints.method(message_types.VoidMessage, ConferenceForms,
            path='lessThanFiveSeats',
            http_method='POST', name='lessThanFiveSeats')
    def getlowReg(self, request):
        """Return conferences that have less than five slots available!"""
        confList = []
        confs = Conference.query()
        # loop through all conferences and push to list
        for conf in confs:
            maxAttendees = conf.maxAttendees
            seatsAvailable = conf.seatsAvailable
            if seatsAvailable < 5:
                confList += [conf]
        
        return ConferenceForms(
            items=[self._copyConferenceToForm(conf, getattr(conf.key.parent().get(), 'displayName')) 
            for conf in confList])


# This query shows conferences that have a 'Workshop'
    @endpoints.method(message_types.VoidMessage, ConferenceForms,
            path='confWithWorkshop',
            http_method='POST', name='confWithWorkshop')
    def getNoSessions(self, request):
        """Returns conferences that have workshops!"""
        confList = []
        confs = Conference.query()
        # loop through all conferences and push to list
        for conf in confs:
            sessions = Session.query(ancestor=conf.key)
            for session in sessions:
                if session.typeOfSession == 'Workshop':
                    if conf not in confList:
                        confList += [conf]
        
        return ConferenceForms(
            items=[self._copyConferenceToForm(conf, getattr(conf.key.parent().get(), 'displayName')) 
            for conf in confList])

        
# - - - Featured speaker - - - - - - - - - - - - - - - - - - -
    # get the featured speaker
    @endpoints.method(message_types.VoidMessage, StringMessage,
            path='featuredSpeaker',
            http_method='GET', name='getFeaturedSpeaker')
    def getFeaturedSpeaker(self, request):
        """Display memcache message for featured speaker!"""
        return StringMessage(data=memcache.get(MEMCACHE_FEATURED_SPEAKER_KEY) or "")

api = endpoints.api_server([ConferenceApi]) # register API