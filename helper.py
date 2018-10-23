from functools import wraps
import time

def multiple_trials(wait_seconds=[0, 60, 120]):
    def _multiple_trials(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            for idx, wait_second in enumerate(wait_seconds):
                time.sleep(wait_second)
                try:
                    print('multiple_trials %s: %s, %s, %s' % (idx + 1, func.__name__, args, kwargs))
                    print('wait %s seconds' % wait_second)
                    return func(*args, **kwargs)
                except Exception as e:
                    print('ERROR: %s\n' % e)
        return wrapper
    return _multiple_trials

