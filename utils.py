#Helper functions for launching FSLeyes locally and some plotting functions
import os, os.path as op, shutil, subprocess

_FSL_OVERLAYS = []   
_FSL_PROC = None     

def loadFSL(fsldir=None):
    fsldir = fsldir or os.environ.get("FSLDIR") or op.expanduser("~/fsl")
    if not op.isdir(fsldir):
        raise RuntimeError(f"FSLDIR not found at: {fsldir}")
    os.environ["FSLDIR"] = fsldir
    os.environ["PATH"]  = os.pathsep.join([op.join(fsldir, "share", "fsl", "bin"),
                                           os.environ.get("PATH", "")])
    os.environ.setdefault("FSLOUTPUTTYPE", "NIFTI_GZ")
    return fsldir

def fsl_reset():
    """Clear the staged overlays/flags."""
    _FSL_OVERLAYS.clear()

def _add_one(arg):
    # flatten lists/tuples so fsl_add(runs) and fsl_add(*runs) both work
    if isinstance(arg, (list, tuple)):
        for a in arg: _add_one(a)
    else:
        _FSL_OVERLAYS.append(str(arg))

def fsl_add(*paths_or_opts):
    """Stage overlays/flags to show next time you call fsl_show()."""
    for a in paths_or_opts:
        _add_one(a)

def fsl_show(kill_old=True):
    """Launch a new FSLeyes window containing all staged overlays/flags."""
    global _FSL_PROC
    loadFSL()
    if not shutil.which("fsleyes"):
        raise RuntimeError("fsleyes not found on PATH; source FSL first.")
    # optionally close previous window so you don’t collect a thousand
    if kill_old and _FSL_PROC is not None:
        try: _FSL_PROC.terminate()
        except Exception: pass
        _FSL_PROC = None
    _FSL_PROC = subprocess.Popen(["fsleyes", *_FSL_OVERLAYS] if _FSL_OVERLAYS else ["fsleyes"])
    return _FSL_PROC

def plot_fd_power(par_path, out_png, thr=0.3, keep=None,
                  break_gaps=True, save_values_path=None, return_fd=False):
    """
    Plot Power FD from an MCFLIRT .par file.
    - If `keep` is provided, FD is computed on the scrubbed series.
    - If `break_gaps` is True, FD is zeroed right after censored gaps.
    """
    import numpy as np, matplotlib.pyplot as plt
    mp = np.loadtxt(par_path) #(T,6): rotX rotY rotZ transX transY transZ
    R  = 50.0 #head radius (mm)
    if keep is None:
        idx = None
        mpk = mp
        xlabel = "Volume"
    else:
        idx = np.asarray(keep, int)
        mpk = mp[idx]
        xlabel = "Volume (scrubbed index)"
    d  = np.diff(mpk, axis=0, prepend=mpk[:1])
    fd = np.abs(d[:, :3]).sum(1)*R + np.abs(d[:, 3:]).sum(1)
    if idx is not None and break_gaps:
        gap = np.r_[False, (idx[1:] - idx[:-1]) > 1]  # first kept frame after any gap
        fd[gap] = 0.0
    if save_values_path:
        np.savetxt(save_values_path, fd, fmt="%.6f")
    plt.figure()
    plt.plot(range(fd.size), fd)
    plt.axhline(thr, ls="--", color="k")
    plt.xlabel(xlabel); plt.ylabel("FD (mm)")
    plt.tight_layout(); plt.savefig(out_png, dpi=150); plt.close()
    if return_fd:
        return fd
