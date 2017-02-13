"""Tools
"""
import numpy as np
from argparse import Namespace


class LazyDist(object):
    " lazy loading of scipy distributions "
    def __init__(self, name):
        self.name = name

    def __call__(self, *args, **kwargs):
        import scipy.stats.distributions
        dist = getattr(scipy.stats.distributions, self.name)
        return dist(*args, **kwargs)

norm = LazyDist('norm')
uniform = LazyDist('uniform')
rv_continuous = LazyDist('rv_continuous')
rv_discrete = LazyDist('rv_discrete')
rv_frozen = LazyDist('rv_frozen')


def dist_todict(dist):
    """scipy dist to keywords
    """
    dist_gen = dist.dist
    n = len(dist_gen.shapes.split()) if dist_gen.shapes else 0
    shapes = dist.args[:n]
    kw = {'name': dist_gen.name, 'loc':0, 'scale':1}
    kw.update(dist.kwds)
    if shapes:
        kw['shapes'] = shapes
    assert len(dist.args[n:]) <= 2, dist.name
    if len(dist.args[n:]) >= 1:
        kw['loc'] = dist.args[n]
    if len(dist.args[n:]) == 2:
        kw['scale'] = dist.args[n+1]
    return kw


def dist_fromkw(name, **kwargs):
    """scipy dist to keywords
    """
    import scipy.stats.distributions as mod
    dist = getattr(mod, name)
    args = list(kwargs.pop('shapes', [])) + [kwargs.pop('loc',0), kwargs.pop('scale',1)]
    assert not kwargs, name
    return dist(*args)



def parse_val(s):
    " string to int, float, str "
    try:
        val = int(s)
    except:
        try:
            val = float(s)
        except:
            val = s
    return val

#def parse_keyval(string):
#    name, value = string.split("=")
#    value = parse_val(value)
#    return name, value


def nans(N):
    a = np.empty(N)
    a.fill(np.nan)
    return a


# Sscipy Dist String I/O (useful for command line)
# ======================

# param to string
# ---------------
def dist_to_str(dist):
    """format scipy-dist distribution
    """
    dname=dist.dist.name
    dargs=dist.args

    # hack (shorted notation)
    dname = dname.replace("norm","N")
    if dname == "uniform":
        dname = "U"
        loc, scale = dargs
        dargs = loc, loc+scale  # more natural

    sargs=",".join([str(v) for v in dargs])
    return "{}?{}".format(dname, sargs)


# string to param
# ---------------
def parse_list(string):
    """List of parameters: VALUE[,VALUE,...]
    """
    if not string:
        raise ValueError("empty list")
    return [parse_val(value) for value in string.split(',')]

def parse_range(string):
    """Parameter range: START:STOP:N
    """
    start, stop, n = string.split(':')
    start = float(start)
    stop = float(stop)
    n = int(n)
    return np.linspace(start, stop, n).tolist()

def parse_dist(string):
    """Distribution:

    N?MEAN,STD or U?MIN,MAX or TYPE?ARG1[,ARG2 ...] 
    where TYPE is any scipy.stats distribution with *shp, loc, scale parameters.
    """
    name,spec = string.split('?')
    args = [float(a) for a in spec.split(',')]
    
    # alias for common cases
    if name == "N":
        mean, std = args
        dist = norm(mean, std)

    elif name == "U":
        lo, hi = args  # note: uniform?loc,scale differs !
        dist = uniform(lo, hi-lo) 

    else:
        dist = LazyDist(name)(*args)

    return dist


# 2-D data structure
# ==================


def str_dataframe(pnames, pmatrix, max_rows=1e20, include_index=False, index=None):
    """Pretty-print matrix like in pandas, but using only basic python functions
    """
    #assert isinstance(pmatrix[0][0], float), type(pmatrix[0][0])
    # determine columns width
    col_width_default = 6
    col_fmt = []
    col_width = []
    for p in pnames:
        w = max(col_width_default, len(p))
        col_width.append( w )
        col_fmt.append( "{:>"+str(w)+"}" )

    # also add index !
    if include_index:
        idx_w = len(str(len(pmatrix)-1)) # width of last line index
        idx_fmt = "{:<"+str(idx_w)+"}" # aligned left
        col_fmt.insert(0, idx_fmt)
        pnames = [""]+list(pnames)
        col_width = [idx_w] + col_width

    line_fmt = " ".join(col_fmt)

    header = line_fmt.format(*pnames)

    # format all lines
    lines = []
    for i, pset in enumerate(pmatrix):
        if include_index:
            ix = i if index is None else index[i]
            pset = [ix] + list(pset)
        lines.append(line_fmt.format(*pset))

    n = len(lines)
    # full print
    if n <= max_rows:
        return "\n".join([header]+lines)

    # partial print
    else:
        sep = line_fmt.format(*['.'*min(3,w) for w in col_width])  # separator '...'
        return "\n".join([header]+lines[:max_rows//2]+[sep]+lines[-max_rows//2:])


def read_df(pfile):
    import numpy as np
    header = open(pfile).readline().strip()
    if header.startswith('#'):
        header = header[1:]
    pnames = header.split()
    pvalues = np.loadtxt(pfile, skiprows=1)  
    return pnames, pvalues


class DataFrame(object):
    """DataFrame with names and matrix : Parameters, State variable etc
    """
    def __init__(self, values, names):
        self.values = values
        self.names = names

    @property
    def df(self):
        " convert to pandas dataframe "
        import pandas as pd
        return pd.DataFrame(self.values, columns=self.names)

    @property
    def plot(self):
        " convert to pandas dataframe "
        return self.df.plot

    @classmethod 
    def read(cls, pfile):
        names, values = read_df(pfile)
        return cls(values, names)

    def write(self, pfile):
        with open(pfile, "w") as f:
            f.write(str(self))

    # make it like a pandas DataFrame
    def __getitem__(self, k):
        return self.values[:, self.names.index(k)]

    def keys(self):
        return self.names

    def __str__(self):
        return str_dataframe(self.names, self.values, index=self.index)

    @property
    def size(self):
        return len(self.values)

    def __iter__(self):
        for k in self.names:
            yield k

    @property
    def __len__(self):
        return self.values.shape[1]

    @property
    def shape(self):
        return self.values.shape

    @property
    def index(self):
        return np.arange(self.size)



def _create_dirtree(a,chunksize=2):
    """create a directory tree from a single, long name

    e.g. "12345" --> ["1", "23", "45"]
    """
    b = a[::-1]  # reverse
    i = 0
    l = []
    while i < len(b):
        l.append(b[i:i+chunksize])
        i += chunksize
    return [e[::-1] for e in l[::-1]]


def _short(param):
    '''Output short string representation of parameter and value.
       Used for automatic folder name generation.'''

    # Store the param value as a string
    # Remove the plus sign in front of exponent
    # Remove directory slashes, periods and trailing .nc from string values
    value = "%s" % (param.value)
    if "+" in value: value = value.replace('+','')

    if "/" in value: value = value.replace('/','')
    if ".." in value: value = value.replace('..','')
    if ".nc" in value: value = value.replace('.nc','')

    # Remove all vowels and underscores from parameter name
    name = param.name
    for letter in ['a','e','i','o','u','A','E','I','O','U','_']:
        name = name[0] + name[1:].replace(letter, '')

    return ".".join([name,value])


def autofolder(params):
    '''Given a list of parameters,
       generate an appropriate folder name.
    '''
    parts = []

    for p in params:
        parts.append( _short(p) )

    return '.'.join(parts)
