import warnings
import numpy as np
import numpy.random as random
from scipy.interpolate import interp1d
from scipy.optimize import brentq
from ..relations import Relation
from .. import DISDIR

import colossus
cosmo = colossus.cosmology.cosmology.setCosmology('planck18')



class SMHM(Relation):

    name = 'SMHM'
    
    def __init__(self, scatter=True):
        self.parameters = {}
        self.sample_scatter = scatter

    @classmethod
    def central_value(cls, mass, z=0.):
        raise NotImplementedError('This is an abstract class.')

    @staticmethod
    def scatter():
        """Lognormal scatter"""
        raise NotImplementedError('This is an abstract class.')

    def __call__(self, mass, z=0.):
        median = self.central_value(mass, z=z)
        if self.sample_scatter:
            return median * 10**random.normal(loc=0,scale=self.scatter(),size=1 if np.array(mass).size==1 else len(mass))
        else:
            return median



############################################################


class Moster13(SMHM):
    """Moster+ 2013's redshift-dependent SMHM relation"""

    name = 'Moster13'

    @classmethod
    def central_value(cls, mass, z=0.):

        mass = np.array(mass)
        
        M10_M13 = 11.590  # +- 0.236
        M11_M13 =  1.195  # +- 0.353
        N10_M13 =  0.0351 # +- 0.0058
        N11_M13 = -0.0247 # +- 0.0069
        b10_M13 =  1.376  # +- 0.153
        b11_M13 = -0.826  # +- 0.225
        g10_M13 =  0.608  # +- 0.608
        g11_M13 =  0.329  # +- 0.173

        M1    = 10**( M10_M13 + M11_M13 * z/(z+1) )
        N     = N10_M13 + N11_M13 * z/(z+1)
        beta  = b10_M13 + b11_M13 * z/(z+1)
        gamma = g10_M13 + g11_M13 * z/(z+1)
        return 2 * N * mass / ( (mass/M1)**-beta + (mass/M1)**gamma )

    @staticmethod
    def scatter():
        return 0.15



class Dooley17(SMHM):
    """Dooley+ 2017's tuned-bent z=0 relation."""

    name = 'Dooley17'

    # load data
    mhD17,msD17 = np.loadtxt(DISDIR+'/data/smhm/dooley.dat' ,unpack=True)
    mstarD17 = interp1d(np.log(mhD17),np.log(msD17),kind='linear',fill_value='extrapolate',bounds_error=False)
    
    @classmethod
    def central_value(cls, mass, z=0.):
        if z != 0: warnings.warn('Dooley+ 2017 SMHM has no support for z>0, using z=0 relation!')            
        return np.exp(cls.mstarD17(np.log(mass)))

    @staticmethod
    def scatter():
        warnings.warn('scatter in Dooley+ 2017 SMHM relation not quantified, using Moster+ 2013 scatter!')
        return 0.15



class Brook14(SMHM):
    """Brook+ 2014's z=0 relation."""

    name = 'Brook14'

    # load data
    mh350B14,msB14 = np.loadtxt(DISDIR+'/data/smhm/brook.dat' ,unpack=True)
    h0 = cosmo.Hz(0)/100.  # convert from 350c units to 200c units, assuming NFW
    c350 = colossus.halo.concentration.concentration(mh350B14/h0, '350c', 0, model='diemer19')
    m200_div_h, r200_div_h, c200 = colossus.halo.mass_defs.changeMassDefinition(mh350B14/h0, c350, 0, '350c', '200c')
    mh200B14,r200 = m200_div_h * h0, r200_div_h * h0
    mstarB14 = interp1d(np.log(mh200B14),np.log(msB14),kind='linear',fill_value='extrapolate',bounds_error=False)    

    @classmethod
    def central_value(cls, mass, z=0.):
        if z !=0:  warnings.warn('Brook+ 2014 SMHM has no support for z>0, using z=0 relation!')
        return np.exp(cls.mstarB14(np.log(mass)))

    @staticmethod
    def scatter():
        warnings.warn('scatter in Brook+ 2014 SMHM relation not quantified, using Moster+ 2013 scatter!')
        return 0.15



class Behroozi13(SMHM):
    """
    Behroozi+ 2013's z=0 relation.
    Redshift-dependent relation exists, but not implemented here.
    """
    
    name = 'Behroozi13'

    # load data
    mhB13,msB13 = np.loadtxt(DISDIR+'/data/smhm/behroozi.dat' ,unpack=True)
    mstarB13 = interp1d(np.log(mhB13),np.log(msB13),kind='linear',fill_value='extrapolate',bounds_error=False)

    @classmethod
    def central_value(cls, mass, z=0.):
        if z != 0: warnings.warn('Behroozi+ 2013 SMHM relation for z>0 not implemented, using z=0 relation!')            
        return np.exp(cls.mstarB13(np.log(mass)))

    @staticmethod
    def scatter():
        warnings.warn('scatter in Behroozi+ 2013 SMHM relation not quantified, using Moster+ 2013 scatter!')
        return 0.15


    
############################################################
# Wrapper for all SMHM relations

def SMHM(mhalo, model='m13', z=0., scatter=False):

    """
    Stellar-mass--halo-mass relations.  Given a halo mass, returns
    the stellar mass of the halo based on the given relation.
    Assumes all masses are in solar masses.

    Notes on Inputs:

    mhalo = halo mass(es) to compute stellar masses for, in solar masses
    
    model = the SMHM relation to use.  Accepted values include:

        'm13' = Moster+ 2013 relation
        'd17' = Dooley+ 2017 relation
        'b14' = Brook+ 2014 relation
        'b13' = Behroozi+ 2013 relation

        By default, assumes the 'm13' relation.

    z = the redshift at which to compute the SMHM relation.  By default,
        assumes z=0.  Note that not all SMHM relations have support for
        z > 0.  For these relations, a warning will print, and the z=0
        relation will be used.

    scatter = whether or not to sample the scatter in the SMHM relation.
        If False, provides the stellar mass predicted by the median
        relation.  Note that the scatter has not been measured for some
        SMHM relations, in which case a lognormal scatter of 0.15 dex is
        adopted (based on Moster+ 2013).        
    """
    
    if   model == 'm13': relation = Moster13(scatter=scatter)
    elif model == 'd17': relation = Dooley17(scatter=scatter)
    elif model == 'b14': relation = Brook14(scatter=scatter)
    elif model == 'b13': relation = Behroozi13(scatter=scatter)
    else:
        raise ValueError("No support for SMHM relation "+model+'!')

    return relation(mhalo, z=z)
