#!/usr/bin/env python2
# -*- coding: utf-8 -*-
"""
eqtexsvg.py
An extension to convert LaTeX equation string into SVG path

This extension need, to work properly:
 - a TeX/LaTeX distribution (MikTeX ...) with latex and dvips
Depending on which program you prefer:
 - dvisvgm (http://dvisvgm.sourceforge.net/) version 0.8.3 or higher
 or
 - pstoedit (http://www.helga-glunz.homepage.t-online.de/pstoedit/)

Recent version can be downloaded via :
 http://www.julienvitard.eu/

Copyright (C) 2006 - 2011 Julien Vitard, eqtexsvg@gmail.com
 * 2011-05-17: changes pstoedit option -quiet
 * 2011-05-16: inx file modification
 * 2011-05-15: uname replacement by platform
 * 2011-03-14: debug info option
 * 2011-03-15: custom packages
 * 2011-03-16: support of dvisvgm and dvips/pstoedit process

This program is free software; you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation; either version 2 of the License, or
(at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with this program; if not, write to the Free Software
Foundation, Inc., 59 Temple Place, Suite 330, Boston, MA  02111-1307  USA
"""

import inkex
import os
import sys
import tempfile
from subprocess import Popen, PIPE
from StringIO import StringIO
import platform
import logging

LOG = os.path.join(os.path.expanduser('~'), 'eqtexsvg.log')
logging.basicConfig(filename=LOG,
                    level=logging.DEBUG,
                    filemode='w',
                    datefmt='%d/%m/%Y %H:%M:%S',
                    format="%(asctime)s: %(message)s")


def exec_cmd(cmd_line=None, debug=True):
    """Launch given command line (and report in log if debug)"""

    clean = lambda x: '\n'.join([l for l in x.split('\n') if l != ""])

    process = Popen(cmd_line, shell=True, stdin=PIPE, stdout=PIPE, stderr=PIPE)

    (std_out, std_err) = process.communicate()
    std_out = clean(std_out)
    std_err = clean(std_err)

    if debug:
        logging.debug(cmd_line)
        logging.debug('returncode: ' + str(process.returncode))
        logging.debug('stderr:\n' + std_err)
        logging.debug('stdout:\n' + std_out)

    return (process.returncode, std_out, std_err)


