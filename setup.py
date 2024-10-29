from setuptools import setup
import versioneer

setup(name='runner',
      version=versioneer.get_version(),
      cmdclass=versioneer.get_cmdclass(),
      author='Mahe Perrette, Alexander Robinson',
      author_email='mahe.perrette@pik-potsdam.de',
      packages = ['runner', 'runner.lib', 'runner.ext', 'runner.tools', 'runner.job'],
      install_requires = ['numpy', 'pandas', 'scipy', 'six', 'tox','tabulate'],
      scripts = ['scripts/job','scripts/jobrun'], 
      )
