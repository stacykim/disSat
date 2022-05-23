import numpy as np
import numpy.random as random
from ..relations import Relation


class GalaxySize(Relation):

    def __init__(self, scatter=True):
        self.parameters = {}
        self.sample_scatter = scatter

    @classmethod
    def central_value(cls, mstar):
        raise NotImplementedError('This is an abstract class.')

    @staticmethod
    def scatter(cls):
        """Lognormal scatter"""
        raise NotImplementedError('This is an abstract class.')

    def __call__(self, mstar):
        median = self.central_value(mstar)
        if self.sample_scatter:
            return median * 10**random.normal(loc=0,scale=self.scatter(),size=len(mstar))
        else:
            return median



############################################################

class Read17(GalaxySize):
    """
    Fit to isolated dwarfs from Read+ 2017 and McConnachie+ 2012,
    taking out repeats from the latter, and no Leo T.
    """

    name = 'Read17'

    @classmethod
    def central_value(cls, mstar):
        return 10**(0.268*np.log10(mstar)-2.11)

    @staticmethod
    def scatter():
        return 0.234

    
