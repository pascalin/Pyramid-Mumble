import colander
import deform.widget
import pytz

user_roles = ['speaker', 'audience']
role_choices = [(role, role.capitalize()) for role in user_roles]
timezones = [('', '')] + [(tz, tz) for tz in pytz.common_timezones]

@colander.deferred
def deferred_tz_default(node, kw):
    return kw['timezone_default']


class TrackSchema(colander.MappingSchema):
    id = colander.SchemaNode(colander.Int(), validator=colander.Range(1, 9999), widget=deform.widget.HiddenWidget())
    title = colander.SchemaNode(colander.String())
    description = colander.SchemaNode(colander.String(), missing="", widget=deform.widget.TextAreaWidget())


class TrackListSchema(colander.SequenceSchema):
    tracks = TrackSchema()


class MeetingSchema(colander.MappingSchema):
    id = colander.SchemaNode(colander.Int(), validator=colander.Range(1, 9999), widget=deform.widget.HiddenWidget())
    title = colander.SchemaNode(colander.String())
    description = colander.SchemaNode(colander.String(), missing="", widget=deform.widget.TextAreaWidget())
    website = colander.SchemaNode(colander.String(), missing="")
    start_time = colander.SchemaNode(colander.DateTime())
    end_time = colander.SchemaNode(colander.DateTime())
    timezone = colander.SchemaNode(colander.String(), validator=colander.OneOf(pytz.common_timezones), widget=deform.widget.SelectWidget(values=timezones), default=deferred_tz_default, required=False, missing="")
    tracks = TrackListSchema()


class IssueSchema(colander.MappingSchema):
    activity_id = colander.SchemaNode(colander.Int(), validator=colander.Range(1, 99999), widget=deform.widget.HiddenWidget(), missing="")
    can_publish = colander.SchemaNode(colander.Boolean(), title="Can be published?")
    can_translate = colander.SchemaNode(colander.Boolean(), title="Can be translated?")
    alt_title = colander.SchemaNode(colander.String(), missing="", title="Alternative title")
    alt_description = colander.SchemaNode(colander.String(), widget=deform.widget.TextAreaWidget(), missing="", title="Alternative abstract")