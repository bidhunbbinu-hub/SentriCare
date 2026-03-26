import mediapipe as mp
import pkgutil
import sys
print('mediapipe file:', getattr(mp, '__file__', None))
print('has attribute solutions:', hasattr(mp, 'solutions'))
try:
    print('mp.__path__:', list(mp.__path__))
    print('submodules under mediapipe:')
    for m in pkgutil.iter_modules(mp.__path__):
        print(' -', m.name)
except Exception as e:
    print('error listing path:', e)

# try to import common candidate modules
candidates = [
    'mediapipe.solutions.face_detection',
    'mediapipe.python.solutions.face_detection',
    'mediapipe.face_detection',
]
for mod in candidates:
    try:
        __import__(mod)
        print('import OK:', mod)
    except Exception as e:
        print('import FAIL:', mod, '->', type(e).__name__, e)
print('sys.path sample:', sys.path[:5])
