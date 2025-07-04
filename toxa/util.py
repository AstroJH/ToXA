from astropy.io import fits

def calc_arearatio():
    ...


def update_header(phapath, *, ancrfile, respfile, backfile):
    with fits.open(phapath, mode="update") as hdul:
        hdu:fits.FitsHDU = hdul["SPECTRUM"]
        hdu.header.update({
            "ANCRFILE": ancrfile,
            "RESPFILE": respfile,
            "BACKFILE": backfile
        })

        hdul.flush()