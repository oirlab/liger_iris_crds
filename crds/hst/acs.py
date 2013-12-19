"""This module defines CRDS customizations for the HST ACS instrument."""

import sys

from crds import log, utils, timestamp

from collections import defaultdict

# ===========================================================================    

#   This section contains matching customizations.

ACS_HALF_CHIP_COLS = 2048         #used in custom bias selection algorithm

SM4 = timestamp.reformat_date("2009-05-14 00:00")
# date beyond which an exposure was
# taken in the SM4 configuration
# (day 2009.134 = May 14 2009,
#  after HST was captured by 
#  the shuttle during SM4, and
#  pre-SM4 exposures had ceased)

def precondition_header(rmap, header):
    """This is the original buggy header preconditioning function for ACS which
    applied to all types but only really affected BIASFILE.  It mutates dataset headers
    prior to performing bestrefs matching.   It is located and called by default when
    the rmap says nothing about hooks.
    """
    header = dict(header)
    if rmap.filekind == "biasfile":
        return precondition_header_biasfile_v1(rmap, header)
    else:
        return header
    
def precondition_header_biasfile_v1(rmap, header_in):
    """Mutate the incoming dataset header based upon hard coded rules
    and the header's contents.   This is an alternative to generating
    an equivalent and bulkier rmap.
    """
    header = dict(header_in)
    log.verbose("acs_biasfile_precondition_header:", header)
    exptime = timestamp.reformat_date(header["DATE-OBS"] + " " + header["TIME-OBS"])
    if (exptime < SM4):
        #if "APERTURE" not in header or header["APERTURE"] == "UNDEFINED":
        log.verbose("Mapping pre-SM4 APERTURE to N/A")
        header["APERTURE"] = "N/A"
    try:
        numcols = int(float(header["NUMCOLS"]))
    except ValueError:
        log.verbose("acs_biasfile_selection: bad NUMCOLS.")
        sys.exc_clear()
    else:
        header["NUMCOLS"] = utils.condition_value(str(numcols))
        # if pre-SM4 and NUMCOLS > HALF_CHIP
        exptime = timestamp.reformat_date(header["DATE-OBS"] + " " + header["TIME-OBS"])
        if (exptime < SM4):
            if numcols > ACS_HALF_CHIP_COLS:
                if header["CCDAMP"] in ["A","D"]: 
                    log.verbose("acs_bias_file_selection: exposure is pre-SM4, converting amp A or D " +
                                "to AD for NUMCOLS = " + header["NUMCOLS"])
                    header["CCDAMP"] = "AD"
                elif header["CCDAMP"] in ["B","C"]:  
                    log.verbose("acs_bias_file_selection: exposure is pre-SM4, converting amp B or C " +
                                "to BC for NUMCOLS = " + header["NUMCOLS"])
                    header["CCDAMP"] = "BC"
    if header['DETECTOR'] == "WFC" and \
        header['XCORNER'] == "0.0" and header['YCORNER'] == "0.0":
        log.verbose("acs_biasfile_selection: precondition_header halving NUMROWS")
        try:
            numrows = int(float(header["NUMROWS"])) / 2
        except ValueError:
            log.verbose("acs_biasfile_selection: bad NUMROWS.")
            sys.exc_clear()
        else:
            header["NUMROWS"] = utils.condition_value(str(numrows)) 
    return header     # XXXXXX RETURN NOW !!!!

