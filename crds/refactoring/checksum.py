"""This script updates the checksums of all the mapping files passed in as 
command line parameters:

% python -m crds.checksum  hst.pmap

will rewrite the sha1sum of hst.pmap.   
"""
from __future__ import print_function
from __future__ import division
from __future__ import absolute_import

import sys

from crds.core import config, log, rmap
from crds.certify import mapping_parser

def update_checksum(file_):
    """Rewrite the checksum of a single mapping, in place.   Silently
    drops invalid duplicate match cases.
    """
    mapping = rmap.Mapping.from_file(file_, ignore_checksum=True)
    mapping.write()

def check_duplicates(file_):
    """Before rewriting an rmap to update the checksum, certify to ensure no
    duplicates (or other certify errors) exist prior to rewriting checksum.
    """
    parsing = mapping_parser.parse_mapping(file_)
    mapping_parser.check_duplicates(parsing)

def update_checksums(files):
    """Rewrite the mapping checksums/hashes/sha1sums in all `files`."""
    for file_ in files:
        log.info("Updating checksum for", file_)
        with log.error_on_exception("Failed updating checksum for", repr(file_)):
            old_errs = log.errors()
            check_duplicates(file_)
            new_errs = log.errors()
            if (new_errs == old_errs):
                update_checksum(file_)
                
if __name__ == "__main__":
    import crds
    update_checksums(sys.argv[1:])
    log.standard_status()
    sys.exit(log.errors())
