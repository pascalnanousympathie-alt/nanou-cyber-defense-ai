import runpy
from pathlib import Path

import pytest


PATCH_SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "patch_thrember_signify_compat.py"
patch_features_source = runpy.run_path(str(PATCH_SCRIPT))["patch_features_source"]


def test_thrember_signify_patch_updates_all_known_api_changes():
    upstream = "\n".join(
        [
            "from signify.authenticode import SignedPEFile",
            "for signed_data in signed_pe.iter_signed_datas():",
            "certs = signed_data.certificates",
            "for cert in certs[:-1]:",
        ]
    )

    patched = patch_features_source(upstream)

    assert "from signify.authenticode.signed_file import SignedPEFile" in patched
    assert "signed_pe.iter_embedded_signatures()" in patched
    assert "certs = list(signed_data.certificates)" in patched
    assert "iter_signed_datas()" not in patched
    assert patch_features_source(patched) == patched


def test_thrember_signify_patch_fails_closed_on_unknown_upstream_source():
    with pytest.raises(RuntimeError, match="Unexpected thrember/features.py layout"):
        patch_features_source("from signify.authenticode import UnexpectedClass")
