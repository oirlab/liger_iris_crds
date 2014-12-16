"""This modules consolidates different kinds of information related to each
instrument and reference type under one data structure. Most of the information
contained here was reverse engineered from CDBS in a piecemeal fashion,  then
consolidated into the single common data structure to support future maintenance
and the addition of new types.
"""

# import sys
import pprint
import os.path
import collections
import glob

from crds import rmap, log, utils, data_file
# from crds.certify import TpnInfo

# =============================================================================
#  Global table loads used at operational runtime:

def _evalfile_with_fail(filename):
    """Evaluate and return a dictionary file,  returning {} if the file
    cannot be found.
    """
    if os.path.exists(filename):
        result = utils.evalfile(filename)
    else:
        log.warning("Couldn't load CRDS config file", repr(filename))
        result = {}
    return result

def _invert_instr_dict(dct):
    """Invert a set of nested dictionaries of the form {instr: {key: val}}
    to create a dict of the form {instr: {val: key}}.
    """
    inverted = {}
    for instr in dct:
        inverted[instr] = utils.invert_dict(dct[instr])
    return inverted

# =============================================================================

# UNIFIED_DEFS = _evalfile_with_fail(os.path.join(HERE, "reftypes.dat"))

# SPEC_PATH = os.path.join(HERE, "specs")
# SPEC_PATH = "specs"

# UNIFIED_DEFS = load_specs()

def write_specs():
    from .__init__ import TEXT_DESCR
    for instr in UNIFIED_DEFS:
        for reftype in UNIFIED_DEFS[instr]:
            specname = os.path.join(SPEC_PATH, instr + "_" + reftype + ".spec")
            with open(specname, "w+") as spec:
                UNIFIED_DEFS[instr][reftype]["text_descr"] = TEXT_DESCR[reftype]
                write_spec(spec, UNIFIED_DEFS[instr][reftype])

def write_spec(spec, spec_dict):
    spec.write("{\n")
    for name, value in sorted(spec_dict.iteritems()):
        spec.write("    " + repr(name) + ": ")
        if isinstance(value, basestring) and "\n" in value:
            spec.write("'''\n")
            for line in value.splitlines():
                spec.write(line + "\n")
            spec.write("''',\n")
        else:
            spec.write(repr(value) + ",\n")
    spec.write("}\n")

# =============================================================================

class TypeSpec(dict):
    pass

def load_specs(spec_path):
    with log.error_on_exception("Failed loading type specs."):
        specs = collections.defaultdict(dict)
        for spec in glob.glob(os.path.join(spec_path, "*.spec")):
            instr, reftype = os.path.splitext(os.path.basename(spec))[0].split("_")
            with log.error_on_exception("Failed loading", repr(spec)):
                specs[instr][reftype] = TypeSpec(utils.evalfile(spec))
        return specs
    return {}

# =============================================================================

def from_package_file(pkg):
    here = (os.path.dirname(pkg) or ".")
    specs_path = os.path.join(here, "specs") 
    unified_defs = load_specs(specs_path)
    return TypeParameters(unified_defs)

class TypeParameters(utils.Struct):

    def __init__(self, unified_defs):

        self.unified_defs = unified_defs

        with log.error_on_exception("Can't determine instruments from specs."):
            self.instruments = sorted(self.unified_defs.keys())

        with log.error_on_exception("Can't determine types from specs."):
            self.filekinds = sorted(
                set(reftype for instr, reftypes in self.unified_defs.items()
                    for reftype in reftypes))

        with log.error_on_exception("Can't determine extensions from specs."):
            self.extensions = sorted(
                set(params.get("file_ext", ".fits") for instr, reftypes in self.unified_defs.items()
                    for reftype, params in reftypes.items()))

        with log.error_on_exception("Can't determine type text descriptions from specs."):
            self.text_descr = {
                reftype : params["text_descr"] for instr, reftypes in self.unified_defs.items()
                for reftype, params in reftypes.items()
                }

        with log.error_on_exception("Failed determining filekind_to_suffix"):
            self.filekind_to_suffix = {
                instr : {
                    filekind : self.unified_defs[instr][filekind]["suffix"]
                    for filekind in self.unified_defs[instr]
                    }
                for instr in self.unified_defs
                }
            
        with log.error_on_exception("Failed determining suffix_to_filekind"):
            self.suffix_to_filekind = _invert_instr_dict(self.filekind_to_suffix)

        with log.error_on_exception("Failed determining filetype_to_suffix"):
            self.filetype_to_suffix = {
                instr : {
                    self.unified_defs[instr][filekind]["filetype"] : self.unified_defs[instr][filekind]["suffix"]
                    for filekind in self.unified_defs[instr]
                    }
                for instr in self.unified_defs
                }

        with log.error_on_exception("Failed determining suffix_to_filetype"):
            self.suffix_to_filetype = _invert_instr_dict(self.filetype_to_suffix)

        with log.error_on_exception("Failed determining unique_rowkeys"):
            self.rowkeys = {
                instr : {
                    filekind : self.unified_defs[instr][filekind]["unique_rowkeys"]
                    for filekind in self.unified_defs[instr]
                    }
                for instr in self.unified_defs
                }

    def filetype_to_filekind(self, instrument, filetype):
        """Map the value of a FILETYPE keyword onto it's associated
        keyword name,  i.e.  'dark image' --> 'darkfile'
        """
        instrument = instrument.lower()
        filetype = filetype.lower()
        if instrument == "nic":
            instrument = "nicmos"
        ext = self.filetype_to_suffix[instrument][filetype]
        return self.suffix_to_filekind[instrument][ext]

    def extension_to_filekind(self, instrument, extension):
        """Map the value of an instrument and TPN extension onto it's
        associated filekind keyword name,  i.e. drk --> darkfile
        """
        if instrument == "nic":
            instrument = "nicmos"
        return self.suffix_to_filekind[instrument][extension]