def precondition_header_biasfile_v2(rmap, header_in):
    """Preconditions ACS BIASFILE dataset matching header prior to matching.
    
    v2 substitutes NAXIS1, NAXIS2 for NUMCOLS, NUMROWS in the first buggy version.
    
    v2 is only called when explicitly added to an rmap in the "hooks" header section.
    """
    header = dict(header_in)

    if "NAXIS1" not in header:
        header["NAXIS1"] = header.get("NUMCOLS","UNDEFINED")
    if "NAXIS2" not in header:
        header["NAXIS2"] = header.get("NUMROWS","UNDEFINED")

    log.verbose("acs_biasfile_precondition_header:", log.PP(header))
    exptime = timestamp.reformat_date(header["DATE-OBS"] + " " + header["TIME-OBS"])
    if (exptime < SM4):
        #if "APERTURE" not in header or header["APERTURE"] == "UNDEFINED":
        log.verbose("Mapping pre-SM4 APERTURE to N/A")
        header["APERTURE"] = "N/A"
    try:
        numcols = int(float(header["NAXIS1"]))
    except ValueError:
        log.verbose("acs_biasfile_selection: bad NAXIS1.")
        sys.exc_clear()
    else:
        header["NAXIS1"] = utils.condition_value(str(numcols))
        # if pre-SM4 and NAXIS1 > HALF_CHIP
        exptime = timestamp.reformat_date(header["DATE-OBS"] + " " + header["TIME-OBS"])
        if (exptime < SM4):
            if numcols > ACS_HALF_CHIP_COLS:
                if header["CCDAMP"] in ["A","D"]: 
                    log.verbose("acs_bias_file_selection: exposure is pre-SM4, converting amp A or D " +
                                "to AD for NAXIS1 = " + header["NAXIS1"])
                    header["CCDAMP"] = "AD"
                elif header["CCDAMP"] in ["B","C"]:  
                    log.verbose("acs_bias_file_selection: exposure is pre-SM4, converting amp B or C " +
                                "to BC for NAXIS1 = " + header["NAXIS1"])
                    header["CCDAMP"] = "BC"
    if header['DETECTOR'] == "WFC" and \
        header['XCORNER'] == "0.0" and header['YCORNER'] == "0.0":
        log.verbose("acs_biasfile_selection: precondition_header halving NAXIS2")
        try:
            numrows = int(float(header["NAXIS2"])) / 2
        except ValueError:
            log.verbose("acs_biasfile_selection: bad NAXIS2.")
            sys.exc_clear()
        else:
            header["NAXIS2"] = utils.condition_value(str(numrows)) 
    return header     # XXXXXX RETURN NOW !!!!

# ===========================================================================    

#   This section contains matching customizations.

# (('DETECTOR', 'CCDAMP', 'CCDGAIN', 'APERTURE', 'NUMCOLS', 'NUMROWS', 'LTV1', 'LTV2', 'XCORNER', 'YCORNER', 'CCDCHIP'), ('DATE-OBS', 'TIME-OBS')),

"""
def _fallback_biasfile(header_in):
    header = _precondition_header_biasfile(header_in)
    log.verbose("No matching BIAS file found for",
               "NUMCOLS=" + repr(header['NUMCOLS']),
               "NUMROWS=" + repr(header['NUMROWS']),
               "LTV1=" + repr(header['LTV1']),
               "LTV2=" + repr(header['LTV2']))
    log.verbose("Trying full-frame default search")
    if header['DETECTOR'] == "WFC":
        header["NUMCOLS"] = "4144.0"
        header["NUMROWS"] = "2068.0"
        header["LTV1"] = "24.0"
        header["LTV2"] = "0.0"
    else:
        header["NUMCOLS"] = "1062.0"
        header["NUMROWS"] = "1044.0"
        header["LTV1"] = "19.0"
        if header['CCDAMP'] in ["C","D"]:
            header["LTV2"] = "0.0"
        else: # assuming HRC with CCDAMP = A or B
            header["LTV2"] = "20.0"
    return header

def fallback_header(rmap, header):
    return None
    if rmap.filekind == "biasfile":
        # log.info("x", end="",sep="")
        return _fallback_biasfile(header)
    else:
        None
"""

# In theory,  this moves the fallback header computation to rmap insertion time.
# This is horrendous,  a second mechanism in addition to the kmap filter for 
# implementing fallbacks which execute in one pass via a more sophisticated rmap
# rather than as a second call to getreferences.
def reference_match_fallback_header(rmap, header):
    """Called at rmap generation and update time to add a weaker "fallback" match case for certain references.
    
    This is the CRDS emulation of a CDBS "try, try again with different query" behaviour.
    """
    if rmap.filekind == "biasfile":
        return reference_match_fallback_header_biasfile_v1(rmap, header)
    else:
        None

