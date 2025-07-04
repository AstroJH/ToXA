from os.path import join as pjoin
import glob
import os
from astropy.io import fits
from astropy.table import Table
import numpy as np
from os.path import join as pjoin
from typing import Literal
from .. import template
from ..util import update_header

def fxt_rootname():
    ...

def search_fxtinfo(dirpath, obsid, module):
    event_dir = pjoin(dirpath, "fxt", "event")
    hk_dir = pjoin(dirpath, "fxt", "hk")

    files = glob.glob(f"fxt_{module}_{obsid}_*_evt_*.fits", root_dir=event_dir)
    if len(files) != 1: raise Exception()
    file = files[0]
    fname = os.path.basename(file)
    comp = fname.split("_")

    result = {
        "mode": comp[3],
        "filter": comp[4],
        "pp": comp[5],
        "lev": comp[8].split(".")[0]
    }

    files = glob.glob(f"fxt_{obsid}_mkf_*.fits", root_dir=hk_dir)
    if len(files) != 1: raise Exception()
    file = files[0]
    fname = os.path.basename(file)
    comp = fname.split("_")

    result.update({ "lev_mkf": comp[3].split(".")[0] })

    return result

def specextract(*,
    evtpath:str,
    srcreg:str,
    bkgreg:str,
    gtis,
    output:str,
    fnameroot=None,
    **kwargs
):
    bkgpha_fname = f"{fnameroot}_bkg.pha"
    pha_fname = f"{fnameroot}.pha"

    phapath = pjoin(output, pha_fname)
    phapath_bkg = pjoin(output, bkgpha_fname)
    

    script = template.xselect.extract_spectrum(
        dirpath=os.path.dirname(evtpath),
        evtfname=os.path.basename(evtpath),
        phapath=phapath,
        phapath_bkg=phapath_bkg,
        gtis=gtis,
        srcreg=srcreg,
        bkgreg=bkgreg
    )

    os.system(script)


def specextract_fxt(*,
    dirpath:str,
    obsid:str,
    mode:Literal["ff", "pw", "tm"],
    module:Literal["a", "b"],
    filter:str,
    pp:Literal["po"],
    lev:str,
    lev_mkf:str,
    srcreg:str,
    bkgreg:str,
    gtis,
    output:str,
    psfcor:bool=False,
    fnameroot=None,
):
    if fnameroot is None:
        fnameroot = f"fxt_{module}_{obsid}_{mode}_{filter}_{pp}"

    arfname = f"{fnameroot}.arf"
    rmfname = f"{fnameroot}.rmf"
    expofname = f"{fnameroot}.exp"
    expo_without_vign = f"{fnameroot}-without_vign.exp"
    bkgpha_fname = f"{fnameroot}_bkg.pha"
    pha_fname = f"{fnameroot}.pha"

    phapath = pjoin(output, pha_fname)
    phapath_bkg = pjoin(output, bkgpha_fname)
    expopath = pjoin(output, expofname)
    arfpath = pjoin(output, arfname)
    rmfpath = pjoin(output, rmfname)
    
    evtfname = f"{fnameroot}_cl_{lev}.fits"
    mkfname = f"fxt_{obsid}_mkf_{lev_mkf}.fits"

    evtpath = pjoin(dirpath, "fxt", "products", evtfname)
    mkfpath = pjoin(dirpath, "fxt", "hk", mkfname)

    script = template.xselect.extract_spectrum(
        dirpath=os.path.dirname(evtpath),
        evtfname=evtfname,
        phapath=phapath,
        phapath_bkg=phapath_bkg,
        gtis=gtis,
        srcreg=srcreg,
        bkgreg=bkgreg
    )

    os.system(script)

    os.system(f"fxtexpogen mkffile={mkfpath} evtfile={evtpath} outfile={expopath}")
    os.system(f"fxtarfgen specfile={phapath} expfile={expo_without_vign} psfcor={1 if psfcor else 0} outfile={arfpath}")
    os.system(f"fxtrmfgen specfile={phapath} outfile={rmfpath}")

    update_header(phapath, ancrfile=arfname, respfile=rmfname, backfile=bkgpha_fname)


def extractcurve_fxt(*,
    dirpath:str,
    obsid:str,
    mode:Literal["ff", "pw", "tm"],
    module:Literal["a", "b"],
    filter:str,
    pp:Literal["po"],
    lev:str,
    srcreg:str,
    bkgreg:str,
    output:str,
    **kwargs
):

    fnameroot = f"fxt_{module}_{obsid}_{mode}_{filter}_{pp}"
    bkgcurve_fname = f"{fnameroot}_bkg.lc"
    curve_fname = f"{fnameroot}.lc"

    curvepath = pjoin(output, curve_fname)
    curvepath_bkg = pjoin(output, bkgcurve_fname)
    
    evtfname = f"{fnameroot}_cl_{lev}.fits"

    evtpath = pjoin(dirpath, "fxt", "products", evtfname)

    script = template.xselect.extract_lcurve(
        dirpath=os.path.dirname(evtpath),
        evtfname=evtfname,
        curvepath=curvepath,
        curvepath_bkg=curvepath_bkg,
        srcreg=srcreg,
        bkgreg=bkgreg,
        binsize=1
    )

    os.system(script)