# =============================================================================

    def mapping_validator_key(self, mapping):
        """Return (_ld.tpn name, ) corresponding to CRDS ReferenceMapping `mapping` object."""
        return (self.unified_defs[mapping.instrument][mapping.filekind]["ld_tpn"],)
        # return reference_name_to_validator_key(mapping.filepath, field="ld_tpn")

    def reference_name_to_validator_key(self, filename, field="tpn"):
        """Given a reference filename `fitsname`,  return a dictionary key
        suitable for caching the reference type's Validator.
        
        This revised version supports computing "subtype" .tpn files based
        on the parameters of the reference.   Most references have unconditional
        associations based on (instrument, filekind).   A select few have
        conditional lookups which select between several .tpn's for the same
        instrument and filetype.
        
        Returns (.tpn filename,)
        """
        header = data_file.get_header(filename)
        instrument = header["INSTRUME"].lower()
        filetype = header["FILETYPE"].lower()
        filekind = self.filetype_to_filekind(instrument, filetype)
        tpnfile = self.unified_defs[instrument][filekind][field]
        if isinstance(tpnfile, basestring):
            key = (tpnfile,)  # tpn filename
        else: # it's a list of conditional tpns
            for (condition, tpn) in tpnfile:
                if eval(condition, header):
                    key = (tpn,)  # tpn filename
                    break
            else:
                raise ValueError("No TPN match for reference='{}' instrument='{}' reftype='{}'".format(
                        os.path.basename(filename), instrument, filekind))
        log.verbose("Validator key for", field, "for", repr(filename), instrument, filekind, "=", key)
        return key

    reference_name_to_tpn_key = reference_name_to_validator_key

    def reference_name_to_ld_tpn_key(self, filename):
        """Return the _ld.tpn file key associated with reference `filename`.
        Strictly speaking this should be driven by mapping_validator_key...  but the interface
        for that is wrong so slave it to reference_name_to_tpn_key instead,  historically
        one-for-one.
        """
        return self.reference_name_to_validator_key(filename, field="ld_tpn")

# =============================================================================

    def get_row_keys(self, mapping):
        """Return the row_keys which define unique table rows corresponding to mapping.
        
        These are used for "mode" checks to issue warnings when unique rows are deleted
        in a certify comparison check against the preceding version of a table.
        
        row_keys are now also utlized to perform "affected datasets" table row
        lookups which essentially requires emulating that aspect of the calibration
        software.  Consequently, row_keys now have a requirement for a higher level
        of fidelity since they were originally defined for mode checks, since the
        consequences of inadequate row keys becomes failed "affects checks" and not
        merely an extraneous warning.  In their capacity as affected datasets
        parameters,  row_keys must be supported by the interface which connects the
        CRDS server to the appropriate system dataset parameter database,  DADSOPS
        for HST.   That interface must be updated when row_keys.dat is changed.
        
        The certify mode checks have a shaky foundation since the concept of mode
        doesn't apply to all tables and sometimes "data" parameters are required to
        render rows unique.   The checks only issue warnings however so they can be
        ignored by file submitters.
        
        For HST calibration references mapping is an rmap.
        """
        mapping = rmap.asmapping(mapping)
        return self.rowkeys[mapping.instrument][mapping.filekind]

    def get_row_keys_by_instrument(self, instrument):
        """To support defining the CRDS server interface to DADSOPS, return the
        sorted list of row keys necessary to perform all the table lookups
        of an instrument.   These (FITS) keywords will be used to instrospect
        DADSOPS and identify table fields which provide the necessary parameters.
        """
        keyset = set()
        for filekind in self.row_keys[instrument]:
            typeset = set(self.row_keys[instrument][filekind] or [])
            keyset = keyset.union(typeset)
        return sorted([key.lower() for key in keyset])

# =============================================================================

    def get_filekinds(self, instrument):
        """Return the sequence of filekind strings for `instrument`."""
        return self.filekind_to_suffix[instrument.lower()].keys()

    def get_item(self, instrument, filekind, name):
        """Return config item `name` for `instrument` and `filekind`"""
        return self.unified_defs[instrument][filekind][name]
