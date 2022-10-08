import logging
import os.path

import colander
import deform.widget
from deform.interfaces import FileUploadTempStore
from .widgets import CaptchaWidget

import pycountry, pytz, tempfile

countries = [('', '')] + [(c.alpha_2, c.name) for c in pycountry.countries]
country_codes = [c[0] for c in countries]
timezones = [('', '')] + [(tz, tz) for tz in pytz.common_timezones]


class CertStorage(FileUploadTempStore):
    def __init__(self):
        self.path = tempfile.mkdtemp()

    def get(self, name, default=None):
        fname = os.path.join(self.path, name)
        if os.path.isfile(fname):
            return open(fname)
        else:
            return default

    def __getitem__(self, name):
        fname = os.path.join(self.path, name)
        return open(fname)

    def __setitem__(self, name, value):
        fname = os.path.join(self.path, name)
        with open(fname, 'wb') as fdest:
            fdest.write(value['fp'].read())

    def __contains__(self, item):
        fname = os.path.join(self.path, item)
        return os.path.isfile(fname)


class Store(dict):
    def preview_url(self, name):
        return ""

tmpstore = Store()
#tmpstore = CertStorage()


@colander.deferred
def deferred_captcha_validator(node, kw):
    captcha = kw.get("captcha")
    choices= []
    value = captcha._request.session.get(captcha._session_key, None)
    if value:
        del captcha._request.session[captcha._session_key]
        choices.append(value)
        return colander.OneOf(choices, msg_err="Wrong captcha code. Are you a robot?")
    else:
        return colander.Function(lambda v: False)


@colander.deferred
def deferred_email_validator(node, kw):
    model_query = kw.get("query")

    def not_registered(address):
        return model_query.filter_by(email=address).count() == 0

    return colander.All(colander.Email(), colander.Function(not_registered, msg="This address is already registered"))


@colander.deferred
def deferred_username_validator(node, kw):
    model_query = kw.get("query")
    alternatives = kw.get("alternatives")

    def not_registered(username):
        return model_query.filter_by(username=username).count() == 0

    return colander.All(colander.Length(max=50), colander.OneOf(alternatives, msg_err="This username is invalid"), colander.Function(not_registered, msg="This username is already taken"))


@colander.deferred
def deferred_username_default(node, kw):
    return kw['username_default']


@colander.deferred
def deferred_language_default(node, kw):
    return kw['language_default']


@colander.deferred
def deferred_tz_default(node, kw):
    return kw['timezone_default']


class MumbleUserSchema(colander.MappingSchema):
    realname = colander.SchemaNode(colander.String(), validator=colander.Regex(r"^([-\w]{1,20}[.]?)( [-\w]{1,20}[.]?){1,5}$"), title="Full Name")
    email = colander.SchemaNode(colander.String(), validator=deferred_email_validator, widget=deform.widget.CheckedInputWidget(), title="Email")
    organization = colander.SchemaNode(colander.String(), required=False, missing="Independent Scholar")
    country = colander.SchemaNode(colander.String(), validator=colander.OneOf(country_codes), widget=deform.widget.SelectWidget(values=countries))
    state = colander.SchemaNode(colander.String(), title="State/province", required=False)
    language = colander.SchemaNode(colander.String(), validator=colander.OneOf(["en", "es"]), widget=deform.widget.RadioChoiceWidget(values=(('es', "Spanish"), ('en', "English"))), title="Preferred language")
    captcha = colander.SchemaNode(colander.String(), widget=CaptchaWidget(), validator=deferred_captcha_validator)


class UserSchema(colander.MappingSchema):
    user = MumbleUserSchema()


user_schema = UserSchema()


class UserSettingsSchema(colander.MappingSchema):
    language = colander.SchemaNode(colander.String(), validator=colander.OneOf(["en", "es"]), widget=deform.widget.RadioChoiceWidget(values=(('es', "Spanish"), ('en', "English"))), title="Preferred language", default=deferred_language_default)
    password = colander.SchemaNode(colander.String(), validator=colander.Length(min=5), widget=deform.widget.CheckedPasswordWidget(), title="Password", missing="")
    timezone = colander.SchemaNode(colander.String(), validator=colander.OneOf(pytz.common_timezones), widget=deform.widget.SelectWidget(values=timezones), default=deferred_tz_default, required=False, title="Timezone you will use during the meeting", missing="")
    username = colander.SchemaNode(colander.String(), validator=deferred_username_validator, widget=deform.widget.SelectWidget(), title="User name", missing="", default=deferred_username_default)


class MumbleSettingsSchema(colander.MappingSchema):
    email = colander.SchemaNode(colander.String(), validator=colander.Email(), widget=deform.widget.HiddenWidget())
    privkey = colander.SchemaNode(deform.FileData(), widget=deform.widget.FileUploadWidget(tmpstore), required=False, title="Private key", missing="")


class EmailLoginSchema(colander.MappingSchema):
    email = colander.SchemaNode(colander.String(), validator=colander.Email(), title="Email")
    captcha = colander.SchemaNode(colander.String(), widget=CaptchaWidget(), validator=deferred_captcha_validator)


class EmailPasswordLoginSchema(colander.MappingSchema):
    email = colander.SchemaNode(colander.String(), validator=colander.Email(), title="Email")
    password = colander.SchemaNode(colander.String(), widget=deform.widget.PasswordWidget(), title="Password")
    captcha = colander.SchemaNode(colander.String(), widget=CaptchaWidget(), validator=deferred_captcha_validator)


class LoginSchema(colander.MappingSchema):
    login = EmailPasswordLoginSchema()


login_schema = LoginSchema()
email_schema = EmailLoginSchema()