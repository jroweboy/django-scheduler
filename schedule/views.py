import datetime
from vobject.icalendar import utc
from urllib import quote
from django.contrib.auth.decorators import login_required

from django.shortcuts import render_to_response, get_object_or_404, render
from django.utils import timezone
from django.http import HttpResponseRedirect, Http404, HttpResponseForbidden, HttpResponse, HttpResponseBadRequest
from django.template import RequestContext
from django.core.urlresolvers import reverse
from django.shortcuts import render
from django.utils.decorators import method_decorator
from django.views.generic.edit import DeleteView

from schedule.conf.settings import GET_EVENTS_FUNC, OCCURRENCE_CANCEL_REDIRECT, GET_EVENTS_AJAX
from schedule.forms import EventForm, OccurrenceForm
from schedule.models import Calendar, Occurrence, Event
from schedule.periods import weekday_names
from schedule.utils import check_event_permissions, coerce_date_dict

# TODO: make guardian optional for those that don't care about calendar permissions
from guardian.shortcuts import get_objects_for_user

# load in json as perscribed at http://stackoverflow.com/a/712799/745719
try: import simplejson as json
except ImportError: import json

def calendars_for_user(request, template='schedule/calendar.html'):
    """
    This view is used to render all of the calendars that a user has permission to 
    view. It will then render the calendar-functions.js to include their permissions
    """
    pass

@login_required
def calendar(request, calendar_slug, template='schedule/calendar.html'):
    """
    TODO: This function is being repurposed. Explain what the changes are and move the
    original information this function provided elsewhere

    This view returns a calendar.  This view should be used if you are
    interested in the meta data of a calendar, not if you want to display a
    calendar.  It is suggested that you use calendar_by_periods if you would
    like to display a calendar.

    Context Variables:

    ``calendar``
        The Calendar object designated by the ``calendar_slug``.
    """

    calendar = get_object_or_404(Calendar, slug=calendar_slug)

    # TODO Support per calendar allow_anon permissions
    if request.user.has_perm('view_calendar',calendar):
        js = render_to_response('schedule/calendar-functions.js',
                            {},
                            context_instance=RequestContext(request),
                            content_type='application/json')
        event_form = EventForm()
        return render(request, template, 
                    {
                        "calendar": calendar, 
                        "calendar_functions": js,
                        "event_form": event_form,
                    })
    return HttpResponseForbidden()

def calendar_ajax_view(request, calendar_slug, periods=None,):
    """ 
    This view was created to draw events for a period and return them
    in JSON format to full calendar
    """

    calendar = get_object_or_404(Calendar, slug=calendar_slug)
    # get the timestamp from start and end 
    try :
        start = datetime.datetime.fromtimestamp(float(request.POST['start']), utc)
        end = datetime.datetime.fromtimestamp(float(request.POST['end']), utc)
    except:
        print "Raised that 404!"
        raise Http404

    event_list = GET_EVENTS_AJAX(request, calendar, start, end)

    occurrence_list = [ occurence for event in event_list 
                                  for occurence in event.get_occurrences(start, end)]
    #import pdb; pdb.set_trace()
    #import calendar
    # convert the start and end times to as standard format that Full Calendar understands
    for a in occurrence_list:
        a.start = a.start.isoformat() #calendar.timegm(a.start.utctimetuple())
        a.end = a.end.isoformat()
    return render_to_response('schedule/event_feed.js',
                                context_instance=RequestContext(request, 
                                    { 'events': occurrence_list, }
                                ),
                                mimetype='application/json')

def ajax_create_event(request, calendar_slug):
    if not request.is_ajax() or not request.POST:
        return HttpResponseBadRequest()
    form = EventForm(data=request.POST)
    if form.is_valid():
        event = form.save(commit=False)
        import pdb; pdb.set_trace()
        event.creator = request.user
        calendar = get_object_or_404(Calendar, slug=calendar_slug)
        event.calendar = calendar
        event.save()
        return HttpResponse()
    else:
        return HttpResponseBadRequest(json.dumps(form.errors), content_type="application/json")

def ajax_edit_event(request, calendar_slug):
    return HttpResponse(json.dumps({"success": True}), content_type="application/json")

def ajax_delete_event(request, calendar_slug):
    return HttpResponse(json.dumps({"success": True}), content_type="application/json")

