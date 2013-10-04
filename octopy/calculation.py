import os
import shutil
import numpy as np
import subprocess


class Calculation(object):
    keep_folder = False
    # set some standard parameters
    _params = {'CalculationMode': 'gs',
               'OutputHow': 'cube',
               'Output': 'density'}
    _species = []
    _coordinates = []

    def __init__(self, folder=None, octopus=None, **kwargs):
        """ Octopy calculation class

        folder: path to folder where octopus data will be saved
        octopus: path to octopus executable. It will be executed
            in folder path
        Other keyword arguments are passed to set_parameters
        """

        if folder is None:
            self.folder = 'temp_octopy'
        if octopus is None:
            octopus = os.getenv('OCTOPUS', value='octopus')
        self.octopus = octopus

        if not os.path.exists(self.folder):
            os.makedirs(self.folder)

        # touch is_octopy file
        open(os.path.join(self.folder, 'is_octopy'), 'w').close()

        self.add_params(**kwargs)

    def __del__(self):
        """ Deletes folder when object is deleted """

        if not self.keep_folder and os.path.exists(os.path.join(self.folder,
                                                                'is_octopy')):
            shutil.rmtree(self.folder)

    def add_params(self, **kwargs):
        """ Set the parameters for the octopus run.

        A list of all parameters is given in the octopus variable
        reference (see octopus wiki for recent version)

        Block variables are added by providing a list, tuple or
        numpy.ndarray.
        """

        inp = []
        # add new params to self._params
        for key in kwargs:
            self._params[key] = kwargs[key]

        # set output according to dimensions
        if ('Dimensions' in self._params and
                int(self._params['Dimensions']) == 1):
            self._params['OutputHow'] = 'axis_x'
        else:
            self._params['OutputHow'] = 'cube'

        params = dict(self._params)

        # add species and coordinates
        if 'Species' not in params and len(self._species) != 0:
            params['Species'] = self._species
        if 'Coordinates' not in params and len(self._coordinates) != 0:
            params['Coordinates'] = self._coordinates

        # create info for inp file
        for key in params:
            value = params[key]
            if not (isinstance(value, (list, tuple)) or
                    (isinstance(value, np.ndarray) and (len(value) > 1 or
                                                        value.ndim > 1))):
                inp.append(key + ' = ' + str(value))
            else:
                # block
                inp.append('%' + key)
                for line in value:
                    if not (isinstance(line, (list, tuple)) or
                            (isinstance(line, np.ndarray) and
                             (len(line) <= 1 or line.ndim > 1))):
                        inp.append(key + ' = ' + str(line))
                    else:
                        inpa = []
                        for l in line:
                            inpa.append(str(l))
                        inp.append(' ' + ' | '.join(inpa))
                inp.append('%')

        # write inp file
        with open(os.path.join(self.folder, 'inp'), 'w') as f:
            for line in inp:
                f.write(line + '\n')

    def add_box_params(self, L, dx):
        """ Convenience function for cubic grids

        L is the length of the box
        dx is the spacing between to grid points on one axis
        """

        self.add_params(Lsize=float(L)/2., Spacing=dx,
                        BoxShape='parallelepiped')

    def add_species(self, name, mass, type, charge, other):
        """ Add Species

        See Species variable in octopus reference for details.
        other can be list or single value
        """

        if not hasattr(other, '__iter__'):
            other = [other]
        for i in range(len(other)):
            if isinstance(other[i], str):
                other[i] = '\'' + other[i] + '\''
            else:
                other[i] = str(other[i])
        self._species.append(['\'' + name + '\'', mass, type, charge] +
                             other)

    def add_coordinate(self, name, position):
        """ Add Coordinate

        See Coordinates variable in octopus reference for details.
        """

        if not hasattr(position, '__iter__'):
            position = [position]
        self._coordinates.append(['\'' + name + '\''] + position)

    def run(self):
        """ Start the octopus run """
        with open(os.path.join(self.folder, 'output'), 'w') as f:
            subprocess.call(self.octopus, cwd=self.folder, stdout=f,
                            stderr=subprocess.STDOUT, shell=True)

    def get_output(self, read_density=True):
        """ Returns a tuple of output values
        E: Total energy
        T: Kinetic energy
        V: Potential energy
        density: density of the system
        """

        # read static/info
        iterations_set = False
        E_set = False
        T_set = False
        V_set = False
        with open(os.path.join(self.folder, 'static', 'info')) as f:
            for line in f:
                # The following makes sure we only find the values once in the
                # info file. If we find a value a second time we can not be
                # sure we have the correct one.
                if 'SCF converged in ' in line:
                    if iterations_set:
                        raise Exception('iterations_set')
                    iterations = int(line.split('SCF converged in')[1].split(
                        'iterations')[0].strip())
                    iterations_set = True
                if 'SCF *not* converged' in line:
                    if iterations_set:
                        raise Exception('iterations_set2')
                    iterations = 0
                    iterations_set = True
                if ('Total' in line and '=' in line
                        and line.split('=')[0].strip() == 'Total'):
                    if E_set:
                        raise Exception('E_set')
                    E = float(line.split('=')[1].strip())
                    E_set = True
                if 'Kinetic' in line:
                    if T_set:
                        raise Exception('T_set')
                    T = float(line.split('=')[1].strip())
                    T_set = True
                if 'External' in line:
                    if V_set:
                        raise Exception('V_set')
                    V = float(line.split('=')[1].strip())
                    V_set = True
            # Check if all information were found.
            if not (iterations_set and E_set and T_set and V_set):
                raise Exception('did not find all information')

        if iterations == 0:
            print('Warning! SCF *not* converged!')

        # read density cube file if required
        if read_density and 'density' in [x.strip() for x in
                                          self._params['Output'].split('+')]:
            if self._params['OutputHow'] == 'cube':
                with open(os.path.join(self.folder, 'static',
                                       'density.cube')) as f:
                    for _ in range(7):
                        f.readline()
                    density = np.fromfile(f, sep=' ')
                dim = self._params.get('Dimensions', 3)
                G = int(round(len(density) ** (1. / float(dim))))
                density = density.reshape(*([G] * dim))
            else:
                density = np.loadtxt(os.path.join(self.folder, 'static',
                                                  'density.y=0,z=0'),
                                     skiprows=1)[:, 1]
        else:
            density = None

        return E, T, V, density