class Equation:
    """Current LaTeX Equation"""

    def __init__(self, param=None):

        param = param or {}
        self.document = None
        self.formula = None
        self.temp_dir = None
        self.header = None
        self.debug = False

        if 'debug' in param:
            self.debug = param['debug']

        inkscape_version = exec_cmd('inkscape -V', False)[1]

        if self.debug:
            logging.debug(inkscape_version)
            # get Python informations system, release and machine informations

            logging.debug("Python %s\nCompiler: %s\nBuild   : %s" % (
                platform.python_version(),
                platform.python_compiler(),
                ' '.join(platform.python_build())))
            logging.debug("Platform: %s" % (platform.platform()))
            logging.debug("Current Working Directory: %s" % (os.getcwd()))
            logging.debug("Current Extension Directory: %s" % (
                os.path.abspath(__file__)))
        try:
            self.temp_dir = tempfile.mkdtemp('', 'inkscape-')
            if self.debug:
                logging.debug(self.temp_dir)
        except:
            if self.debug:
                logging.debug('Temporary directory cannot be created')
            sys.exit('Temporary directory cannot be created')

        if 'document' in param:
            self.document = param['document']

        if 'formula' in param:
            self.formula = param['formula']
            if self.debug:
                logging.debug(self.formula)
        else:
            if self.debug:
                logging.debug('No formula detected')
            sys.exit('Without formula, no equation will be generated')

        if 'packages' in param:
            self.pkgstring = param['packages']
        else:
            self.pkgstring = ""

        self.file_ext = ['.tex', '.aux', '.log', '.dvi', '.out', '.err', '.ps']

        self.file = 'eq'
        self.svg = None
        self.file_tex = os.path.join(self.temp_dir, self.file + '.tex')
        self.file_ps = os.path.join(self.temp_dir, self.file + '.ps')
        self.file_dvi = os.path.join(self.temp_dir, self.file + '.dvi')
        self.file_svg = os.path.join(self.temp_dir, self.file + '.svg')
        self.file_out = os.path.join(self.temp_dir, self.file + '.out')
        self.file_err = os.path.join(self.temp_dir, self.file + '.err')

        self.latex = False
        self.dvips = False
        self.pstoedit = False
        self.dvisvgm = False
        self.process = True

    def path_programs(self, cmd_line=None, code=True):
        """Try to launch given command line with pass return code"""

        # convention ==0 : True, !=0 : False
        # 'latex --version' ==0
        # 'dvips -v'  !=0
        # 'pstoedit -v' !=0
        # 'dvisvgm -V' ==0

        program_name = cmd_line.split()[0]

        try:
            retcode = exec_cmd(cmd_line, self.debug)[0]

            if ((retcode == 0) if code else retcode):
                exec('self.' + program_name + ' = True')
                if self.debug:
                    logging.debug(program_name + " OK")
            else:
                exec('self.' + program_name + ' = False')
                if self.debug:
                    logging.debug(program_name + " not OK")

        except OSError, err:
            if self.debug:
                logging.debug(program_name + " failed: " + err)
            sys.stderr.write(program_name + " failed:" + err)
            sys.exit(1)

    def parse_pkgs(self):
        """Add custom packages to TeX source"""

        header = ""
        if self.pkgstring != "":
            pkglist = self.pkgstring.replace(" ", "").split(",")
            for pkg in pkglist:
                header += "\\usepackage{%s}\n" % pkg
            self.header = header
            if self.debug:
                logging.debug('packages:\n' + self.header)
        else:
            self.header = ""
            if self.debug:
                logging.debug('No package')

    def generate_tex(self):
        """Generate the LaTeX Equation file"""

        self.parse_pkgs()

        texstring = "%% processed with eqtexsvg.py\n"
        texstring += "\\documentclass{article}\n"
        texstring += "\\usepackage{amsmath}\n"
        texstring += "\\usepackage{amssymb}\n"
        texstring += "\\usepackage{amsfonts}\n"
        texstring += self.header
        texstring += "\\thispagestyle{empty}\n"
        texstring += "\\begin{document}\n"
        # Todo1: Check the argument carefully, especially Math delimiters
        #  delimiters : ('$','$')('$$','$$')('\(','\)')('\[','\]')
        #               ('\begin{equation*}', '\end{equation*}')
        #               ('\begin{equation}', '\end{equation}')
        #               ('\begin{math}', '\end{math}')
        #               ('\begin{displaymath}', '\end{displaymath}')
        #               ...
        texstring += self.formula
        texstring += "\n\\end{document}\n"

        if self.debug:
            logging.debug('\n' + texstring)

        try:
            tex = open(self.file_tex, 'w')
            tex.write(texstring)
            tex.close()
            if self.debug:
                logging.debug('TEX file generated')
        except IOError:
            if self.debug:
                logging.debug('TEX file not generated')

    def generate_dvi(self):
        """Generate the DVI Equation file"""

        cmd_line = 'latex '
        cmd_line += '-output-directory="%s"' % (self.temp_dir)
        cmd_line += ' -halt-on-error '
        cmd_line += "%s " % (self.file_tex)

        retcode = exec_cmd(cmd_line, self.debug) [0]

        if retcode:
            if self.debug:
                logging.debug('DVI file not generated with latex')
            sys.exit('Problem to generate DVI file')
        else:
            if self.debug:
                logging.debug('DVI file generated with latex')

    def generate_svg(self):
        """Generate the SVG Equation string/file"""

        if self.process:
            # Use dvisvgm
            cmd_line = 'dvisvgm '
            cmd_line += '-v0 '         # set verbosity level to 0
            cmd_line += '-a '          # trace all glyphs of bitmap fonts
            cmd_line += '-n '          # draw glyphs by using path elements
            cmd_line += '-s '          # write SVG output to stdout
            cmd_line += '"%s"' % (self.file_dvi)   # Input file

            retcode, std_out, std_err = exec_cmd(cmd_line, self.debug)
            # Get SVG from dvisvgm output
            self.svg = std_out

            if not retcode:
                if self.debug:
                    logging.debug('SVG file generated with dvisvgm')
            else:
                if self.debug:
                    logging.debug('SVG file not generated with dvisvgm')
                sys.exit('SVG file not generated with dvisvgm')
        else:
            # Use dvips to produce PS file
            cmd_line = 'dvips '
            cmd_line += '-q '          # Run quietly
            cmd_line += '-f '          # Run as filter
            cmd_line += '-E '          # Try to create EPSF
            cmd_line += '-D 600 '      # Resolution
