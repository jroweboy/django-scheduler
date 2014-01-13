

//*----
// Function to handle the day clicked event on the calendar. 
// This should only show up if the user is either logged in and has permission or 
// the calendar is set to allow anonymous adding of events to the calendar.
// This also only have effect if the date clicked on is in the future.

function dayClicked(date, overnight, jsEvent, view) {
    {% comment %}
	if(date.getHours() < 8) {
		date.setHours(08);
		date.setMinutes(00);
	}
    {% endcomment %}

    if (view.name == "agendaDay" || view.name == "agendaWeek") {
        {% if perms.calendar.edit_calendar %}
        {# $('input#id_user').val(username); #}
        if(overnight) {
            if(date >= (new Date().getTime() - (24*60*60*1000))) {
            	// schedule an overnight event
                $('div#newRequest').dialog({
                    autoOpen : false,
                    width : 'auto',
                    background : 'blue'
                });

                // we need to close the request box if one is already open
                $('div#newRequest').dialog('close');
                $('div#newRequest').dialog('open');
                
                date.setHours(22);
                date.setMinutes(00);
                $('#id_start_time').datetimepicker('setDate', date);

				var startMonth = date.getMonth() + 1;
				var startDay  = date.getDate();
				var startYear = date.getFullYear();

                originalStart = "";
                if(startMonth < 10) {
                    originalStart += "0";
                }
                originalStart += startMonth + "/";
                if(startDay < 10) {
                    originalStart += "0";
                }
                originalStart += startDay + "/" + startYear + " 10:00 pm";
                
                date.setDate(date.getDate() + 1);
                date.setHours(8);
                $('#id_end_time').datetimepicker('setDate', date);

                var endMonth = date.getMonth() + 1;
                var endDay = date.getDate();
                var endYear = date.getFullYear();

                originalEnd = "";
                if(endMonth < 10) {
                    originalEnd += "0";
                }
                originalEnd+= endMonth + "/";
                if(endDay < 10) {
                    originalEnd += "0";
                }
                originalEnd += endDay + "/" + endYear + " 08:00 am";
                
                // disable start/end editing capabilities
                $('input#id_overnight').prop('checked', true);
                $('input#id_overnight').prop('disabled', true);
                $('input#id_start_time').prop('disabled', true);
                $('input#id_end_time').prop('disabled', true);
            }
        } else { // this is not an overnight event    
            // this disables user from being able to request things in the past.
            if (date >= new Date()) {
                $('div#newRequest').dialog({
                    autoOpen : false,
                    width : 'auto'
                });
                
                // we need to close the request box if one is already open
                $('div#newRequest').dialog('close');
                $('div#newRequest').dialog('open');
                //switch the dates to the current clicked time/date. works like a charm
                $('#id_start_0').datetimepicker('setDate', date);
                if(date.getHours() >= 8 && date.getHours() < 21) {
                    date.setMinutes(date.getMinutes() + 30);
                } else {
                    if(date.getMinutes() < 30) {
                        date.setMinutes(date.getMinutes() + 30);
                    } else {
                        date.setHours(22);
                        date.setMinutes(00);
                    }
                }
                $('#id_end_0').datetimepicker('setDate', date);
                $('#id_end_0').focus();
            }
        }
        {% endif %}
    } else {
        $('#calendar').fullCalendar('changeView', 'agendaDay');
        $('#calendar').fullCalendar('gotoDate', date);
    }
}


function enableTimeEditing() {
    $('input#id_start').prop('disabled', false);
    $('input#id_end').prop('disabled', false);
    {# $('input#id_overnight').prop('disabled', false); #}
}

function newEventFormValInit(){

    $('form#newRequestForm').validator({
        effect : 'wall',
        container : '#errors'
    }).submit(function(e) {
        enableTimeEditing();

        /***This converts from AM/PM to 24Hr time *****/
        var stop_times = $('input#id_end_time').val().split(" ");

        var monthDayYear = stop_times[0].split("/");
        var month = parseInt(monthDayYear[0]);
        var day = monthDayYear[1];
        var year = monthDayYear[2];
        var hour;
        var minutes;

        var new_stop = "" + stop_times[0] + " ";
        //alert(stop_times[2]);
        if (stop_times[2] == 'pm') {
            hours = stop_times[1].split(":");
            if (hours[0] != '12') {
                new_hour = parseInt(hours[0]) + 12;
            } else {
                new_hour = 12;
            }
            new_stop += "" + new_hour + ":" + hours[1];
            hour = new_hour;
            minutes = hours[1];
        } else {
            new_stop += "" + stop_times[1];
            hour = stop_times[1].split(":")[0];
            minutes = stop_times[1].split(":")[1];
        }
        $('input#id_end_time').val(new_stop);
        var stopDate = new Date(year, (month-1), day, hour, minutes);

        var start_times = $('input#id_start_time').val().split(" ");
        
        monthDayYear = start_times[0].split("/");
        month = parseInt(monthDayYear[0]);
        day = monthDayYear[1];
        year = monthDayYear[2];

        var new_start = "" + start_times[0] + " ";
        //alert(stop_times[2]);
        if (start_times[2] == 'pm') {
            hours = start_times[1].split(":");
            if (hours[0] != '12') {
                new_hour = parseInt(hours[0]) + 12;
            } else {
                new_hour = 12;
            }
            new_start += "" + new_hour + ":" + hours[1];
            hour = new_hour;
            minutes = hours[1];
        } else {
            new_start += "" + start_times[1];
            hour = start_times[1].split(":")[0];
            minutes = start_times[1].split(":")[1];
        }
        $('input#id_start_time').val(new_start);
        var startDate = new Date(year, (month-1), day, hour, minutes);
        /*******End time conversion *********/

        /*        
        If any of the events fail due to a scheduling conflict,
        then I need to ask the user to do one of two things: 
        (1) abort request and revert or
        (2) schedule everything that doesn't conflict with other 
        events.
        */

        var sendRequest = true;

        var dayDelta = (stopDate - startDate)/(1000*60*60*24)
        if(dayDelta <= 0) {
            alert("The start time must be before the end time.");
            sendRequest = false;
            // TODO find a way to prevent refreshing, and closing of the request form
        }

        if(sendRequest) {

            var endHour = stopDate.getHours();
            var endMinutes = stopDate.getMinutes();
            var startHour = startDate.getHours();
            
            var sameDayStartAndEnd = stopDate.getDate() - startDate.getDate() == 0;
            if(sameDayStartAndEnd && startHour < 22) {
                if(endHour == 22 && endMinutes != 0) { // endHour before midnight, but on the same day
                    // TODO ask user what they want to do out of the following 
                    // five options:
                    //
                    // 1) Attempt to request both events, split into two
                        // splitting event into two event requests:
                        // (1) from start to 10pm on same day,
                        // (2) from 10pm on same day to 8am on next day
                    // 2) attempt to request only until 10pm
                    // 3) attempt to request only an overnight event
                    // 4) go back to edit the times
                    // 5) cancel, (return;)
                }
            } else if(sameDayStartAndEnd && startHour == 22) {
                var y = confirm("Events that start at or after 10pm must be overnight events.\nWould you like to create an overnight event now?");
                if(y) {
                    // create an overnight event
                    new_start = new_start.split(" ")[0] + " 22:00";
                    $('input#id_start_time').val(new_start);
                    
                    stopDate = new Date(startDate.getTime() + (24*60*60*1000));

                    var month = "";
                    if(stopDate.getMonth() < 10) {
                        month = "0";
                    }
                    month += (stopDate.getMonth()+1);

                    var day = "";
                    if(stopDate.getDate() < 10) {
                        day = "0";
                    }
                    day += stopDate.getDate();
                    
                    new_stop = month + "/" + day + "/" + stopDate.getFullYear() + " 08:00";
                    $('input#id_end_time').val(new_stop);
                    $('input#id_overnight').prop('checked', true);            
                } else {
                    return;
                }
            } 

            var form = $(this);
            //csrf = $("input[name=csrfmiddlewaretoken]")
            //$(csrf).appendTo('form#newRequestForm')
            if (!e.isDefaultPrevented()) {
                $.post(add_partitioned_event_url, form.serialize(), function(json) {
                    if (!json.error) {
                        $('#errors p').remove();
                        $('#errors').css('border', 'none');
                        $('#newRequestForm input[type=text]').val('');
                        $('#newRequestForm input[type=checkbox]').attr('checked', false);
                        $('div#newRequest').dialog('close');
                        $('#calendar').fullCalendar('refetchEvents');
                        $('#messages').html('<span class="success" >' + json.message + '</span>');
                        $('input#id_overnight').prop('checked', false);
                        $('.requestFormRepeating').hide();
                        displayMessages();
                    } else {
                        form.data("validator").invalidate(json);
                       $('#errors').html(json.message);
                       setTimeout(function(){document.getElementById('errors').style.display = 'none'},6000);
                       // $('#messages').html('<span class="error" >' + json.message + '</span>');
                       // displayMessages();
                    }
                }, 'json');
                e.preventDefault();
            }
        }
    });
}


$(function (){
    $("#makeRequestForm").submit(function(event) {
        $.post( create_url,
                $("#makeRequestForm").serialize()
        ).done(function (data) {
            $('div#newRequest').dialog('close');
        }).fail(function(data) {
            //alert("Error!");
            $.each(data.responseJSON, function(label, errors) {
                var parent = $("#id_"+label).parent()
                var list = "<ul>";
                var i;
                for (i=0; i<errors.length; ++i) {
                    list += "<li>"+errors[i]+"</li>";
                }
                parent.prepend(list + "</ul>");
            });
            // $("#makeRequestForm").html(data.responseText);
        });
        event.preventDefault();
    });
});


// *---
// Django CSRF protection for AJAX requests
// see: https://docs.djangoproject.com/en/dev/ref/contrib/csrf/#ajax

function getCookie(name) {
    var cookieValue = null;
    if (document.cookie && document.cookie != '') {
        var cookies = document.cookie.split(';');
        for (var i = 0; i < cookies.length; i++) {
            var cookie = jQuery.trim(cookies[i]);
            // Does this cookie string begin with the name we want?
            if (cookie.substring(0, name.length + 1) == (name + '=')) {
                cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                break;
            }
        }
    }
    return cookieValue;
}
var csrftoken = getCookie('csrftoken');

function csrfSafeMethod(method) {
    // these HTTP methods do not require CSRF protection
    return (/^(GET|HEAD|OPTIONS|TRACE)$/.test(method));
}
function sameOrigin(url) {
    // test that a given url is a same-origin URL
    // url could be relative or scheme relative or absolute
    var host = document.location.host; // host + port
    var protocol = document.location.protocol;
    var sr_origin = '//' + host;
    var origin = protocol + sr_origin;
    // Allow absolute or scheme relative URLs to same origin
    return (url == origin || url.slice(0, origin.length + 1) == origin + '/') ||
        (url == sr_origin || url.slice(0, sr_origin.length + 1) == sr_origin + '/') ||
        // or any other URL that isn't scheme relative or absolute i.e relative.
        !(/^(\/\/|http:|https:).*/.test(url));
}
$.ajaxSetup({
    beforeSend: function(xhr, settings) {
        if (!csrfSafeMethod(settings.type) && sameOrigin(settings.url)) {
            // Send the token to same-origin, relative URLs only.
            // Send the token only if the method warrants CSRF protection
            // Using the CSRFToken value acquired earlier
            xhr.setRequestHeader("X-CSRFToken", csrftoken);
        }
    }
});