def reference_match_fallback_header_biasfile_v1(rmap, header_in):
    
    header = precondition_header_biasfile_v1(rmap, header_in)

    if header_matches(header, dict(DETECTOR='WFC', NUMCOLS='4144.0', NUMROWS='2068.0', LTV1='24.0', LTV2='0.0')):
        return dont_care(header, ['NUMROWS','NUMCOLS','LTV1', 'LTV2'])
    
    if header_matches(header, dict(DETECTOR='HRC', CCDAMP='C', NUMROWS='1044.0', NUMCOLS='1062.0', LTV1='19.0', LTV2='0.0')):
        return dont_care(header, ['NUMROWS','NUMCOLS','LTV1', 'LTV2'])
    
    if header_matches(header, dict(DETECTOR='HRC', CCDAMP='D', NUMROWS='1044.0', NUMCOLS='1062.0', LTV1='19.0', LTV2='0.0')):
        return dont_care(header, ['NUMROWS','NUMCOLS','LTV1', 'LTV2'])
    
    if header_matches(header, dict(DETECTOR='HRC', CCDAMP='C|D', NUMROWS='1044.0', NUMCOLS='1062.0', LTV1='19.0', LTV2='0.0')):
        return dont_care(header, ['NUMROWS','NUMCOLS','LTV1', 'LTV2'])
    
    if header_matches(header, dict(DETECTOR='HRC', CCDAMP='A', NUMROWS='1044.0', NUMCOLS='1062.0', LTV1='19.0', LTV2='20.0')):
        return dont_care(header, ['NUMROWS','NUMCOLS','LTV1', 'LTV2'])
    
    if header_matches(header, dict(DETECTOR='HRC', CCDAMP='B', NUMROWS='1044.0', NUMCOLS='1062.0', LTV1='19.0', LTV2='20.0')):
        return dont_care(header, ['NUMROWS','NUMCOLS','LTV1', 'LTV2'])
    
    if header_matches(header, dict(DETECTOR='HRC', CCDAMP='A|B', NUMROWS='1044.0', NUMCOLS='1062.0', LTV1='19.0', LTV2='20.0')):
        return dont_care(header, ['NUMROWS','NUMCOLS','LTV1', 'LTV2'])
    
    return header

def header_matches(header, conditions):
    for var, val in conditions.items():
        if header[var] != val:
            return False
    return True

def dont_care(header, vars):
    header = dict(header)
    for var in vars:
        header[var] = "N/A"
    return header

def reference_match_fallback_header_biasfile_v2(rmap, header_in):
    """Given a reference file header specifying the applicable cases for a reference,  this generates
    a weaker match case which may apply when the primary match fails.  Called to update rmaps
    with "fallback cases" when a file is submitted to the CRDS web site and it updates the rmap,
    in addition to the primary match cases from the unaltered header_in.  
    """
    header = precondition_header_biasfile_v2(header_in)

    if header_matches(header, dict(DETECTOR='WFC', NAXIS1='4144.0', NAXIS2='2068.0', LTV1='24.0', LTV2='0.0')):
        return dont_care(header, ['NAXIS2','NAXIS1','LTV1', 'LTV2'])
    
    if header_matches(header, dict(DETECTOR='HRC', CCDAMP='C', NAXIS2='1044.0', NAXIS1='1062.0', LTV1='19.0', LTV2='0.0')):
        return dont_care(header, ['NAXIS2','NAXIS1','LTV1', 'LTV2'])
    
    if header_matches(header, dict(DETECTOR='HRC', CCDAMP='D', NAXIS2='1044.0', NAXIS1='1062.0', LTV1='19.0', LTV2='0.0')):
        return dont_care(header, ['NAXIS2','NAXIS1','LTV1', 'LTV2'])
    
    if header_matches(header, dict(DETECTOR='HRC', CCDAMP='C|D', NAXIS2='1044.0', NAXIS1='1062.0', LTV1='19.0', LTV2='0.0')):
        return dont_care(header, ['NAXIS2','NAXIS1','LTV1', 'LTV2'])
    
    if header_matches(header, dict(DETECTOR='HRC', CCDAMP='A', NAXIS2='1044.0', NAXIS1='1062.0', LTV1='19.0', LTV2='20.0')):
        return dont_care(header, ['NAXIS2','NAXIS1','LTV1', 'LTV2'])
    
    if header_matches(header, dict(DETECTOR='HRC', CCDAMP='B', NAXIS2='1044.0', NAXIS1='1062.0', LTV1='19.0', LTV2='20.0')):
        return dont_care(header, ['NAXIS2','NAXIS1','LTV1', 'LTV2'])
    
    if header_matches(header, dict(DETECTOR='HRC', CCDAMP='A|B', NAXIS2='1044.0', NAXIS1='1062.0', LTV1='19.0', LTV2='20.0')):
        return dont_care(header, ['NAXIS2','NAXIS1','LTV1', 'LTV2'])
    
    return header

