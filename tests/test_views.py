from pyramid_mumble import models
from pyramid_mumble.views.default import main_view
from pyramid_mumble.views.notfound import notfound_view


def test_my_view_failure(app_request):
    info = main_view(app_request)
    assert info.status_int == 500

def test_my_view_success(app_request, dbsession):
    model = models.MumbleUser(username="Lewontin_Dick", realname="Dick Lewontin", affiliation="Harvard University", email="dick@harvard.edu", language="English", publickey="", online=False)
    dbsession.add(model)
    dbsession.flush()

    info = main_view(app_request)
    assert app_request.response.status_int == 200
    assert len(info['users']) == 1
    assert info['project'] == 'Pyramid Mumble'

def test_notfound_view(app_request):
    info = notfound_view(app_request)
    assert app_request.response.status_int == 404
    assert info == {}
