"""
Distributed components.

Components that are used in multiple places for testing distributed components.
"""
import numpy as np
import openmdao.api as om

from openmdao.utils.mpi import MPI
from openmdao.utils.array_utils import evenly_distrib_idxs


class DistribComp(om.ExplicitComponent):
    """Simple Distributed Component."""

    def initialize(self):
        self.options['distributed'] = True

        self.options.declare('size', types=int, default=1,
                             desc="Size of input and output vectors.")

    def setup(self):
        comm = self.comm
        rank = comm.rank

        size = self.options['size']

        # if comm.size is 2 and size is 15, this results in
        # 8 entries for proc 0 and 7 entries for proc 1
        sizes, offsets = evenly_distrib_idxs(comm.size, size)
        mysize = sizes[rank]
        start = offsets[rank]
        end = start + mysize

        self.add_input('invec', np.ones(mysize, float),
                       src_indices=np.arange(start, end, dtype=int))

        self.add_output('outvec', np.ones(mysize, float))

    def compute(self, inputs, outputs):
        if self.comm.rank == 0:
            outputs['outvec'] = inputs['invec'] * 2.0
        else:
            outputs['outvec'] = inputs['invec'] * -3.0


class Summer(om.ExplicitComponent):
    """Sums an input array."""

    def initialize(self):
        self.options.declare('size', types=int, default=1,
                             desc="Size of input and output vectors.")

    def setup(self):
        size = self.options['size']

        self.add_input('invec', np.ones(size, float))

        self.add_output('out', 0.0)

    def compute(self, inputs, outputs):
        outputs['out'] = np.sum(inputs['invec'])


class DistribCompDerivs(om.ExplicitComponent):
    """Simple Distributed Component with Derivatives."""

    def initialize(self):
        self.options['distributed'] = True

        self.options.declare('size', types=int, default=1,
                             desc="Size of input and output vectors.")

    def setup(self):
        comm = self.comm
        rank = comm.rank

        size = self.options['size']

        # if comm.size is 2 and size is 15, this results in
        # 8 entries for proc 0 and 7 entries for proc 1
        sizes, _ = evenly_distrib_idxs(comm.size, size)
        self.mysize = mysize = sizes[rank]

        # don't set src_indices on the input, just use default behavior
        self.add_input('invec', np.ones(mysize, float))
        self.add_output('outvec', np.ones(mysize, float))

        # declare partial derivatives (diagonal of mysize)
        self.declare_partials('outvec', 'invec', 
                              rows=np.arange(0, mysize),
                              cols=np.arange(0, mysize))

    def compute(self, inputs, outputs):
        if self.comm.rank == 0:
            outputs['outvec'] = inputs['invec'] * 2.0
        else:
            outputs['outvec'] = inputs['invec'] * -3.0

    def compute_partials(self, inputs, J):
        # get mysize from the input vector for this process
        mysize = inputs['invec'].size

        if self.comm.rank == 0:
            J['outvec', 'invec'] = 2.0 * np.ones((mysize,))
        else:
            J['outvec', 'invec'] = -3.0 * np.ones((mysize,))


class SummerDerivs(om.ExplicitComponent):
    """Sums an input array."""

    def initialize(self):
        self.options.declare('size', types=int, default=1,
                             desc="Size of input and output vectors.")

    def setup(self):
        size = self.options['size']

        self.add_input('invec', np.ones(size, float))

        self.add_output('out', 0.0)

        # the derivative is constant
        self.declare_partials('out', 'invec', val=1.)

    def compute(self, inputs, outputs):
        outputs['out'] = np.sum(inputs['invec'])
