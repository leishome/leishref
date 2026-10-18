import subprocess
import zipfile

import pytest

from leishref.ncbi import NCBIError, fetch_fasta_gff


def fake_run(returncode=0, stderr="", zip_members=None):
    """A stand-in for subprocess.run that writes the zip `datasets` would have written."""

    def run(cmd, **kwargs):
        if zip_members is not None:
            target = cmd[cmd.index("--filename") + 1]
            with zipfile.ZipFile(target, "w") as z:
                for name, content in zip_members.items():
                    z.writestr(name, content)
        return subprocess.CompletedProcess(cmd, returncode, stdout="", stderr=stderr)

    return run


def test_a_download_returns_the_fasta_and_a_gff_named_after_it(tmp_path, monkeypatch):
    members = {"ncbi/GCA_1.1_asm_genomic.fna": ">c\nACGT\n", "ncbi/genomic.gff": "##gff-version 3\n"}
    monkeypatch.setattr(subprocess, "run", fake_run(zip_members=members))

    fasta, gff = fetch_fasta_gff("GCA_1.1", tmp_path)
    assert fasta.name == "GCA_1.1_asm_genomic.fna"
    assert gff.name == "GCA_1.1_asm_genomic.gff"
    assert fasta.read_text() == ">c\nACGT\n"


@pytest.mark.parametrize(
    "stderr",
    [
        "Error: There are no genome assemblies that match your query.\nPlease try again using different search criteria.",
        "Error: accession GCA_9.9 not found",
    ],
)
def test_an_accession_that_does_not_exist_gives_none(tmp_path, monkeypatch, stderr):
    monkeypatch.setattr(subprocess, "run", fake_run(returncode=1, stderr=stderr))
    assert fetch_fasta_gff("GCA_9.9", tmp_path) == (None, None)


def test_any_other_failure_reports_what_datasets_said(tmp_path, monkeypatch):
    """An NCBI outage must not look like a missing genome."""
    stderr = "New version of client (18.39.0) available at https://example.org\nError: 503 Service Unavailable"
    monkeypatch.setattr(subprocess, "run", fake_run(returncode=1, stderr=stderr))

    with pytest.raises(NCBIError) as excinfo:
        fetch_fasta_gff("GCA_1.1", tmp_path)
    message = str(excinfo.value)
    assert "GCA_1.1" in message and "503 Service Unavailable" in message
    assert "New version of client" not in message


def test_a_missing_datasets_command_says_so(tmp_path, monkeypatch):
    def run(cmd, **kwargs):
        raise FileNotFoundError("datasets")

    monkeypatch.setattr(subprocess, "run", run)
    with pytest.raises(NCBIError, match="not installed"):
        fetch_fasta_gff("GCA_1.1", tmp_path)


def test_a_clean_exit_without_a_zip_gives_none(tmp_path, monkeypatch):
    monkeypatch.setattr(subprocess, "run", fake_run())
    assert fetch_fasta_gff("GCA_1.1", tmp_path) == (None, None)
