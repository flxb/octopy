octopy
======

A simple python wrapper for the DFT code octopus (http://tddft.org/programs/octopus)


Example: 1-D Harmonic Oscillator
--------------------------------

This will calculate the 1-D quantum harmonic oscillator.

    c = octopy.Calculation(octopus='/path/to/your/octopus')
    c.add_params(Dimensions=1, TheoryLevel='independent_particles')
    potential = '0.5*x^2'
    c.add_species(name='A', mass=0, type='spec_user_defined', charge=2, other=potential)
    c.add_coordinate(name='A', position=0)
    c.add_box_params(L='20', dx='0.1')
    c.run()
    E, T, V, density = c.get_output()

It outputs the total (E), kinetic (T) and potential (V) energy and the density.

Example: Hydrogen Atom
----------------------

This will do a ground-state calculation for 3-D Hydrogen.

    c = octopy.Calculation(octopus='/path/to/your/octopus')
    c.add_coordinate(name='H', position=[0, 0, 0])
    c.run()
    E, T, V, density = c.get_output()
