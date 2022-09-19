import colander
import deform.widget

user_roles = ['speaker', 'audience']
role_choices = [(role, role.capitalize()) for role in user_roles]


class UserRoleSchema(colander.MappingSchema):
    uid = colander.SchemaNode(colander.Int(), validator=colander.Range(1, 9999), widget=deform.widget.HiddenWidget())
    name = colander.SchemaNode(colander.String())
    role = colander.SchemaNode(colander.String(), validator=colander.OneOf(choices=user_roles), widget=deform.widget.SelectWidget(values=role_choices))
    is_staff = colander.SchemaNode(colander.Boolean())
    update = colander.SchemaNode(colander.Boolean())


class UserAdminSchema(colander.SequenceSchema):
    users = UserRoleSchema()

class AdminRolesSchema(colander.MappingSchema):
    roles = UserAdminSchema()


@colander.deferred
def default_track_deferred(node, kw):
    track = kw.get('default_track')
    if track:
        return track.id


@colander.deferred
def tracks_deferred_widget(node, kw):
    tracks = kw.get('tracks')
    if tracks:
        values = [('', '---')] + [(t.id, t.title) for t in tracks]
        return deform.widget.SelectWidget(values=values)
    else:
        return deform.widget.SelectWidget()


class ActivitySchema(colander.MappingSchema):
    id = colander.SchemaNode(colander.Int(), validator=colander.Range(1, 99999), widget=deform.widget.HiddenWidget(), missing="")
    title = colander.SchemaNode(colander.String(),)
    description = colander.SchemaNode(colander.String(), widget=deform.widget.TextAreaWidget(), missing="")


class SessionActivitiesSchema(colander.SequenceSchema):
    activities = ActivitySchema()


class SessionSchema(colander.MappingSchema):
    id = colander.SchemaNode(colander.Int(), validator=colander.Range(1, 99999), widget=deform.widget.HiddenWidget())
    title = colander.SchemaNode(colander.String(), missing="")
    description = colander.SchemaNode(colander.String(), widget=deform.widget.TextAreaWidget(), missing="")
    start_time = colander.SchemaNode(colander.DateTime())
    end_time = colander.SchemaNode(colander.DateTime())
    track = colander.SchemaNode(colander.String(), widget=tracks_deferred_widget, default=default_track_deferred)
    activities = SessionActivitiesSchema()


# class PerformerSchema(colander.MappingSchema):
#     id = colander.SchemaNode(colander.Int(), validator=colander.Range(1, 9999), missing="")
#
#
# class ActivityPerformersSchema(colander.SequenceSchema):
#     activities = ActivitySchema()
#
#
@colander.deferred
def sessions_deferred_widget(node, kw):
    sessions = kw.get("sessions")
    choices = []
    if sessions:
        choices = [('', '---')] + [(session.id, "{} on {}".format(session, session.start_time)) for session in sessions]
    return deform.widget.SelectWidget(values=choices)

@colander.deferred
def performers_deferred_widget(node, kw):
    performers = kw.get("performers")
    choices = []
    if performers:
        choices = [(performer.id, performer.realname) for performer in performers]
    return deform.widget.SelectWidget(values=choices, multiple=True)



class ActivitySchema(colander.MappingSchema):
    id = colander.SchemaNode(colander.Int(), validator=colander.Range(1, 999999), widget=deform.widget.HiddenWidget())
    title = colander.SchemaNode(colander.String())
    description = colander.SchemaNode(colander.String(), widget=deform.widget.TextAreaWidget(), missing="")
    session = colander.SchemaNode(colander.String(), widget=sessions_deferred_widget)
    performers = colander.SchemaNode(colander.Set(), widget=performers_deferred_widget)
    # flavors = colander.SchemaNode(colander.Set(), widget=deform.widget.SelectWidget(values=[('sweet', 'Sweet'), ('salty', 'Salty')], multiple=True))
