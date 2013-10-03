octopy
======

A python wrapper for the DFT code octopus (http://tddft.org/programs/octopus)

Example
-------
This will calculate the 1-D quantum harmonic oscillator.

    c = octopy.Calculation(octopus='/path/to/your/octopus')
    c.set_params(Dimensions=1,
                 TheoryLevel='independent_particles',
                 Species=[['\'A\'', 0, 'spec_user_defined', 2, '\'0.5*x^2\'']],
                 Coordinates=[['\'A\'', 0]])
    c.set_box_params(L='20', dx='0.1')
    c.run()
    E, T, V, density = c.get_output()

It outputs the total (E), kinetic (T) and potential (V) energy and the density.
