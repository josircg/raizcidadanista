# BruteBuster by Cyber Security Consulting (www.csc.bg)

"""
Brutebuster needs access to the REMOTE_IP of the incoming request. We're doing
this by adding the request object to the thread_local space
"""
from django.http import Http404
from django.core.exceptions import PermissionDenied

from BruteBuster.models import FailedURLAttempt

try:
    from threading import local
except ImportError:
    from django.utils.threading_local import local
_thread_locals = local()


def get_request():
    return getattr(_thread_locals, 'request', None)


class RequestMiddleware(object):
    """Provides access to the request object via thread locals"""
    def process_request(self, request):
        _thread_locals.request = request


class Response404Middleware(object):
    def process_exception(self, request, exception):
        if isinstance(exception, Http404):
            IP_ADDR = request.META.get('HTTP_X_FORWARDED_FOR', request.META.get('REMOTE_ADDR', None))
            try:
                fa = FailedURLAttempt.objects.filter(IP=IP_ADDR).latest('timestamp')
                fa.failures += 1
                fa.save()
                if fa.recent_failure():
                    if fa.too_many_failures():
                        # we block the authentication attempt because
                        # of too many recent failures
                        raise PermissionDenied()
                else:
                    # the block interval is over, so let's start
                    # with a clean sheet
                    fa.failures = 1
                    fa.save()
            except FailedURLAttempt.DoesNotExist:
                # the authentication was kaput, we should record this
                FailedURLAttempt(IP=IP_ADDR, failures=1).save()