# =============================================================================================

# This section contains RMAP GENERATION code. It is unversioned, plugging into hst_gentools/gen_rmap.py and
# running only at rmap generation time during system bootstrap.  It is closely related to 
# reference_match_fallback_header_biasfile which runs at rmap update time to add new files.

def acs_biasfile_filter(kmap):
    """APERTURE was added late as a matching parameter and so many existing references
    have an APERTURE value of '' in CDBS.   Where it's relevant,  it's actually defined.
    Here we change '' to * to make CRDS ignore it when it doesn't matter.   We also change 
    APERTURE to * for any useafter date which precedes SM4 (possibly they define APERTURE).
    
    add_fallback_to_kmap() duplicates the correct filemaps to simulate the fallback header lookup.
    """
    replacement = "*"
    log.info("Hacking ACS biasfile  APERTURE macros.  Changing APERTURE='' to APERTURE='%s'" % replacement)
    start_files = total_files(kmap)
    for match, fmaps in kmap.items():
        new_key = na_key(match, replacement)
        if match[3] == '':
            if new_key not in kmap:
                kmap[new_key] = []
            kmap[new_key] = sorted(set(kmap[new_key] + fmaps))
            del kmap[match]
            for fmap in fmaps:
                log.info("Unconditionally mapping APERTURE '' to '%s' for" % replacement, fmap)
            continue
        remap_fmaps = []
        for fmap in fmaps[:]:
            if fmap.date < SM4:
                log.info("Remapping <SM4 APERTURE to '%s'" % replacement, repr(fmap))
                remap_fmaps.append(fmap)
                fmaps.remove(fmap)
        if remap_fmaps:
            if new_key not in kmap:
                kmap[new_key] = []
            kmap[new_key].extend(remap_fmaps)
            log.info("Moving", match, "to", new_key, "for files", total_files({None:remap_fmaps}))
            log.info("Remainder", match, "=", total_files({None:kmap[match]}))
            # log.info("New kmap for", repr(new_key), "is", repr(kmap[new_key]))
        if not fmaps and (new_key != match):
            del kmap[match]

    dropped_files = start_files - total_files(kmap)
    if dropped_files:  # bummer,  bug in my code...
        log.error("Dropped files:", sorted(dropped_files))

    kmap = add_fallback_to_kmap(kmap, 
        matches=dict(DETECTOR='WFC', NAXIS1='4144.0', NAXIS2='2068.0', LTV1='24.0', LTV2='0.0'),
        dont_care=['NAXIS2','NAXIS1','LTV1', 'LTV2'])
    
    kmap = add_fallback_to_kmap(kmap, 
        matches=dict(DETECTOR='HRC', CCDAMP='C', NAXIS2='1044.0', NAXIS1='1062.0', LTV1='19.0', LTV2='0.0'),
        dont_care=['NAXIS2','NAXIS1','LTV1', 'LTV2'])
    
    kmap = add_fallback_to_kmap(kmap, 
        matches=dict(DETECTOR='HRC', CCDAMP='D', NAXIS2='1044.0', NAXIS1='1062.0', LTV1='19.0', LTV2='0.0'),
        dont_care=['NAXIS2','NAXIS1','LTV1', 'LTV2'])
    
    kmap = add_fallback_to_kmap(kmap, 
        matches=dict(DETECTOR='HRC', CCDAMP='A', NAXIS2='1044.0', NAXIS1='1062.0', LTV1='19.0', LTV2='20.0'),
        dont_care=['NAXIS2','NAXIS1','LTV1', 'LTV2'])
    
    kmap = add_fallback_to_kmap(kmap, 
        matches=dict(DETECTOR='HRC', CCDAMP='B', NAXIS2='1044.0', NAXIS1='1062.0', LTV1='19.0', LTV2='20.0'),
        dont_care=['NAXIS2','NAXIS1','LTV1', 'LTV2'])

    header_additions = [
        ("hooks",  {
            "precondition_header" : "precondition_header_biasfile_v2",
            "reference_match_fallback_header" : "reference_match_fallback_header_biasfile_v2",
        }),
    ]

    return kmap, header_additions

