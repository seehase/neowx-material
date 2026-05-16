"""
chart_methods_loader.py — WeeWX SearchList Extension
=====================================================
Pre-compiles _chart_methods.tmpl using Cheetah's Compiler API and registers
the resulting class in ``sys.modules`` so that ``#extends _chart_methods``
resolves in child page templates.

Also scans the skin directory at startup and ensures every template that
uses ``#extends _chart_methods`` also has ``#implements respond``.  Without
this directive CT3 puts the template body in ``writeBody()`` instead of
``respond()``, causing blank pages.

Does NOT use ImportHooks — the module is pre-registered before any template
is compiled, so the standard ``from _chart_methods import _chart_methods``
import in the child templates resolves instantly from sys.modules.

Register in skin.conf under [CheetahGenerator]:
    search_list_extensions = user.chart_methods_loader.ChartMethodsLoader, ...

Compatible with WeeWX 5.x (Python 3 / Cheetah3 / CT3).
"""

import glob
import os
import sys
import types
import logging

from weewx.cheetahgenerator import SearchList

log = logging.getLogger(__name__)

_CLASS_NAME = '_chart_methods'
_MODULE_NAME = '_chart_methods'

# The two directives that must appear together (in this order).
_EXTENDS_LINE    = '#extends _chart_methods'
_IMPLEMENTS_LINE = '#implements respond'


