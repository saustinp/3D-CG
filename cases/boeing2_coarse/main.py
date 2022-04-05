import sys
import numpy as np
sys.path.insert(0, '../../util')
sys.path.insert(0, '../../mesh')
sys.path.insert(0, '../../master')
sys.path.insert(0, '../../viz')
sys.path.insert(0, '../../CG')
from import_util import load_mat
import viz
from cgmesh import cgmesh
import mkmesh_cube
import mkmaster
import cg_solve
import pickle
import calc_derivative
import logging
import logging.config
import os
import helper
import domain_helper_fcns

########## INITIALIZE LOGGING ##########
logging.config.fileConfig('logging.conf', disable_existing_loggers=False)
# root logger, no __name__ as in submodules further down the hierarchy - this is very important - cost me a lot of time when I passed __name__ to the main logger
logger = logging.getLogger('root')
logger.info('*************************** INITIALIZING SIM ***************************')

# Check whether the specified path exists or not
if not os.path.exists('out/'):
    os.makedirs('out/')
    logger.info('out/ directory not present, created...')


########## TOP LEVEL SIM SETUP ##########
meshfile = 'mesh/' + 'boeing_plane_final_coarse'     # No file extension!
stepfile = 'mesh/boeing_plane_no_landing_gear.STEP'
case_select = 'Ex'
porder = 3
ndim = 3
solver = 'cg'

outdir = 'out/'
vis_filename = 'boeing_plane_Ex_coarse'
build_mesh = True
buildAF = True
use_preconditioning = True
compute_sol = True
call_pv = True
vis_filename = outdir+vis_filename
visorder = 3
viz_labels = {'scalars': {0: 'Potential'}, 'vectors': {0: 'Potential Gradient'}}


fuselage_dia = 3.76     # This is the fuselage of the 737 in m
stabilizers = [20, 26, 51, 85, 72, 95, 34, 38, 87, 108, 97, 116]
nose = [39, 78, 33, 48, 99, 118, 84, 106]
fuselage = [107, 117, 122, 130, 131, 134]
engines = [16, 17, 18, 19, 31, 32, 59, 60, 57, 58, 89, 90]
wings = [121, 119, 101, 103, 79, 82, 41, 45, 27, 30, 6, 11, 2, 3, 132, 137, 126, 136, 123, 124, 109, 114, 88, 93, 56, 69, 35, 36]
body_surfs = stabilizers + nose + fuselage + engines + wings
# body_surfs = fuselage

########## GEOMETRY SETUP ##########
pt_1_fuselage = np.array([8547.42, 1505.00, 5678.37])
pt_2_fuselage = np.array([8547.42, -1505.00, 5678.37])

r_fuselage_msh = np.linalg.norm(pt_1_fuselage-pt_2_fuselage)/2
scale_factor =  fuselage_dia/r_fuselage_msh    # Normalize mesh by the fuselage radius and rescale so that mesh dimensions are in meters

########## BCs ##########
surf_faces = np.arange(137)+1   # Faces are 1-indexed
x_minus_face = 138
x_plus_face = 139
y_minus_face = 140
y_plus_face = 141
z_minus_face = 142
z_plus_face = 143

bdry = (x_minus_face, x_plus_face, y_minus_face, y_plus_face, z_minus_face, z_plus_face)
nbc = {face:0 for face in bdry}

if case_select == 'charged_surface':
    dbc = {face:1 for face in surf_faces}.update(nbc)     # Concatenating two dictionaries together
    nbc = {}
elif case_select == 'Ex':
    dbc = {face:0 for face in surf_faces}
    nbc[x_minus_face] = -1
    nbc[x_plus_face] = 1
elif case_select == 'Ey':
    dbc = {face:0 for face in surf_faces}
    nbc[y_minus_face] = -1
    nbc[y_plus_face] = 1
elif case_select == 'Ez':
    dbc = {face:0 for face in surf_faces}
    nbc[z_minus_face] = -1
    nbc[y_plus_face] = 1

########## PHYSICS PARAM ##########
param = {'kappa': 1, 'c': np.array([0, 0, 0]), 's': 0}

if compute_sol:
    ########## CREATE MESH ##########
    mesh = mkmesh_cube.mkmesh_cube(porder, ndim, meshfile, build_mesh, dbc, nbc, scale_factor, stepfile, body_surfs)

    logger.info('Preparing master data structure...')
    master = mkmaster.mkmaster(mesh, ndim=3, pgauss=2*mesh['porder'])

    # ########## CALCULATE APPROX SOLUTION ##########
    logger.info('Computing approximate solution')
    approx_charge = domain_helper_fcns.approx_sol_charge(mesh)

    with open('approx_charge_vec.npy', 'wb') as file:
        np.save(file, approx_charge)

    logger.info('Visualizing approx solution...')
    viz.visualize(mesh, visorder, viz_labels, vis_filename, call_pv, scalars=approx_charge)

    ########## SOLVE ##########

    sol, x0 = cg_solve.cg_solve(master, mesh, domain_helper_fcns.forcing_zero, param, ndim, outdir, np.squeeze(approx_charge), buildAF, solver)

    ########## SAVE DATA ##########

    # NOTE: in the future uh will need to be reshaped into a nplocal x numvisfields x numel when the derivatives are added
    with open(outdir+'mesh', 'wb') as file:
        pickle.dump(mesh, file)
    with open(outdir+'master', 'wb') as file:
        pickle.dump(master, file)
    with open(outdir+'sol', 'wb') as file:
        pickle.dump(sol, file)
    with open(outdir+'x0', 'wb') as file:
        pickle.dump(x0, file)
    logger.info('Wrote solution to file...')
else:
    ########## LOADING SOLUTION ##########

    logger.info('Reading solution from file...')

    with open(outdir+'mesh', 'rb') as file:
        mesh = pickle.load(file)
    with open(outdir+'master', 'rb') as file:
        master = pickle.load(file)
    with open(outdir+'sol', 'rb') as file:
        sol = pickle.load(file)
    with open(outdir+'x0', 'rb') as file:
        x0 = pickle.load(file)

########## CALC DERIVATIVES ##########
logger.info('Calculating derivatives')

# Reshape into DG high order data structure
sol_reshaped = helper.reshape_field(mesh, sol[:,None], 'to_array', 'scalars')
scalars = np.concatenate((sol[:,None], x0[:,None]), axis=1)

grad = calc_derivative.calc_derivatives(mesh, master, sol_reshaped, ndim)[None,:,:]

# ########## VISUALIZE SOLUTION ##########
viz.visualize(mesh, visorder, viz_labels, vis_filename, call_pv, scalars=scalars, vectors=grad)