def calendar_by_periods(request, calendar_slug, periods=None,
    template_name="schedule/calendar_by_period.html"):
    """
    This view is for getting a calendar, but also getting periods with that
    calendar.  Which periods you get, is designated with the list periods. You
    can designate which date you the periods to be initialized to by passing
    a date in request.GET. See the template tag ``query_string_for_date``

    Context Variables

    ``date``
        This was the date that was generated from the query string.

    ``periods``
        this is a dictionary that returns the periods from the list you passed
        in.  If you passed in Month and Day, then your dictionary would look
        like this

        {
            'month': <schedule.periods.Month object>
            'day':   <schedule.periods.Day object>
        }

        So in the template to access the Day period in the context you simply
        use ``periods.day``.

    ``calendar``
        This is the Calendar that is designated by the ``calendar_slug``.

    ``weekday_names``
        This is for convenience. It returns the local names of weekedays for
        internationalization.

    """
    calendar = get_object_or_404(Calendar, slug=calendar_slug)
    date = coerce_date_dict(request.GET)
    if date:
        try:
            date = datetime.datetime(**date)
        except ValueError:
            raise Http404
    else:
        date = timezone.now()
    event_list = GET_EVENTS_FUNC(request, calendar)
    period_objects = dict([(period.__name__.lower(), period(event_list, date)) for period in periods])
    return render_to_response(template_name,{
            'date': date,
            'periods': period_objects,
            'calendar': calendar,
            'weekday_names': weekday_names,
            'here':quote(request.get_full_path()),
        },context_instance=RequestContext(request),)

def event(request, event_id, template_name="schedule/event.html"):
    """
    This view is for showing an event. It is important to remember that an
    event is not an occurrence.  Events define a set of reccurring occurrences.
    If you would like to display an occurrence (a single instance of a
    recurring event) use occurrence.

    Context Variables:

    event
        This is the event designated by the event_id

    back_url
        this is the url that referred to this view.
    """
    event = get_object_or_404(Event, id=event_id)
    #back_url = request.META.get('HTTP_REFERER', None)
    try:
        cal = event.calendar_set.get()
    except:
        cal = None
    return render(request, template_name, {
        "event": event,
        "back_url" : None,
    })
    #, context_instance=RequestContext(request))

def occurrence(request, event_id,
    template_name="schedule/occurrence.html", *args, **kwargs):
    """
    This view is used to display an occurrence.

    Context Variables:

    ``event``
        the event that produces the occurrence

    ``occurrence``
        the occurrence to be displayed

    ``back_url``
        the url from which this request was refered
    """
    event, occurrence = get_occurrence(event_id, *args, **kwargs)
    back_url = request.META.get('HTTP_REFERER', None)
    return render_to_response(template_name, {
        'event': event,
        'occurrence': occurrence,
        'back_url': back_url,
    }, context_instance=RequestContext(request))


@check_event_permissions
def edit_occurrence(request, event_id,
    template_name="schedule/edit_occurrence.html", *args, **kwargs):
    event, occurrence = get_occurrence(event_id, *args, **kwargs)
    next = kwargs.get('next', None)
    form = OccurrenceForm(data=request.POST or None, instance=occurrence)
    if form.is_valid():
        occurrence = form.save(commit=False)
        occurrence.event = event
        occurrence.save()
        next = next or get_next_url(request, occurrence.get_absolute_url())
        return HttpResponseRedirect(next)
    next = next or get_next_url(request, occurrence.get_absolute_url())
    return render_to_response(template_name, {
        'form': form,
        'occurrence': occurrence,
        'next':next,
    }, context_instance=RequestContext(request))


@check_event_permissions
def cancel_occurrence(request, event_id,
    template_name='schedule/cancel_occurrence.html', *args, **kwargs):
    """
    This view is used to cancel an occurrence. If it is called with a POST it
    will cancel the view. If it is called with a GET it will ask for
    conformation to cancel.
    """
    event, occurrence = get_occurrence(event_id, *args, **kwargs)
    next = kwargs.get('next',None) or get_next_url(request, event.get_absolute_url())
    if request.method != "POST":
        return render_to_response(template_name, {
            "occurrence": occurrence,
            "next":next,
        }, context_instance=RequestContext(request))
    occurrence.cancel()
    return HttpResponseRedirect(next)