class ChartMethodsLoader(SearchList):
    """Compile _chart_methods.tmpl once and make it importable as a module."""

    # Class-level flag — only run once per WeeWX process.
    _registered = False

    def __init__(self, generator):
        super(ChartMethodsLoader, self).__init__(generator)

        if ChartMethodsLoader._registered:
            return

        skin_dir = self._find_skin_dir(generator)
        if skin_dir is None:
            log.error("chart_methods_loader: could not determine skin directory")
            return

        log.debug("chart_methods_loader: skin dir = %s", skin_dir)

        tmpl_path = os.path.join(skin_dir, '_chart_methods.tmpl')
        if not os.path.isfile(tmpl_path):
            log.error("chart_methods_loader: '%s' not found — child templates "
                      "that use #extends _chart_methods will fail to render",
                      tmpl_path)
            return

        # 1. Compile & register the base class.
        self._compile_and_register(tmpl_path)

        # 2. Ensure every child template has '#implements respond'.
        self._patch_child_templates(skin_dir)

    # ── self-healing patch ────────────────────────────────────────────────

    @staticmethod
    def _patch_child_templates(skin_dir):
        """Add '#implements respond' to any .tmpl that has '#extends _chart_methods'
        but is missing the directive.  Edits files in-place (idempotent).
        """
        for path in glob.glob(os.path.join(skin_dir, '*.html.tmpl')):
            try:
                with open(path, 'r', encoding='utf-8') as fh:
                    content = fh.read()
            except Exception as e:
                log.warning("chart_methods_loader: cannot read '%s': %s", path, e)
                continue

            if _EXTENDS_LINE not in content:
                continue  # Not a child template — skip.

            if _IMPLEMENTS_LINE in content:
                log.debug("chart_methods_loader: '%s' already has #implements respond",
                          os.path.basename(path))
                continue  # Already patched.

            # Insert '#implements respond' immediately after '#extends _chart_methods'.
            patched = content.replace(
                _EXTENDS_LINE + '\n',
                _EXTENDS_LINE + '\n' + _IMPLEMENTS_LINE + '\n',
                1,
            )
            try:
                with open(path, 'w', encoding='utf-8') as fh:
                    fh.write(patched)
                log.info(
                    "chart_methods_loader: patched '%s' — added #implements respond",
                    os.path.basename(path),
                )
            except Exception as e:
                log.error(
                    "chart_methods_loader: cannot patch '%s': %s", path, e,
                )

    # ── compilation ──────────────────────────────────────────────────────

    @classmethod
    def _compile_and_register(cls, tmpl_path):
        """Compile the base template and put it in sys.modules."""
        try:
            from Cheetah.Compiler import Compiler
        except ImportError as e:
            log.error("chart_methods_loader: cannot import Cheetah.Compiler: %s", e)
            return

        try:
            with open(tmpl_path, 'r', encoding='utf-8') as fh:
                source = fh.read()

            # Use the low-level Compiler class directly so we get Python source
            # code back — no ambiguity about what compile() returns.
            compiler = Compiler(
                source=source,
                moduleName=_MODULE_NAME,
                mainClassName=_CLASS_NAME,
            )
            py_code = compiler.getModuleCode()

        except Exception as e:
            log.error(
                "chart_methods_loader: Cheetah compilation of '%s' failed: %s",
                tmpl_path, e, exc_info=True,
            )
            return

        # exec() the generated Python into a fresh module.
        mod = types.ModuleType(_MODULE_NAME)
        mod.__file__ = tmpl_path
        try:
            exec(compile(py_code, tmpl_path, 'exec'), mod.__dict__)  # noqa: S102
        except Exception as e:
            log.error(
                "chart_methods_loader: exec of compiled '%s' failed: %s",
                tmpl_path, e, exc_info=True,
            )
            return

        # Verify the expected class is present.
        base_class = mod.__dict__.get(_CLASS_NAME)
        if base_class is None:
            # Cheetah might have used a different class name — try to find it.
            try:
                from Cheetah.Template import Template as _CheetahTemplate
                candidates = [
                    v for v in mod.__dict__.values()
                    if isinstance(v, type) and issubclass(v, _CheetahTemplate)
                    and v is not _CheetahTemplate
                ]
                if candidates:
                    base_class = candidates[0]
                    log.warning(
                        "chart_methods_loader: expected class '%s' not found; "
                        "using '%s' instead", _CLASS_NAME, base_class.__name__,
                    )
                    # Expose it under the expected name too.
                    setattr(mod, _CLASS_NAME, base_class)
            except Exception:
                pass

        if base_class is None:
            log.error(
                "chart_methods_loader: no Cheetah template class found in "
                "compiled '%s'. Available names: %s",
                tmpl_path,
                [k for k in mod.__dict__ if not k.startswith('__')],
            )
            return

        # Register in sys.modules so child templates can import it.
        sys.modules[_MODULE_NAME] = mod
        cls._registered = True
        log.info(
            "chart_methods_loader: registered '%s' (class %s) from %s",
            _MODULE_NAME, base_class.__name__, tmpl_path,
        )

    # ── skin-dir lookup ───────────────────────────────────────────────────

    @staticmethod
    def _find_skin_dir(generator):
        """Return the absolute path to the skin directory, or None."""

        # Some WeeWX builds expose skin_path directly.
        skin_path = getattr(generator, 'skin_path', None)
        if skin_path and os.path.isdir(skin_path):
            return skin_path

        try:
            cfg = generator.config_dict
            std_report = cfg.get('StdReport', {})

            skin_root = std_report.get('SKIN_ROOT', 'skins')
            if not os.path.isabs(skin_root):
                weewx_root = cfg.get('WEEWX_ROOT', '/')
                skin_root = os.path.join(weewx_root, skin_root)

            skin_name = generator.skin_dict.get('skin', 'neowx-material')
            skin_dir = os.path.join(skin_root, skin_name)

            if os.path.isdir(skin_dir):
                return skin_dir

            log.warning(
                "chart_methods_loader: computed skin dir '%s' does not exist",
                skin_dir,
            )
        except Exception as e:
            log.error("chart_methods_loader: cannot determine skin dir: %s", e)

        return None

    def get_extension_list(self, timespan, db_lookup):
        """No search-list items — we only pre-register the base class."""
        # Verify _chart_methods is still in sys.modules (sanity check).
        if _MODULE_NAME not in sys.modules:
            log.error(
                "chart_methods_loader: '%s' disappeared from sys.modules — "
                "re-registering", _MODULE_NAME,
            )
            ChartMethodsLoader._registered = False
            skin_dir = self._find_skin_dir(self.generator)
            if skin_dir:
                tmpl_path = os.path.join(skin_dir, '_chart_methods.tmpl')
                self._compile_and_register(tmpl_path)
        return []
