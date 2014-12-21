**EQTeXSVG**
============

EQTeXSVG is an extension for [Inkscape][1] used to convert an inline [LaTeX][2] equation into SVG path using Python.


Installation
------------

EQTeXSVG extension is meant to work with Inkscape (at the moment). It is composed of two files:

 - `eqtexsvg.inx`: which is used by Inkscape to describe the extension
 - `eqtexsvg.py`: which is the python script converting inline equation into SVG path

To install it, you need to replace existing files:

 - on Windows, in the following directory: `C:\Program Files\Inkscape\share\extensions\`
 - on Unix, in the following directory: `/usr/share/inkscape/extensions/`

Directories containing your softwares may depend on your configuration.


Needed tools
------------

This extension needs some external tools to work properly:
 - a TeX/LaTeX distribution with `latex` and `dvips` installed (see [MikTeX][3] on Windows or any distribution on Unix)

And depending on which program you prefer:
 - [`dvisvgm`][4] (version 0.8.3 or higher) 
or
 - [`pstoedit`][5]


Using EQTeXSVG
--------------

An example of LATEX equation (see [website][6]):
```
\lim_{n \to \infty}\sum_{k=1}^n \frac{1}{k^2}= \frac{\pi^2}{6}
```

And the SVG result (after some color manipulations inside Inkscape): 
![][7]


[1]: https://www.inkscape.org/
[2]: http://latex-project.org/
[3]: http://miktex.org/
[4]: http://dvisvgm.sourceforge.net/
[5]: http://www.helga-glunz.homepage.t-online.de/pstoedit/
[6]: http://www.julienvitard.eu/en/eqtexsvg_en.html#Use
[7]: http://www.julienvitard.eu/images/photo_eqtexsvg/example.svg