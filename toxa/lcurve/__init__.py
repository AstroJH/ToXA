import os
from os.path import join as pjoin
import glob

import numpy as np

from astropy.io import fits
from astropy.table import Table, vstack

import matplotlib.pyplot as plt
from matplotlib.widgets import Button
from ..epta import fxt

def split_curve_by_gti(curve, gti):
    time = curve["TIME"]
    curves = []

    for row in gti:
        start = row["START"]
        stop = row["STOP"]

        mask = (time >= start) & (time <= stop)
        curves.append(curve[mask])
    
    return curves


def loadcurves(dirpath, fname):
    with fits.open(pjoin(dirpath, fname)) as hdul:
        header = hdul[0].header
        curve = Table(hdul["RATE"].data)
        gti = Table(hdul["GTI"].data)
        start0 = gti["START"][0]

        time = curve["TIME"]
        curves = []
        for row in gti:
            start = row["START"] - start0
            stop = row["STOP"] - start0

            mask = (time >= start) & (time <= stop)
            curves.append(curve[mask])
    return {
        "mjd_ref": header["MJDREFI"]+header["MJDREFF"],
        "t_start": header["TSTART"],
        "t_end": header["TEND"],
        "curves": curves
    }


def bincurve(curve, tbin):
    time_lo = []
    time_hi = []
    rate = []
    error = []

    time_sum = 0
    cts = 0
    time_start = -1
    err_2 = 0

    for row in curve:
        if time_start < 0:
            time_start = row["TIME"]

        time_sum += 1
        cts += row["RATE"]
        err_2 += row["ERROR"]**2

        if time_sum >= tbin:
            time_lo.append(time_start)
            time_hi.append(row["TIME"]+1)
            time_start = -1

            rate.append(cts/time_sum)
            cts = 0

            error.append(np.sqrt(err_2)/time_sum)
            err_2 = 0

            time_sum = 0
    return np.array(time_lo), np.array(time_hi), np.array(rate), np.array(error)


def combine_curves(files):
    curves = []
    gtis = []
    for f in files:
        with fits.open(f) as hdul:
            curve = Table(hdul["RATE"].data)
            gti = Table(hdul["GTI"].data)
            curves.append(curve)
            gtis.append(gti)
    
    curve = vstack(curves)
    gti = vstack(gtis)
    curve.sort(keys="TIME")
    gti.sort(keys="START")

    return curve, gti



class LightCurveViewer:
    def __init__(self, files:list, obsids:list):
        # self.files = glob.glob(file_pattern, root_dir=root_dir)

        tstarts = []
        for f in files:
            with fits.open(f) as hdul:
                tstart = hdul[0].header["TSTART"]
                tstarts.append(tstart)
        
        tstarts = np.array(tstarts)
        idx = np.argsort(tstarts)
        tstarts = tstarts[idx]
        self.tstarts = tstarts
        self.files = np.array(files)[idx]
        self.obsids = np.array(obsids)[idx]

        self.current_index = 0
        
        # Set up figure and axes
        self.fig, self.ax = plt.subplots(figsize=(10, 6))
        plt.subplots_adjust(bottom=0.2)
        
        # Create buttons
        ax_prev = plt.axes([0.59, 0.05, 0.1, 0.075])
        ax_next = plt.axes([0.7, 0.05, 0.1, 0.075])
        self.btn_prev = Button(ax_prev, 'Previous')
        self.btn_next = Button(ax_next, 'Next')
        
        # Connect events
        self.btn_prev.on_clicked(self.prev_file)
        self.btn_next.on_clicked(self.next_file)
        self.fig.canvas.mpl_connect('button_press_event', self.on_click)
        
        # Load and plot initial file
        self.load_plot_file()
    
    def load_plot_file(self):
        """Load current file and plot its light curve."""
        files = self.files

        self.ax.clear()

        idx = self.current_index
        self.ax.set_title(self.files[idx])
        self.ax.set_ylim(0, 18)

        lcpath:str = files[idx]
        bgpath = lcpath.replace(".lc", "_bkg.lc")
        with fits.open(lcpath) as hdul, fits.open(bgpath) as bghdul:
            data = Table(hdul[1].data)
            bgdata = Table(bghdul[1].data)
            gti = Table(hdul["GTI"].data)

            start0 = gti[0]["START"]

            binsize = 30
            for start, end in gti:
                start = start-start0
                end = end-start0
                mask = (data["TIME"]>=start) & (data["TIME"]<=end)
                curve = data[mask]
                bgcurve = bgdata[mask]

                lo, hi, rate, error = bincurve(curve, binsize)
                bglo, bghi, bgrate, bgerror = bincurve(bgcurve, binsize)
                time = (lo+hi)/2
                terr = (hi-lo)/2
                bgtime = (bglo+bghi)/2
                bgterr = (bghi-bglo)/2

                self.ax.errorbar(time, rate, xerr=terr, yerr=error, linestyle="none", color="k")
                self.ax.errorbar(bgtime, bgrate, xerr=bgterr, yerr=bgerror, linestyle="none", color="grey")

        self.fig.canvas.draw_idle()
    
    def prev_file(self, event):
        """Load previous light curve file."""
        self.current_index = (self.current_index - 1) % len(self.files)
        self.load_plot_file()
    
    def next_file(self, event):
        """Load next light curve file."""
        self.current_index = (self.current_index + 1) % len(self.files)
        self.load_plot_file()
    
    def on_click(self, event):
        """Handle mouse clicks on the plot area."""

        idx = self.current_index
        if event.inaxes == self.ax:
            print(f"Clicked at time: {event.xdata+self.tstarts[idx]:.2f} (obsid: {self.obsids[idx]})")
