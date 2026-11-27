from __future__ import annotations

import importlib
import importlib.util
from pathlib import Path

_SUBSTITUTIONS = (
    (
        "from signify.authenticode import SignedPEFile",
        "from signify.authenticode.signed_file import SignedPEFile",
    ),
    (
        "signed_pe.iter_signed_datas()",
        "signed_pe.iter_embedded_signatures()",
    ),
    (
        "certs = signed_data.certificates",
        "certs = list(signed_data.certificates)",
    ),
)


def patch_features_source(source: str) -> str:
    """Apply a small, reviewed Signify 0.9.x compatibility patch to thrember."""
    for old, new in _SUBSTITUTIONS:
        old_count = source.count(old)
        new_count = source.count(new)
        if old_count == 1 and new_count == 0:
            source = source.replace(old, new, 1)
        elif old_count == 0 and new_count == 1:
            # Idempotent if the patch command is rerun in the same environment.
            continue
        else:
            raise RuntimeError(
                "Unexpected thrember/features.py layout: "
                f"expected one old or one patched anchor; old={old_count}, new={new_count}"
            )
    return source


def patch_installed_thrember() -> Path:
    spec = importlib.util.find_spec("thrember")
    if spec is None or not spec.submodule_search_locations:
        raise RuntimeError("Pinned EMBER2024 'thrember' package is not installed.")

    package_dir = Path(next(iter(spec.submodule_search_locations))).resolve(strict=True)
    if package_dir.name != "thrember":
        raise RuntimeError("Refusing to patch an unexpected package directory.")

    features_path = package_dir / "features.py"
    if features_path.is_symlink() or not features_path.is_file():
        raise RuntimeError("Expected a regular thrember/features.py file.")

    original = features_path.read_text(encoding="utf-8")
    patched = patch_features_source(original)
    compile(patched, str(features_path), "exec")
    if patched != original:
        features_path.write_text(patched, encoding="utf-8")

    importlib.invalidate_caches()
    features = importlib.import_module("thrember.features")
    importlib.reload(features)

    from signify.authenticode.signed_file import SignedPEFile

    if not callable(SignedPEFile) or not callable(
        getattr(SignedPEFile, "iter_embedded_signatures", None)
    ):
        raise RuntimeError("Installed Signify does not expose the required Authenticode API.")

    print("EMBER_SIGNIFY_COMPAT_PASS")
    return features_path


if __name__ == "__main__":
    patch_installed_thrember()
