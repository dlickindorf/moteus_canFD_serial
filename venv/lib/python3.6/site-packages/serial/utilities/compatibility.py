from __future__ import nested_scopes, generators, division, absolute_import, with_statement, \
   print_function, unicode_literals
import inspect

BACKWARDS_COMPATIBILITY_IMPORTS = '\n'.join(
    (
        '# region Backwards Compatibility',
        'from __future__ import nested_scopes, generators, division, absolute_import, with_statement, \\',
        '   print_function, unicode_literals',
        'from future import standard_library',
        'standard_library.install_aliases()',
        'from future.builtins import *',
        '# endregion'
    )
)


def backport():
    # type: (...) -> None

    frame_info = inspect.stack()[1]  # type: inspect.FrameInfo

    try:
        frame = frame_info.frame
    except AttributeError:
        frame = frame_info[0]

    exec(BACKWARDS_COMPATIBILITY_IMPORTS, frame.f_globals, frame.f_locals)

