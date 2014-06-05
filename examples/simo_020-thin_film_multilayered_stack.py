"""
    simo_020-thin_film_mulilatered_stack.py is a simulation example for EMUstack.

    Copyright (C) 2013  Bjorn Sturmberg, Kokou Dossou, Felix Lawrence

    This program is free software: you can redistribute it and/or modify
    it under the terms of the GNU General Public License as published by
    the Free Software Foundation, either version 3 of the License, or
    (at your option) any later version.

    This program is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
    GNU General Public License for more details.

    You should have received a copy of the GNU General Public License
    along with this program.  If not, see <http://www.gnu.org/licenses/>.
"""

"""
Simulating a stack of homogeneous, dispersive media.
"""

import time
import datetime
import numpy as np
import sys
from multiprocessing import Pool
sys.path.append("../backend/")

import objects
import materials
import plotting
from stack import *

start = time.time()

# Remove results of previous simulations.
plotting.clear_previous('.txt')
plotting.clear_previous('.pdf')
plotting.clear_previous('.log')

################ Simulation parameters ################
# Select the number of CPUs to use in simulation.
num_cores = 2

################ Light parameters #####################
wl_1     = 400
wl_2     = 800
no_wl_1  = 4
wavelengths = np.linspace(wl_1, wl_2, no_wl_1)
light_list  = [objects.Light(wl, max_order_PWs = 1, theta = 0.0, phi = 0.0) for wl in wavelengths]

# The period must be consistent throughout a simulation!
period = 300

# Define each layer of the structure.
superstrate = objects.ThinFilm(period, height_nm = 'semi_inf',
    material = materials.Air)
TF_1 = objects.ThinFilm(period, height_nm = 100, # specify thickness in nm
    material = materials.Material(2.0 + 0.1j)) # give it a constant refractive index
TF_2 = objects.ThinFilm(period, height_nm = 5e6, # EMUstack calc time is independent of height
    material = materials.InP, loss=False) # dispersive refractive index, but with
# the imaginary part of n set to zero for all wavelengths.
TF_3 = objects.ThinFilm(period, height_nm = 52,
    material = materials.Si_a) # by default loss = True
substrate   = objects.ThinFilm(period, height_nm = 'semi_inf',
    material = materials.Si_c, loss=False) # Crystaline silicon
# Note that the semi-inf substrate must be lossess so that EMUstack can distinguish 
# propagating plane waves that carry energy from evanescent waves which do not.

def simulate_stack(light):    
    ################ Evaluate each layer individually ##############
    sim_superstrate = superstrate.calc_modes(light)
    sim_TF_1 = TF_1.calc_modes(light)
    sim_TF_2 = TF_2.calc_modes(light)
    sim_TF_3 = TF_3.calc_modes(light)
    sim_substrate   = substrate.calc_modes(light)
    ################ Evaluate stacked structure ##############
    """ Now when defining full structure order is critical and
    stack MUST be ordered from bottom to top!
    """
# We can now stack these layers of finite thickness however we wish.
    stack = Stack((sim_substrate, sim_TF_1, sim_TF_3, sim_TF_2, sim_TF_1, sim_superstrate))
    stack.calc_scat(pol = 'TM')

    return stack

# Run wavelengths in parallel across num_cores CPUs using multiprocessing package.
pool = Pool(num_cores)
stacks_list = pool.map(simulate_stack, light_list)
# Save full simo data to .npz file for safe keeping!
simotime = str(time.strftime("%Y%m%d%H%M%S", time.localtime()))
np.savez('Simo_results'+simotime, stacks_list=stacks_list)

######################## Post Processing ########################
# We will now see the absorption in each individual layer as well as of the stack.
plotting.t_r_a_plots(stacks_list)

######################## Wrapping up ########################
print '\n*******************************************'
# Calculate and record the (real) time taken for simulation,
elapsed = (time.time() - start)
hms     = str(datetime.timedelta(seconds=elapsed))
hms_string = 'Total time for simulation was \n \
    %(hms)s (%(elapsed)12.3f seconds)'% {
            'hms'       : hms,
            'elapsed'   : elapsed, }
print hms_string
print '*******************************************'
print ''

# and store this info.
python_log = open("python_log.log", "w")
python_log.write(hms_string)
python_log.close()