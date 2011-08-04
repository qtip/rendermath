from tempfile import NamedTemporaryFile
from shutil import copy2 as copy
import os
import os.path
import subprocess
import re
import hashlib

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

class MathSource(object):

    def __init__(self, src, dpi=120, is_display=False):
        self.src = src
        self.dpi = dpi
        self.is_display = is_display
        self.baseline = None

    def formatted_src(self):
        """ Returns src prepared as a LaTeX document """
        # Delimit the LaTeX math input
        if self.is_display:
            tagged_src = r"\[%s\]" % self.src
        else:
            tagged_src = "$%s$" % self.src
        
        document_src = r"""\documentclass[12pt]{article}
        \usepackage{amsmath}
        \usepackage{amsfonts}
        \usepackage{amssymb}
        \usepackage{colordvi}
        \usepackage[active]{preview}
        \begin{document}
        \begin{preview}
        %s
        \end{preview}
        \end{document}""" % tagged_src

        return document_src

    def hashed(self):
        """ Return a hash for use in a filename """
        output = hashlib.md5()
        output.update(self.src)
        output.update(repr(self.dpi))
        output.update(repr(self.is_display))
        return output.hexdigest()


    def matches(self, filename):
        """ Given a filepath, returns None if it isn't an already-compiled
        version of this source, otherwise returns the baseline"""
        filename_pattern = r"%s_(?P<baseline>\d+)_.*" % self.hashed()
        match = re.search(filename_pattern, filename)
        if match:
            return int(match.group('baseline'))
        else:
            return None

    class BaselineNotSetException(Exception): pass

    def generated_filename(self, suffix=".png"):
        """ Return a filename to represent this math source. """
        if not self.baseline:
            raise MathSource.BaselineNotSetException()
        return "%s_%d_%s" % (self.hashed(), self.baseline, suffix)

    def find_in_dir(self, dirpath):
        """ Given a path to a directory return the filename and baseline of an
        already compiled image of this source, or (None, None). """
        for filename in os.listdir(dirpath):
            if os.path.isfile(filename):
                baseline = self.matches(filename)
                if baseline:
                    self.baseline = baseline
                    return os.path.join(dirpath, filename), baseline
        return None, None

def temp_filepath(suffix=''):
    """ Return the name of a temporarily created file. Don't forget to delete it. """
    f = NamedTemporaryFile(suffix=suffix, delete=False)
    f.close()
    return f.name

def render_math(src, path, dpi=120, is_display=False):
    """ Given a string `src`, which is in LaTeX math syntax, write a png to the
    file at the path `path`, and return the path and number of pixels from the bottom
    of the image, to the baseline.

    >>>render_math(r"\sum_{k=1}^n k = \frac{n(n+1)}{2}", ".")
    ('.\\b942cd8866afa64b92b8246adb100eef_7_.png', 7)
    >>>os.path.exists(".\\b942cd8866afa64b92b8246adb100eef_7_.png")
    True
    """

    math_source = MathSource(src, dpi, is_display)

    # Generate a name if a directory is given as the path
    has_generated_name = os.path.isdir(path)
    # Try to find an already generated copy of the file
    if has_generated_name:
        filename, baseline = math_source.find_in_dir(path)
        if filename:
            return filename, baseline
        else:
            image_path = temp_filepath()
    else:
        image_path = path

    # Create the LaTeX source file
    with NamedTemporaryFile(suffix='.tex', delete=False) as tempfile:
        tempfilename = tempfile.name
        tempfile.write(math_source.formatted_src())

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
    dvipng_args += ['-depth'] # report baseline
    dvipng_args += ['-D', str(dpi)] # set dpi
    dvipng_args += ['-T', 'tight'] # make bounding box tight
    dvipng_args += ['-o', os.path.abspath(image_path)] # set output file
    dvipng_args += [tempfilename[:-3] + "dvi"] # set input file
    dvipng_out, dvipng_err = call(dvipng_args)
    baseline = int(re.search("depth=(\d+)", dvipng_out).group(1))
    math_source.baseline = baseline
    # Clean up temp files
    def remove_if_exists(filename):
        try:
            os.remove(filename)
        except OSError:
            pass
    if has_generated_name:
        output_path = os.path.join(path, math_source.generated_filename())
        copy(image_path, output_path)
        remove_if_exists(image_path)
    else:
        output_path = path
    remove_if_exists(tempfilename)
    remove_if_exists(tempfilename[:-3] + "dvi")
    remove_if_exists(tempfilename[:-3] + "aux")
    remove_if_exists(tempfilename[:-3] + "log")
    return output_path, baseline

