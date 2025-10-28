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
