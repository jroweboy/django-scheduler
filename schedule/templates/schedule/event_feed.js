[   {% for event in events %}
  {
    "title": "{{event.title}}",
    "start": "{{event.start}}",
    "end": "{{event.end}}",
    "description": "{{event.description}}"
    {% comment %},
    "allDay": {{event.allDay|lower}},
    "id":     "{{event.id}}",
    "user":   "{{event.user}}",
    "instrument": "{{event.instrument}}",
    "className": "owner",
    "disableDragging": false, 
    "disableResizing": false,
 {%if user.is_superuser or perms.instrument.add_room%}
    "editable":true,{%else%}
    "editable":false,{%endif%}
    "repeating": {%if not request.repeating == Null %}"yes"{%else%}"no"{%endif%},
{%else%}
    "editable":false,
{%endif%}
    "title":  "{{event.title}}",
    "purpose": "{{event.purpose}}",
    "etag": "{{event.etag}}",
    "color":  "{{event.color}}" 
    {% endcomment %}

  }{% if forloop.last %}{%else%},{%endif%}
{%endfor%}
]


{# "email":  "{{event.email}}", #}
{# "phone":  "{{event.contact_phone}}", #}
