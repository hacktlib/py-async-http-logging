from http import HTTPStatus
from http.server import HTTPServer, BaseHTTPRequestHandler
import io
import json
import logging
import shutil
import sys
import urllib


logging.basicConfig(level=logging.DEBUG)


SERVE_ON_PORT = 8765


response_cache = []


class LocalHostHandler(BaseHTTPRequestHandler):

    def __init__(self, *args, **kwargs):
        self.do_POST = self.do_GET
        self._headers = None

        super().__init__(*args, **kwargs)

    def do_GET(self):
        try:
            if 'get_all_responses' in self.path:
                print('Returning all cached responses')
                response = self.get_all_responses()

            elif 'clear_response_cache' in self.path:
                print('Clearing cached responses')
                response = self.clear_response_cache()

            elif 'last_response' in self.path:
                print('Returning last cached response')
                response = self.get_last_response()

            else:
                print('Returning request mirror')
                response = self.request_mirror()

        except Exception as exc:
            response = json.dumps({
                'error': {
                    'name': type(exc).__name__,
                    'msg': f'{str(exc)}',
                },
            })

        content_type = f'application/json; charset={self.encoding}'
        encoded = f'{response}\n'.encode(self.encoding, 'surrogateescape')

        f = io.BytesIO()
        f.write(encoded)
        f.seek(0)

        self.send_response(code=HTTPStatus.OK)
        self.send_header('Content-type', content_type)
        self.send_header("Content-Length", str(len(encoded)))
        self.end_headers()

        try:
            self.copyfile(f, self.wfile)
        finally:
            f.close()

    def request_mirror(self):
        global response_cache

        headers = {k: v for k, v in self.headers.items()}
        host, port = headers['Host'].split(':')
        del headers['Host']

        response = {
            'request': {
                'http': {
                    'method': self.command,
                    'version': self.protocol_version,
                    'secure': 'HTTPS' in self.protocol_version,
                },
                'url': {
                    'host': host,
                    'port': int(port),
                    'path': self.path,
                    'query_strings': self.query_strings,
                },
                'headers': headers,
                'body': self.body,
            },
            'client': {
                'ip': self.client_address[0],
                'port': self.client_address[1],
            }
        }

        response_cache.append(response)

        return json.dumps(response)

    def clear_response_cache(self):
        global response_cache

        response_cache = []

        return json.dumps({'clear_response_cache': True})

    def get_all_responses(self):
        global response_cache

        return json.dumps(response_cache)

    def get_last_response(self):
        global response_cache

        try:
            return json.dumps({'last_response': response_cache[-1]})
        except IndexError:
            return json.dumps({'last_response': None})

    @property
    def body(self):
        body_length = int(self.headers['Content-Length'])
        content = self.rfile.read(body_length)

        body = content.decode(self.encoding)

        try:
            body = json.loads(body)
        except json.JSONDecodeError:
            pass

        return body

    @property
    def query_strings(self):
        return {
            k: v[0] if len(v) == 1 else v
            for k, v in urllib.parse.parse_qs(self.path.split('?')[-1]).items()
        }

    @property
    def encoding(self):
        return sys.getfilesystemencoding()

    def copyfile(self, source, outputfile):
        shutil.copyfileobj(source, outputfile)


def run(
    server_class: HTTPServer = HTTPServer,
    handler_class: BaseHTTPRequestHandler = LocalHostHandler,
    port: int = SERVE_ON_PORT,
) -> None:
    print(f'Serving on port {port}...')
    server_address = ('', port)
    httpd = server_class(server_address, handler_class)
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print('\nTerminating server...')
        pass
    finally:
        httpd.server_close()


if __name__ == '__main__':
    from sys import argv

    if len(argv) == 2:
        run(port=int(argv[1]))
    else:
        run()