def get_occurrence(event_id, occurrence_id=None, year=None, month=None,
    day=None, hour=None, minute=None, second=None):
    """
    Because occurrences don't have to be persisted, there must be two ways to
    retrieve them. both need an event, but if its persisted the occurrence can
    be retrieved with an id. If it is not persisted it takes a date to
    retrieve it.  This function returns an event and occurrence regardless of
    which method is used.
    """
    if(occurrence_id):
        occurrence = get_object_or_404(Occurrence, id=occurrence_id)
        event = occurrence.event
    elif(all((year, month, day, hour, minute, second))):
        event = get_object_or_404(Event, id=event_id)
        occurrence = event.get_occurrence(
            datetime.datetime(int(year), int(month), int(day), int(hour),
                int(minute), int(second)))
        if occurrence is None:
            raise Http404
    else:
        raise Http404
    return event, occurrence


@check_event_permissions
def create_or_edit_event(request, calendar_slug, event_id=None, next=None,
    template_name='schedule/create_event.html', form_class = EventForm):
    """
    This function, if it receives a GET request or if given an invalid form in a
    POST request it will generate the following response

    Template:
        schedule/create_event.html

    Context Variables:

    form:
        an instance of EventForm

    calendar:
        a Calendar with id=calendar_id

    if this function gets a GET request with ``year``, ``month``, ``day``,
    ``hour``, ``minute``, and ``second`` it will auto fill the form, with
    the date specifed in the GET being the start and 30 minutes from that
    being the end.

    If this form receives an event_id it will edit the event with that id, if it
    recieves a calendar_id and it is creating a new event it will add that event
    to the calendar with the id calendar_id

    If it is given a valid form in a POST request it will redirect with one of
    three options, in this order

    # Try to find a 'next' GET variable
    # If the key word argument redirect is set
    # Lastly redirect to the event detail of the recently create event
    """
    date = coerce_date_dict(request.GET)
    initial_data = None
    if date:
        try:
            start = datetime.datetime(**date)
            initial_data = {
                "start": start,
                "end": start + datetime.timedelta(minutes=30)
            }
        except TypeError:
            raise Http404
        except ValueError:
            raise Http404

    instance = None
    if event_id is not None:
        instance = get_object_or_404(Event, id=event_id)

    calendar = get_object_or_404(Calendar, slug=calendar_slug)

    form = form_class(data=request.POST or None, instance=instance,
        hour24=True, initial=initial_data)

    if form.is_valid():
        event = form.save(commit=False)
        if instance is None:
            event.creator = request.user
            event.calendar = calendar
        event.save()
        next = next or reverse('event', args=[event.id])
        next = get_next_url(request, next)
        return HttpResponseRedirect(next)

    next = get_next_url(request, next)
    return render_to_response(template_name, {
        "form": form,
        "calendar": calendar,
        "next":next
    }, context_instance=RequestContext(request))


class DeleteEventView(DeleteView):
    template_name = 'schedule/delete_event.html'
    pk_url_kwarg = 'event_id'
    model = Event

    def get_context_data(self, **kwargs):
        ctx = super(DeleteEventView, self).get_context_data(**kwargs)
        ctx['next'] = self.get_success_url()
        return ctx

    def get_success_url(self):
        """
        After the event is deleted there are three options for redirect, tried in
        this order:

        # Try to find a 'next' GET variable
        # If the key word argument redirect is set
        # Lastly redirect to the event detail of the recently create event
        """
        next = self.kwargs.get('next') or reverse('day_calendar', args=[self.object.calendar.slug])
        next = get_next_url(self.request, next)
        return next

    ## Override dispatch to apply the permission decorator
    @method_decorator(login_required)
    @method_decorator(check_event_permissions)
    def dispatch(self, request, *args, **kwargs):
        return super(DeleteEventView, self).dispatch(request, *args, **kwargs)


def check_next_url(next):
    """
    Checks to make sure the next url is not redirecting to another page.
    Basically it is a minimal security check.
    """
    if not next or '://' in next:
        return None
    return next

def get_next_url(request, default):
    next = default
    if OCCURRENCE_CANCEL_REDIRECT:
        next = OCCURRENCE_CANCEL_REDIRECT
    if 'next' in request.REQUEST and check_next_url(request.REQUEST['next']) is not None:
        next = request.REQUEST['next']
    return next