#              cmd_line += '-y 1000 '     # Multiply by dvi magnification
            cmd_line += '-o "%s" ' % (self.file_ps)   # Output file
            cmd_line += '"%s"' % (self.file_dvi)  # Input file

            retcode, std_out, std_err = exec_cmd(cmd_line, self.debug)

            if not retcode:
                if self.debug:
                    logging.debug('PS file generated with dvips')
            else:
                if self.debug:
                    logging.debug('PS file not generated with dvips')
                sys.exit('PS file not generated with dvips')

            # Use pstoedit to produce SVG file
            cmd_line = 'pstoedit '
            cmd_line += '-f plot-svg '  # svg via GNU libplot
            cmd_line += '-dt '          # convert text to polygons
            cmd_line += '-ssp '         # simulate subpaths
#             cmd_line += '-quiet '      # quiet mode
            cmd_line += '"%s" ' % (self.file_ps)     # Input file

            retcode, std_out, std_err = exec_cmd(cmd_line, self.debug)
            # Get SVG from pstoedit output
            self.svg = std_out

            if not retcode:
                if self.debug:
                    logging.debug('SVG file generated with pstoedit')
            else:
                if self.debug:
                    logging.debug('SVG file not generated with pstoedit')
                sys.exit('SVG file not generated with pstoedit')

    def import_svg(self):
        """Import the SVG Equation file into Current layer"""

        svg_uri = inkex.NSS['svg']
        xlink_uri = inkex.NSS['xlink']

        if self.debug:
            logging.debug('import_svg():\n' + self.svg + '\n')
        try:
            # parsing self.svg from file:
            tree = inkex.etree.parse(StringIO(self.svg))
            eq_tree = tree.getroot()
            if self.debug:
                logging.debug('SVG file imported from parse')
        except Exception:
            if self.debug:
                logging.debug('SVG file not imported')
            sys.exit('Problem to import svg string/file')

        # Collect document ids
        doc_ids = {}
        doc_id_nodes = self.document.xpath('//@id')

        for id_nodes in doc_id_nodes:
            doc_ids[id_nodes] = 1

        name = 'equation_00'

        # Make sure that the id/name is unique
        index = 0
        while name in doc_ids:
            name = 'equation_%02d' % index
            index = index + 1

        # Create new group node containing the equation
        eqn = inkex.etree.Element('{%s}%s' % (svg_uri, 'g'))
        eqn.set('id', name)
        eqn.set('style', 'fill: black;')
        eqn.set('title', str(self.formula))

        if not self.process:
            # Apply transform to pstoedit result
            doc_width = inkex.unittouu(self.document.getroot().get('width'))
            doc_height = inkex.unittouu(self.document.getroot().get('height'))
            doc_sizeH = min(doc_width, doc_height)
            doc_sizeW = max(doc_width, doc_height)

            matrix_transform = 'matrix(1,0,0,-1,%f,%f)' % (-doc_sizeH * 0.2,
                                                           doc_sizeW * 0.65)
            if self.debug:
                logging.debug('Dimensions:\n'
                              + '  W:' + str(doc_width)
                              + '  H:' + str(doc_height)
                              + ' sH:' + str(doc_sizeH)
                              + ' sW:' + str(doc_sizeW))
                logging.debug('Applying matrix: '+matrix_transform)
            eqn.set('transform', matrix_transform)

        dic = {}
        counter = 0

        # Get the Ids from <defs/>
        # And make unique Ids from name and counter
        for elt in eq_tree:
            if elt.tag == ('{%s}%s' % (svg_uri, 'defs')):
                for subelt in elt:
                    dic[subelt.get('id')] = "%s_%02d" % (name, counter)
                    counter += 1

        # Build new equation nodes
        for elt in eq_tree:
            eqn_elt = inkex.etree.SubElement(eqn, elt.tag)
            if 'id' in elt.keys():
                eqn_elt.set('id', name + '_' + elt.tag.split('}')[-1])
            for subelt in elt:
                eqn_subelt = inkex.etree.SubElement(eqn_elt, subelt.tag)
                for key in subelt.keys():
                    eqn_subelt.set(key, subelt.attrib[key])
                if 'id' in subelt.attrib:
                    eqn_subelt.set('id', dic[subelt.get('id')])
                xlink = '{%s}%s' % (xlink_uri, 'href')
                if xlink in subelt.attrib:
                    eqn_subelt.set(xlink,
                                   '#' + dic[subelt.get(xlink).split("#")[-1]])

        self.svg = eqn

    def clean(self):
        """Clean all necessary file"""

        for ext in self.file_ext:
            try:
                os.unlink(os.path.join(self.temp_dir, self.file + ext))
                if self.debug:
                    logging.debug(self.file + ext + ' file deleted')
            except OSError:
                if self.debug:
                    logging.debug(self.file + ext + ' file not deleted')
        try:
            os.rmdir(self.temp_dir)
            if self.debug:
                logging.debug(self.temp_dir + ' is removed')
        except OSError:
            if self.debug:
                logging.debug(self.temp_dir + 'cannot be removed')

    def generate(self):
        """Generate SVG from LaTeX equation file"""

        self.path_programs('latex --version', True)
        self.path_programs('dvips -v', True)
        self.path_programs('pstoedit -v', False)
        self.path_programs('dvisvgm -V', True)

        self.generate_tex()
        self.generate_dvi()

        if self.latex and self.dvisvgm:  # and False:
            self.process = True
            if self.debug:
                logging.debug('latex and dvisvgm process in use')
        elif self.latex and self.dvips and self.pstoedit:
            self.process = False
            if self.debug:
                logging.debug('latex, dvips and pstoedit process in use')
        else:
            if self.debug:
                logging.debug('No process in use!')
            sys.exit('No process in use!')

        self.generate_svg()
        self.import_svg()
        self.clean()

        return self.svg


