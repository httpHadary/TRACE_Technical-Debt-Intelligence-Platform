"""Verify the already installed numerical runtime; never acquire dependencies."""
import base64
import csv
import hashlib
import importlib.metadata
from pathlib import Path


def runtime_identity():
    distribution=importlib.metadata.distribution('numpy')
    if distribution.version!='2.4.4':raise ValueError('Expected existing NumPy 2.4.4')
    records=[p for p in distribution.files if str(p).endswith('.dist-info/RECORD')]
    if len(records)!=1:raise ValueError('Missing unique runtime RECORD')
    files={}
    with Path(distribution.locate_file(records[0])).open(newline='') as f:
        for name,checksum,size in csv.reader(f):
            if not checksum:continue
            algorithm,expected=checksum.split('=',1)
            if algorithm!='sha256':raise ValueError('Unexpected runtime checksum')
            p=Path(distribution.locate_file(name))
            with p.open('rb') as source:raw=hashlib.file_digest(source,'sha256').digest()
            if base64.urlsafe_b64encode(raw).decode().rstrip('=')!=expected or p.stat().st_size!=int(size):
                raise ValueError('Installed NumPy integrity failure')
            files[name]=raw.hex()
    return dict(numpy_version=distribution.version,files=files,
        provenance='Existing local RECORD consistency; not independent publisher signature')