#  An old example of hacking the kmap....
#     kmap[('UVIS', 'G280_AMPS', 1.5, 1.0, 1.0, 'G280-REF', 'T')] = \
#       [rmap.Filemap(date='1990-01-01 00:00:00', file='t6i1733ei_bia.fits',
#               comment='Placeholder file. All values set to zero.--------------------------, 12047, Jun 18 2009 05:36PM')]
#    return kmap, header_additions

def na_key(match, replacement='*'):
    """Replace APERTURE with N/A or *"""
    new = list(match)
    new[3] = replacement
    return tuple(new)

def total_files(kmap):
    total = set()
    for match, fmaps in kmap.items():
        total = total.union(set([fmap.file for fmap in fmaps]))
    return total
        
def add_fallback_to_kmap(kmap, matches, dont_care,
                         parkeys=('DETECTOR', 'CCDAMP', 'CCDGAIN', 'APERTURE', 
                                  'NAXIS1', 'NAXIS2', 'LTV1', 'LTV2', 'XCORNER', 'YCORNER', 'CCDCHIP')):
    """Copy items in `kmap` whose keys match the parameters in `matches`,  setting
    the key-copy values named in `dont_care` to 'N/A'.   The copy with some 'N/A's is a fallback.
    `parkeys` names the items of each tuple key in `kmap`,  in order.
    """
    kmap = defaultdict(list, kmap.items())
    for key in kmap.keys():
        if key_matches(key, parkeys, matches):
            new_key = set_dont_care(key, parkeys, dont_care)
#            if new_key not in kmap:
#                kmap[new_key] = []
            kmap[new_key].extend(list(kmap[key]))
            kmap[new_key].sort()
            log.info("Creating fallback", repr(key), "-->", repr(new_key))
    return kmap

def key_matches(key, parkeys, matches):
    """Return True IFF `key` matches all the values in dict `matches`.
    Corresponding values in tuple `key` are named by values in `parkeys`.
    """
    for i, name in enumerate(parkeys):
        if name in matches:
            if utils.condition_value(matches[name]) != utils.condition_value(key[i]):
                log.verbose("Exiting on", repr(name), 
                         utils.condition_value(matches[name]),
                         utils.condition_value(key[i]))
                return False
    log.verbose("Matching", repr(key))
    return True

def set_dont_care(key, parkeys, dont_care):
    """Set the values of `key` named in `dont_care` to 'N/A'."""
    key = list(key)
    for i, name in enumerate(parkeys):
        if name in dont_care:
            key[i] = 'N/A'
    return tuple(key)

