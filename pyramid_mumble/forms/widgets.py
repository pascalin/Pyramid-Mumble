from pyramid.request import Request
from deform.widget import Widget
from colander import null
import html
from .. import security

class CaptchaWidget(Widget):
    def serialize(self, field, cstruct=None, readonly=False):
        if cstruct is null:
            cstruct = ""
        quoted = html.escape(cstruct, quote='"')
        return '<img src="/captcha/{}.png"><br>' \
               '<input type="text" name="{}" value="{}" autocomplete="off">'.format(security.random_string(20), field.name, quoted)

    def deserialize(self, field, pstruct):
        if pstruct is null:
            return null
        return pstruct

    def handle_error(self, field, error):
        if field.error is None:
            field.error = error
        for e in error.children:
            for num, subfield in enumerate(field.children):
                if e.pos == num:
                    subfield.widget.handle_error(subfield, e)
