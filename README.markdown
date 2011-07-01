Install
=======
To install run `python setup.py install` on the command line

To test that it has install correctly, run `python -c "import rendermath"`. If no error appears, then the library has installed correctly.

Dependencies
===========
This library requires that latex and dvipng are installed and on the PATH.

Usage
=====
    >>>from rendermath import render_math
    >>>render_math(r"\sum_{k=1}^n k = \frac{n(n+1)}{2}", "output.png")
    6
    >>>import os
    >>>os.path.exists("output.png")
    True

