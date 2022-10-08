from deform import Form, ValidationFailure, Button
from pyramid.httpexceptions import HTTPSeeOther
from pyramid.view import (
    view_config,
)

from .. import models
from ..forms import admin


@view_config(route_name='admin_roles', renderer='pyramid_mumble:templates/admin_roles.jinja2', permission='admin')
def roles_view(request):
    meeting = request.dbsession.query(models.Meeting).first()
    if meeting:
        project = meeting.title
        website = meeting.website
    else:
        project = "A Pyramid Mumble Site"
        website = ''

    profiles = request.dbsession.query(models.MumbleUser).all()
    roles = []
    for profile in profiles:
        roles.append({
            'uid': profile.id,
            'name': profile.realname,
            'role': profile.is_speaker and 'speaker' or 'audience',
            'is_staff': profile.is_staff,
        })
    appstruct = {'roles': roles,}

    form = Form(admin.AdminRolesSchema(), buttons=[Button('submit',)])

    if 'submit' in request.POST:
        useradmin_schema = admin.AdminRolesSchema().bind()
        form = Form(useradmin_schema, buttons=[Button('submit',)])
        controls = request.POST.items()
        try:
            appstruct = form.validate(controls)
        except ValidationFailure as e:
            return {'useradmin_form': e.render(), 'project': project, 'website': website}
        updated_profiles = [p for p in appstruct['roles'] if p['update']]
        for update in updated_profiles:
            profile = request.dbsession.query(models.MumbleUser).filter_by(id=update['uid']).first()
            if profile:
                profile.is_staff = update['is_staff']
                if update['role'] == 'speaker':
                    profile.is_speaker = True
                else:
                    profile.is_speaker = False

            return HTTPSeeOther(request.route_path("profile_list"))

    return {'useradmin_form': form.render(appstruct=appstruct), 'profile_list': profiles, 'project': project, 'website': website}
