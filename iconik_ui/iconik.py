import os
import urllib.parse
from werkzeug.wrappers import Request, Response
from werkzeug.routing import Map, Rule
from werkzeug.exceptions import HTTPException, NotFound
from werkzeug.wsgi import SharedDataMiddleware
from werkzeug.utils import redirect

from jinja2 import Environment, FileSystemLoader


def get_hostname(url):
    return urllib.parse.urlparse(url).netloc


class IconikApp(object):

    def __init__(self):
        template_path = os.path.join(os.path.dirname(__file__), 'templates')
        self.jinja_env = Environment(loader=FileSystemLoader(template_path), autoescape=True)
        self.jinja_env.filters['hostname'] = get_hostname

        self.url_map = Map([
            Rule('/', endpoint='index'),
        ])

    def on_index(self, request):
        error, url = None, ''
        return self.render_template('index.html', error=error, url=url)

    def error_404(self):
        response = self.render_template('404.html')
        response.status_code = 404
        return response

    def render_template(self, template_name, **context):
        template = self.jinja_env.get_template(template_name)
        return Response(template.render(context), mimetype='text/html')

    def dispatch_request(self, request):
        adapter = self.url_map.bind_to_environ(request.environ)
        try:
            endpoint, values = adapter.match()
            return getattr(self, 'on_' + endpoint)(request, **values)
        except NotFound:
            return self.error_404()
        except HTTPException as e:
            return e

    def wsgi_app(self, environ, start_response):
        request = Request(environ)
        response = self.dispatch_request(request)
        return response(environ, start_response)

    def __call__(self, environ, start_response):
        return self.wsgi_app(environ, start_response)


if __name__ == '__main__':
    from werkzeug.serving import run_simple

    app = IconikApp()
    app.wsgi_app = SharedDataMiddleware(app.wsgi_app, {
        '/static': os.path.join(os.path.dirname(__file__), 'static')
    })
    run_simple('127.0.0.1', 8000, app, use_debugger=True, use_reloader=True)
