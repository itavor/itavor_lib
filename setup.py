from distutils.core import setup
import os

# Compile the list of packages available, because distutils doesn't have
# an easy way to do this.
packages, data_files = [], []
root_dir = os.path.dirname(__file__)
if root_dir:
    os.chdir(root_dir)

for dirpath, dirnames, filenames in os.walk('itavor_lib'):
    # Ignore dirnames that start with '.'
    for i, dirname in enumerate(dirnames):
        if dirname.startswith('.'): del dirnames[i]
    if '__init__.py' in filenames:
        pkg = dirpath.replace(os.path.sep, '.')
        if os.path.altsep:
            pkg = pkg.replace(os.path.altsep, '.')
        packages.append(pkg)
    elif filenames:
        prefix = dirpath[13:] # Strip "itavor_lib/" or "itavor_lib\"
        for f in filenames:
            data_files.append(os.path.join(prefix, f))

setup(name='django-video-assets',
      version='0.19',
      description='A django app adding video media handling capabilities to websites',
      author='Itai Tavor',
      author_email='itai@tavor.net',
      url='http://github.com/itavor/itavor-lib/',
      package_dir={'itavor_lib': 'itavor_lib'},
      packages=packages,
      package_data={'itavor_lib': data_files},
      classifiers=['Development Status :: 4 - Beta',
                   'Environment :: Web Environment',
                   'Intended Audience :: Developers',
                   'License :: OSI Approved :: BSD License',
                   'Operating System :: OS Independent',
                   'Programming Language :: Python',
                   'Topic :: Utilities'],
      )