#Helper functions for launching FSLeyes locally and some plotting functions
import os, os.path as op, shutil, subprocess, sys

def loadFSL(fsldir=None):
    fsldir = fsldir or os.environ.get("FSLDIR") or op.expanduser("~/fsl")
    if not op.isdir(fsldir):
        raise RuntimeError(f"FSLDIR not found at: {fsldir}")
    os.environ["FSLDIR"] = fsldir
    os.environ["PATH"]  = os.pathsep.join([op.join(fsldir, "share", "fsl", "bin"),
                                           os.environ.get("PATH", "")])
    os.environ.setdefault("FSLOUTPUTTYPE", "NIFTI_GZ")
    return fsldir

def launch_fsleyes(image=None, extra_args=None):
    import shutil, subprocess, os.path as op
    loadFSL()  # ensure FSLDIR/bin is on PATH

    args = ["fsleyes"]
    if extra_args:
        args += [str(a) for a in extra_args]
    if image is not None:
        # (optional) only append if it exists; drop this check if you prefer
        if op.exists(str(image)):
            args.append(str(image))
        else:
            args.append(str(image)) 

    if not shutil.which("fsleyes"):
        raise RuntimeError("fsleyes not found on PATH. Install FSL/FSLeyes or source FSL first.")

    if "--cliserver" in args:
        subprocess.Popen(args)      
    else:
        subprocess.run(args, check=True)  
    return 0

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
