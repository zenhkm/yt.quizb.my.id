import sys
import os

sys.path.insert(0, os.path.dirname(__file__))

try:
    from app import app as application
except Exception as e:
    # Script ini akan menampilkan error asli ke layar browser
    import traceback
    error_trace = traceback.format_exc()
    def application(environ, start_response):
        start_response('500 Internal Server Error', [('Content-Type', 'text/plain')])
        return [f"ERROR STARTUP APLIKASI:\n\n{error_trace}".encode()]