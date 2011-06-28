from tempfile import NamedTemporaryFile
import os
import os.path
import subprocess

def call(*args, **kwargs):
    """Using the parameters to subprocess.Popen.__init__, return
    a double of the stdout and the stderr of the call.
    
    >>>call(['echo', 'hello world'])
    ('hello world\n', '')
    """
    outfilename = None
    errfilename = None
    with NamedTemporaryFile(delete=False) as outfile:
        with NamedTemporaryFile(delete=False) as errfile:
            outfilename = outfile.name
            errfilename = errfile.name
            proc = subprocess.Popen(*args, stdout=outfile, stderr=errfile, **kwargs)
            proc.wait()
    out = None
    err = None
    with open(outfilename, 'r+b') as outfile:
        out = outfile.read()
    os.remove(outfilename)
    with open(errfilename, 'r+b') as errfile:
        err = errfile.read()
    os.remove(errfilename)
    return out, err

def render_math(src, output, dpi=120, is_display=False):
    """ Given a string `src`, which is in LaTeX math syntax, write a png to the
    file at the path `output`.

    >>>render_math(r"\sum_{k=1}^n k = \frac{n(n+1)}{2}", "output.png")
    >>>os.path.exists("output.png")
    True
    """
    # Delimit the LaTeX math input
    if is_display:
        tagged_src = r"\[%s\]" % src
    else:
        tagged_src = "$%s$" % src
    # Create the LaTeX source file
    with NamedTemporaryFile(suffix='.tex', delete=False) as tempfile:
        tempfilename = tempfile.name
        tempfile.write(r"""\documentclass[12pt]{article}
        \pagestyle{empty}
        \begin{document}
        %s
        \end{document}""" % tagged_src)

    tempfilepath = os.path.dirname(tempfilename)
    # Run latex
    latex_args = ['latex']
    latex_args += ['-interaction=nonstopmode'] # no interaction with console
    latex_args += [tempfilename] # set input file
    latex_out, latex_err = call(latex_args, cwd = tempfilepath)
    if latex_err:
        raise RuntimeError(latex_err)
    # Run dvipng
    dvipng_args = ['dvipng']
    dvipng_args += ['-D', str(dpi)] # set dpi
    dvipng_args += ['-T', 'tight'] # make bounding box tight
    dvipng_args += ['-o', os.path.abspath(output)] # set output file
    dvipng_args += [tempfilename[:-3] + "dvi"] # set input file
    dvipng_out, dvipng_err = call(dvipng_args)
    # Clean up temp files
    def remove_if_exists(filename):
        try:
            os.remove(filename)
        except OSError:
            pass
    remove_if_exists(tempfilename)
    remove_if_exists(tempfilename[:-3] + "dvi")
    remove_if_exists(tempfilename[:-3] + "aux")
    remove_if_exists(tempfilename[:-3] + "log")

