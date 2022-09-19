from pyramid.view import notfound_view_config
from .. import models


@notfound_view_config(renderer='pyramid_mumble:templates/404.jinja2', append_slash=True)
def notfound_view(request):
    meeting = request.dbsession.query(models.Meeting).first()
    if meeting:
        project = meeting.title
    else:
        project = "A Pyramid Mumble Site"

    request.response.status = 404
    return {'project': project}
