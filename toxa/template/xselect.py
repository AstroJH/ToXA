def filter_scctime(gtis):
    if gtis is None: gtis = []

    script = ""
    for gti in gtis:
        start, end = gti
        script += f"filter time scc \"{start}, {end}\"\n"
    
    return script


def filter_region(regs):
    if regs is None: regs = []

    script = ""
    for reg in regs:
        script += f"filter region {reg}\n"
    
    return script


def extract_spectrum(*, dirpath=".", evtfname, srcreg, bkgreg, phapath, phapath_bkg, gtis):
    script_filter_scctime = filter_scctime(gtis)

    script = f"""xselect << EOF
xsel
read events {evtfname}
{dirpath}
yes

select event "status==b0"
filter grade 0-12
{script_filter_scctime}

filter region {srcreg}
show filter
extract spectrum
save spectrum {phapath}
clear region

filter region {bkgreg}
show filter
extract spectrum
save spectrum {phapath_bkg}
clear region

quit
no
EOF"""
    return script


def extract_lcurve(*, dirpath=".", evtfname, srcreg, bkgreg, binsize, curvepath, curvepath_bkg):
    script = f"""xselect << EOF
xsel
read events {evtfname}
{dirpath}
yes

set binsize {binsize}

filter region {srcreg}
show filter
extract curve
save curve {curvepath}
clear region

filter region {bkgreg}
show filter
extract curve
save curve {curvepath_bkg}
clear region

quit
no
EOF"""
    return script