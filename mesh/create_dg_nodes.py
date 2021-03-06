import numpy as np

def create_dg_nodes(mesh, ndim):
    """
    Note: can't do curved elements
    
    """
    if ndim == 2:
        plocal = mesh['plocal']
        nplocal = plocal.shape[0]
        numel = mesh['t'].shape[0]

        # Allocate memory for the dgnodes - remember the difference between matlab and python is that python uses C-style ordering where the last index changes fastest. This means that all the dgnodes for one element are indexed as dgnodes[elem_num,:,:] as opposed to dgnodes[:,:,elem_num] in matlab.
        dgnodes = np.zeros((numel, nplocal, 3))

        for i_elem, elem in enumerate(mesh['t']):

            v1 = mesh['p'][elem[1], :] - mesh['p'][elem[0], :]  # v1 = p1->p2
            v2 = mesh['p'][elem[2], :] - mesh['p'][elem[0], :]  # v2 = p1->p3

            crossprod = np.cross(v1, v2)
            v3 = crossprod/np.linalg.norm(crossprod)  # normal vector to the plane containing v1 and v2

            # Affine transformation matrix - transposed version of what we normally think of as the aff. trans. matrix
            # Typically we do Ap=r, but this time we need A^Tp^T=r^T, so we have to transpose A
            A = np.array([v1, v2, v3])

            # Multiply plocal pts by the transformation, add to array
            dgnodes[i_elem, :, :] = plocal@A + mesh['p'][elem[0],:]

    elif ndim == 3:
        plocal = mesh['plocal']
        nplocal = plocal.shape[0]
        numel = mesh['t'].shape[0]

        # Allocate memory for the dgnodes - remember the difference between matlab and python is that python uses C-style ordering where the last index changes fastest. This means that all the dgnodes for one element are indexed as dgnodes[elem_num,:,:] as opposed to dgnodes[:,:,elem_num] in matlab.
        dgnodes = np.zeros((numel, nplocal, 3))

        for i_elem, elem in enumerate(mesh['t']):
            # Define affine transformation

            # Reverting to 0-indexing form 1-indexing of t2f
            v1 = mesh['p'][elem[1], :] - mesh['p'][elem[0], :]  # v1 = p1->p2
            v2 = mesh['p'][elem[2], :] - mesh['p'][elem[0], :]  # v2 = p1->p3
            v3 = mesh['p'][elem[3], :] - mesh['p'][elem[0], :]  # v3 = p1->p4

            # Affine transformation matrix - transposed version of what we normally think of as the aff. trans. matrix
            # Typically we do Ap=r, but this time we need A^Tp^T=r^T, so we have to transpose A
            A = np.array([v1, v2, v3])

            # Multiply plocal pts by the transformation, add to array
            dgnodes[i_elem, :, :] = plocal@A + mesh['p'][elem[0],:]

    return dgnodes