# =============================================================================================
#
# This section contains relevant code from cdbsquery.py and explanation,  such as it is.
# cdbsquery.py was/is part of CDBS.  This module is about capturing those quirks in different
# ways for CRDS.
#
'''
This is special case code which CDBS implements in cdbsquery.py 
(see crds/hst/cdbs/cdbs_bestrefs/cdbsquery.py or get the latest from Mike Swam / OPUS)

Fundamentally, cdbsquery searches the reference file database
(reffile_ops...) which enumerates how specific dataset header
configurations map onto reference files.  Each row of reffile_ops maps
one instrument configuration and date onto the reference file which
handles it.  Some files are used in many rows.  Each column of a row
specifies the value of a particular parameter.

reffile_ops matching parameters, and other things,  are specified in the CDBS file
reference_file_defs.xml.   Parameters listed here are important in some way for
matching.

Ideally,  CDBS and CRDS implement something like:   

   match(dataset parameters, reference parameters) --> reference.

Here dataset and reference correspond to the tuples of relevant header values
or database values.  1:1,  match them up,  shebang.

CDBS does the matching as a single SQL query against refile_ops...  cdbsquery
builds the SQL which constrains each parameter to the configuration of one dataset.

CRDS encodes the matching parameters of reference_file_ops in a
more compact way,  the rmaps.   The rmaps are interpreted by CRDS code
in selectors.py rather than by a SQL engine.

In practice,  CDBS special case code like that below does this:   

   match(f(dataset parameters), reference parameters) -->  reference or g(dataset)

There are a few kinds of hacks:

1. The special case code excludes some dataset parameters from
matching in the reference database.  There might be no column for that
parameter but it is needed later.

2. The special case code fudges some of the dataset parameters,
replacing dataset[X] with f(dataset),  where the fudged value of one 
matching parameter may depend on the value of many other parameters.

3. Sometimes fallback code,  g(dataset),  is used as a secondary solution
when the primary solution fails to obtain a match.

In CDBS:

"dataset" can come from the dadsops database (there are many servers and variants).

"dataset" can come from a FITS header.

At match time,  "reference" comes from the reffile_ops database.   Matching is
done by doing a gigantic anded SQL query which equates reffile_ops columns with 
specific dataset values,  doing a gigantic anded SQL query,  and also choosing 
the maximum applicable USEAFTER.  In cdbsquery,  the query is built one 
parameter at a time.   Some parameters are omitted from the query.

At new reference submission time, "reference" comes from the ref file
header and is exploded in to refile_ops database rows.

In CRDS:

"dataset" comes from the same places, either a database or dataset file header.
  
At rmap generation time,  "reference" comes from the reffile_ops database and
is encoded into rmaps.

At new file submission time, "reference" comes from the reference file
headers and must be appropriately matched against rmaps to see where
to insert or replace files.   This is batch reference submission / refactoring.

At match time, essentially "reference" comes from the rmaps and
matching is done by recursively executing CRDS selector.py Selector code
on nested selectors.

# ================================================================================

  def find_exposure_start(self, aSource):
    # fill the exposure start time, after converting keyword value
    # to datetime format from source format
    beyond_SM4 = True    # default
    try:
      if aSource._keywords.has_key('TEXPSTRT'):
       #timetuple = time.strptime(aSource._keywords['TEXPSTRT'][0],
       #                        "%Y.%m.%d %H:%M:%S")
        timetuple = time.strptime(aSource._keywords['TEXPSTRT'][0].rstrip(),
                                "%Y.%m.%d %H:%M:%S")
      elif aSource._keywords.has_key('EXPSTART'):
       #timetuple = time.strptime(aSource._keywords['EXPSTART'][0],
       #                        "%Y.%m.%d %H:%M:%S ")
        timetuple = time.strptime(aSource._keywords['EXPSTART'][0].rstrip(),
                                "%Y.%m.%d %H:%M:%S")
      #
      # these are used in FITS input mode
      elif (aSource._keywords.has_key('PSTRTIME') and
            aSource._keywords['PSTRTIME'][0] != ' '):
        opusutil.PrintMsg("D","Trying PSTRTIME for exposure start:"+
                          aSource._keywords['PSTRTIME'][0]+'|')
        # its there, use it and convert it
       #temptuple = time.strptime(aSource._keywords['PSTRTIME'][0],
       #                        "%Y.%j:%H:%M:%S")
        temptuple = time.strptime(aSource._keywords['PSTRTIME'][0].rstrip(),
                                "%Y.%j:%H:%M:%S")
        # convert DOY to month and day
        parts = string.split(aSource._keywords['PSTRTIME'][0],":")
        moparts = string.split(parts[0],".")
        if int(moparts[0]) % 4 == 0:
          modays = (31, 29, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31)
        else:
          modays = (31, 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31)
        monum = 0
        doy = int(moparts[1])
        while doy > modays[monum]:
          doy = doy - modays[monum]
          monum = monum + 1
        # adjust month to 1-relative value
        month = monum + 1
        day = doy
        timetuple = (temptuple[0],month,day,temptuple[3],temptuple[4],
                     temptuple[5],temptuple[6],temptuple[7],temptuple[8])
      elif (aSource._keywords.has_key('TVSTART') and 
            aSource._keywords['TVSTART'][0] != ' '):
        # thermal vac keyword for COS/WFC3 testing
        opusutil.PrintMsg("D","Trying TVSTART for exposure start:"+
                          aSource._keywords['TVSTART'][0]+'|')
        timetuple = time.strptime(aSource._keywords['TVSTART'][0],
                                  "%Y-%m-%dT%H:%M:%S")
      elif (aSource._keywords.has_key('DATE-OBS') and 
            aSource._keywords['DATE-OBS'][0] != ' ' and
            aSource._keywords.has_key('TIME-OBS') and 
            aSource._keywords['TIME-OBS'][0] != ' ') :
        opusutil.PrintMsg("D","Trying DATE-OBS,TIME-OBS for exposure start.")
        timetuple = time.strptime(aSource._keywords['DATE-OBS'][0]+' '+
                                  aSource._keywords['TIME-OBS'][0],
                                  "%Y-%m-%d %H:%M:%S")
      else:
        opusutil.PrintMsg("E","Failed to find any exposure start keys")
        raise FailedTimeConversion
      #
      exposure_start = time.strftime("%m/%d/%Y %H:%M:%S",timetuple)
      #
      # determine if exposure start is post SM4
      exposure_start_compare = time.strftime("%Y.%j:%H:%M:%S",timetuple)
      if (exposure_start_compare > SM4_YYYYDDDHHMMSS): beyond_SM4 = True
      else:                                            beyond_SM4 = False

    except Exception:
      traceback.print_exc()
      opusutil.PrintMsg("E","Failed time conversion for exposure start.")
      raise FailedTimeConversion
    #
    return exposure_start, beyond_SM4


  def acs_bias_file_selection(self, querynum, thereffile, aSource, beyond_SM4):
    querytxt = ""
    #
    # add the file selection fields
    for k in thereffile._file_selections:
      if k._restrictions:
        # see if the restriction allows this file selection field
        opusutil.PrintMsg("D",'found a file select restricted: '+
                               k._restrictions)
        if (not eval(k._restrictions)):
          opusutil.PrintMsg("D","File_selection on "+k._field+
                                " restricted away")
          continue
      #
      # skip these (not used in selection, only for special tests)
      if (k._field == 'XCORNER' or k._field == 'YCORNER' or
          k._field == 'CCDCHIP'):
          continue
      #
      # skip APERTURE prior to SM4, otherwise use it (PR 72156)
      if (k._field == 'APERTURE' and not beyond_SM4):
          continue
      #
      # special cases
      elif k._field == 'NUMROWS':
        querytxt = querytxt + "and acs_row_"+querynum+ ".naxis2 = OBS_NAXIS2 "
        continue
      elif k._field == 'NUMCOLS':
        querytxt = querytxt + "and acs_row_"+querynum+ ".naxis1 = OBS_NAXIS1 "
        continue
      elif k._field == 'LTV1':
        querytxt = querytxt + "and acs_row_"+querynum+ ".ltv1 = OBS_LTV1 "
        continue
      elif k._field == 'LTV2':
        querytxt = querytxt + "and acs_row_"+querynum+ ".ltv2 = OBS_LTV2 "
        continue
      # only apply this case for exposures before SM4
      elif k._field == 'CCDAMP' and not beyond_SM4:
        #
        # convert amp A or D reads to AD if size is more than half a chip
        if ((aSource._keywords["CCDAMP"][0] == "A" or
             aSource._keywords["CCDAMP"][0] == "D") and
            aSource._keywords["NUMCOLS"][0] > ACS_HALF_CHIP_COLS):
            opusutil.PrintMsg("I","acs_bias_file_selection: exposure is pre-SM4, converting amp A or D "+
                                  "to AD for NUMCOLS = "+
                                  str(aSource._keywords["NUMCOLS"][0]))
            aSource._keywords["CCDAMP"][0] = "AD"
        #
        # convert amp B reads to BC if size is more than half a chip
        elif ((aSource._keywords["CCDAMP"][0] == "B" or
               aSource._keywords["CCDAMP"][0] == "C") and
              aSource._keywords["NUMCOLS"][0] > ACS_HALF_CHIP_COLS):
            opusutil.PrintMsg("I","acs_bias_file_selection: exposure is pre-SM4, converting amp B or C"+
                                  "to BC for NUMCOLS = "+
                                  str(aSource._keywords["NUMCOLS"][0]))
            aSource._keywords["CCDAMP"][0] = "BC"
      #
      # apply the file selection field
      # (first as a string, but if that fails, as a number converted to string,
      #  since numbers are not quoted but string are)
      try:
        querytxt = (querytxt + "and acs_row_"+querynum+"." +
                 string.lower(k._field) + " = '" + 
                 aSource._keywords[k._field][0] + "' ")
      except TypeError:
        querytxt = (querytxt + "and acs_row_"+querynum+"." +
                 string.lower(k._field) + " = " + 
                 str(aSource._keywords[k._field][0]) + " ")
    #
    return querytxt
'''