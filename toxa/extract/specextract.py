from astropy.io import fits
from astropy.io import fits
from os.path import join as pjoin
import os
import glob

def update_header(phapath, *, ancrfile, respfile, backfile):
    with fits.open(phapath, mode="update") as hdul:
        hdu:fits.FitsHDU = hdul["SPECTRUM"]
        hdu.header.update({
            "ANCRFILE": ancrfile,
            "RESPFILE": respfile,
            "BACKFILE": backfile
        })

        hdul.flush()

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