class InsertEquation(inkex.Effect):
    """Insert LaTeX Equation into the current Inscape instance"""

    def __init__(self):

        formula = '\(\displaystyle\lim_{n\\to \infty}\sum_{k=1}^n\\frac{1}{k^2}' \
                  + '=\\frac{\pi^2}{6}\)'

        inkex.Effect.__init__(self)
        self.OptionParser.add_option(
            '-f', '--formule', action='store', type='string',
            dest='formula', help='LaTeX formula', default=formula,)
        self.OptionParser.add_option(
            "-p", "--packages", action="store", type="string",
            dest="packages", help="Additional packages", default="",)
        self.OptionParser.add_option(
            "-d", "--debug", action="store", type="inkbool",
            dest="debug", help="Debug information", default=False,)

    def effect(self):
        """Generate inline Equation"""
        equation = Equation({
            'formula':  self.options.formula,
            'document': self.document,
            'packages': self.options.packages,
            'debug':    self.options.debug,
        })

        debug = self.options.debug

        current_eq = equation.generate()

        if current_eq != None:
            self.current_layer.append(current_eq)
            if debug:
                logging.debug('Equation added to current layer')
        else:
            if debug:
                logging.debug('Equation not generated')
            inkex.debug('No Equation was generated\n')


if __name__ == "__main__":
    EFFECT = InsertEquation()
    EFFECT.affect()
