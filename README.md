# runner

Sample parameters, run model ensemble over multiple processors

Requirements
============
- Python 2.7 and 3

Python libraries:
- numpy (tested with 1.11)
- scipy (tested with 0.16 and 0.18)
- tabulate

These libraries can be installed with `pip`, e.g., `pip install tabulate`. 

Install
=======

1. Install `runner` to your Python installation via `pip`:

```
pip install https://github.com/cxesmc/runner/archive/refs/heads/master.zip
```

Now check that system command `job` is available by running `job -h`. 

Usage
=====
Use command-line help:

- [job -h](doc/job.txt)
- [job product -h](doc/product.txt)
- [job sample -h](doc/sample.txt)
- [job resample -h](doc/resample.txt)
- [job run -h](doc/run.txt)
- [job analyze -h](doc/analyze.txt)


Examples
========

Parameter sampling
------------------

Factorial combination of parameters:

    job product a=2,3,4 b=0,1
    
     a      b
     2      0
     2      1
     3      0
     3      1
     4      0
     4      1

Monte-carlo sampling:

    job sample a=U?0,1 b=N?0,1 --size 10 --seed 4

         a      b
    0.425298236238 0.988953805595
    0.904416005793 2.62482283016
    0.68629932356 0.705445219934
    0.397627445478 -0.766770633921
    0.577938292179 -0.522609467132
    0.0967029839014 -0.14215407458
    0.71638422414 0.0495725958965
    0.26977288246 0.519632323554
    0.197268435996 -1.60068615198
    0.800898609767 -0.948326628599

The above command draws 10 samples from "a" as uniform distribution between 0 
and 1 and "b" as normal distribution of mean 0 and standard deviation 1. 
The seed parameter sets the random state, to make the sampling reproducible.
Sampling method defaults to Latin Hypercube Sampling, built on the pyDOE 
package (copied in runner to reduce external dependencies).


Run model ensemble
------------------

The canonical form of `job run` is:

    job run [OPTIONS] -- EXECUTABLE [OPTIONS]
    job run [OPTIONS] -m CUSTOM

where `EXECUTABLE` is your model executable or a command, followed by its
arguments, and `CUSTOM` indicates a custom model interface. 
Note the `--` that separates `job run` arguments `OPTIONS` from the
executable.  When there is no ambiguity in the command-line arguments (as seen
by python's argparse) it may be dropped. `job run` options determine in which
manner to run the model, which parameter values to vary (the ensemble), and how
to communicate these parameter values to the model.  The most straightforward
way it to use formattable command-line argument. For instance using canonical
UNIX command `echo` as executable:

    job run -p a=2,3,4 b=0,1 -o out -- echo --a {a} --b {b} --out {}

The standard output is written in log files under `out/RUNID`:

    cat out/*/log.out

    --a 2 --b 0 --out out/0
    --a 2 --b 1 --out out/1
    --a 3 --b 0 --out out/2
    --a 3 --b 1 --out out/3
    --a 4 --b 0 --out out/4
    --a 4 --b 1 --out out/5

The command above runs an ensemble of 6 model versions, by calling 
`echo --a {a} --b {b} --out {}`  where `{a}`, `{b}` and `{}` 
are formatted using runtime with
parameter and run directory values, as displayed in the output above.
Parameter ensembles generated by `job sample` can also be provided as input via
`-i/--params-file` option instead of `-p/--params`. 
The `job run` parameter `-o/--out-dir` indicates experiment directory, under
which individual ensemble member run directories `{}` will be created. There
are a number of options to determine how this should be done (e.g.
`-a/--auto-dir` to create sub-directory based on parameter names and values).
The command is executed in the background  and the standard output is
saved to log files. 

There are a number of other ways to communicate parameter values to your model
(see also `--arg-prefix` parameter, e.g. with `--arg-prefix "--{} "` to achieve
the same result with less redundancy, when parameter names match). Parameters
can also be passed via a file:

    job run -p a=2,3,4 b=0,1 -o out --file-name params.txt --file-type linesep --line-sep " "

    cat out/*/params.txt

    a 2
    b 0
    a 2
    b 1
    a 3
    b 0
    a 3
    b 1
    a 4
    b 0
    a 4
    b 1

with a number of other file types. File types that involve grouping, such as
namelist, require a group prefix with a `.` separator in the parameter name:

    job run -p g1.a=0,1 g2.b=2. -o out --file-name params.txt --file-type namelist

    cat out/*/params.txt

    &g1
     a               = 0          
    /
    &g2
     b               = 2.0        
    /
    &g1
     a               = 1          
    /
    &g2
     b               = 2.0        
    /

Additionally, parameters can be set as environment variables via `--env-prefix`
argument (e.g. `--env-prefix ""` for direct access via `$NAME` within the
script).


Custom model interface
----------------------
For more complex model setup you may subclass `runner.model.ModelInterface` methods
`setup` and `postprocess`. See [examples/custom.py](examples/custom.py) how to do that.


Note for use on the cluster
---------------------------
The current version makes use of python's multiprocessing.Pool to handle parallel
tasks. When running on the cluster, it is up to the user to allocate ressources, via
sbatch, e.g. by simply writing the command in a bash script:

    
    # write job script
    echo job run -p a=2,3,4 b=0,1 -o out -- echo --a {a} --b {b} --out {} > jobrun.sh

    # submit with slurm with 10 procs
    sbatch -n 10 jobrun.sh
