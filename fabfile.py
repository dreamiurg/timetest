"""
This fabric file simplifies set up and deployment of your django project
to vagrant-managed virtual box. It makes few assumptions about your
django project though:

    - It uses MySQL
    - It uses South to manage DB migrations

Thanks to:

    http://github.com/ryanmark/django-project-templates
    http://github.com/garethr/django-project-templates

This fabfile.py expects the following local project dir stucture:
   
    <project_name>
        fabfile.py                  - this file
        requirements.txt            - python package requirements for pip
        apache/
            config.wsgi.template    - mod_wsgi configuration template
            vagrant.conf.template   - httpd.conf to be used on vagrant-managed server
            ...
        cookbooks/                  - contains chef cookbooks
        sql/
            createdb.sql.template   - executed by create_database() command
            dropdb.sql.template     - executed by drop_database() command
        <project_name>/             - your django project
            __init__.py
            settings.py
            urls.py
            ...

"""

from __future__ import with_statement
from fabric.api import local, settings, abort, run, cd, env, sudo
from fabric.colors import green as _green
from fabric.colors import yellow as _yellow
from fabric.colors import red as _red
from fabric.contrib.console import confirm
from fabric.contrib.project import rsync_project
from fabric.contrib.files import upload_template, exists
from fabric.operations import require
from fabric.context_managers import prefix
import os.path
import inspect
import sys

# -----------------------------------------------------------------------------
# Globals
# -----------------------------------------------------------------------------

env.project_name = 'timetest'
    
def _set_vagrant_env():
    env.python = 'python2.6'

    env.path = '/home/vagrant/www'
    env.repo_path = '/vagrant'
    env.env_path  = os.path.join(env.path, 'env')
    env.code_path = os.path.join(env.repo_path, env.project_name)

    env.cmd_apache_start = 'sudo /usr/sbin/apache2ctl start'
    env.cmd_apache_stop = 'sudo /usr/sbin/apache2ctl stop'
    env.cmd_apache_restart = 'sudo /usr/sbin/apache2ctl restart'
    
    env.mysql_admin_user = 'root'
    env.mysql_admin_pass = 'root'
    
    try:
        sys.path.insert(0, env.project_name)
        from config.vagrant import DATABASES
        env.mysql_dbname = DATABASES['default']['NAME']
        env.mysql_user = DATABASES['default']['USER']
        env.mysql_pass = DATABASES['default']['PASSWORD']
        
    except ImportError:
        print(_red('... Unable to get database configuration from Django project, falling back to defaults'))
        env.mysql_dbname = env.project_name
        env.mysql_user = env.project_name
        env.mysql_pass = env.project_name
    

# -----------------------------------------------------------------------------
# Environments
# -----------------------------------------------------------------------------

def vagrant():
    """
    Select vagrant-managed VM for commands
    """
    env.settings = 'vagrant'
    
    # get vagrant ssh setup
    vagrant_config = _get_vagrant_config()
    env.key_filename = vagrant_config['IdentityFile']
    env.hosts = ['%s:%s' % (vagrant_config['HostName'], vagrant_config['Port'])]
    env.user = vagrant_config['User']
    
    _set_vagrant_env()
    
# -----------------------------------------------------------------------------
# Main commands
# -----------------------------------------------------------------------------

def setup():
    """
    Setup a fresh virtualenv, install everything we need, and fire up the database.
    """
    require('settings', provided_by=[vagrant])
    
    mkdirs()
    setup_virtualenv()
    install_requirements()
    drop_database();
    create_database()
    populate_database()
    install_apache_conf()
    apache_restart()
    
    
def destroy_world():
    """
    Removes everything
    """
    require('settings', provided_by=[vagrant])
    
    mkdirs() # drop_database files are copied here
    remove_apache_conf()
    apache_restart()
    drop_database()
    rmdirs()
    

    
# -----------------------------------------------------------------------------
# Database operations
# -----------------------------------------------------------------------------

def create_database():
    """
    Create database and db user
    """
    print(_yellow('>>> starting %s()' % _fn()))
    require('settings', provided_by=[vagrant])
    if env.settings != 'vagrant':
        print('... skipping this action for non-vagrant environment')
        return
    
    upload_template('sql/createdb.sql.template', '%(path)s/temp.sql' % env, context=env, use_jinja=True)
    run('mysql -u %(mysql_admin_user)s -p%(mysql_admin_pass)s --batch < %(path)s/temp.sql' % env)
    run('rm -f %(path)s/temp.sql' % env)

    
def drop_database():
    """
    Create database and db user
    """
    print(_yellow('>>> starting %s()' % _fn()))
    require('settings', provided_by=[vagrant])
    if env.settings != 'vagrant':
        print('... skipping this action for non-vagrant environment')
        return
    
    upload_template('sql/dropdb.sql.template', '%(path)s/temp.sql' % env, context=env, use_jinja=True)
    run('mysql -u %(mysql_admin_user)s -p%(mysql_admin_pass)s --batch < %(path)s/temp.sql' % env)
    run('rm -f %(path)s/temp.sql' % env)

        
def populate_database():
    """
    Create initial database scheme and load initial data
    """
    print(_yellow('>>> starting %s()' % _fn()))
    require('settings', provided_by=[vagrant])
    
    virtualenv('FLAVOR=%(settings)s %(python)s %(code_path)s/manage.py syncdb --noinput' % env)
    virtualenv('FLAVOR=%(settings)s %(python)s %(code_path)s/manage.py loaddata %(repo_path)s/sql/init.json' % env)


def migrate():
    """
    Migrate database scheme and data
    """
    print(_yellow('>>> starting %s()' % _fn()))
    require('settings', provided_by=[vagrant])

    virtualenv('FLAVOR=%(settings)s %(python)s %(code_path)s/manage.py migrate common' % env)

# -----------------------------------------------------------------------------
# Helpers
# -----------------------------------------------------------------------------

def dummy():
    """
    Dummy task for testing
    """
    print(_yellow('>>> starting %s()' % _fn()))
    require('settings', provided_by=[vagrant])
    run('uname -a && hostname && pwd')


def wsgi_restart():
    """
    Gently restarts mod_wsgi by touching it's config
    """
    print(_yellow('>>> starting %s()' % _fn()))
    require('settings', provided_by=[vagrant])
    
    if env.settings == 'vagrant':
      run('touch /etc/apache2/sites-available/%(project_name)s.wsgi' % env)

def apache_restart():
    """
    Restarts apache
    """
    print(_yellow('>>> starting %s()' % _fn()))
    require('settings', provided_by=[vagrant])
    
    run(env.cmd_apache_restart)


def apache_start():
    """
    Starts apache
    """
    print(_yellow('>>> starting %s()' % _fn()))
    require('settings', provided_by=[vagrant])

    run(env.cmd_apache_start)
    

def apache_stop():
    """
    Stops apache
    """
    print(_yellow('>>> starting %s()' % _fn()))
    require('settings', provided_by=[vagrant])

    run(env.cmd_apache_start)

    
def setup_virtualenv():
    """
    Setup a fresh virtualenv.
    """
    print(_yellow('>>> starting %s()' % _fn()))
    run('virtualenv -p %(python)s --no-site-packages %(env_path)s' % env)
    virtualenv('easy_install -U setuptools')
    virtualenv('easy_install pip')


def virtualenv(command):
    """
    Run command in virtualenv.
    """
    with prefix('source %(env_path)s/bin/activate' % env):
        run(command)
        
        
def install_requirements():
    """
    Install the required packages using pip.
    """
    print(_yellow('>>> starting %s()' % _fn()))
    virtualenv('pip install -q -E %(env_path)s -r %(repo_path)s/requirements.txt' % env)


def install_apache_conf():
    """
    Backup old httpd.conf and install new one.
    """
    print(_yellow('>>> starting %s()' % _fn()))
    require('settings', provided_by=[vagrant])
    
    if env.settings == 'vagrant':
        upload_template('apache/vagrant.conf.template', '/etc/apache2/sites-available/%(project_name)s' % env,
                        context=env, use_jinja=True, use_sudo=True)

        upload_template('apache/config.wsgi.template', '/etc/apache2/sites-available/%(project_name)s.wsgi' % env,
                        context=env, use_jinja=True, use_sudo=True)
    
        sudo('a2ensite %(project_name)s' % env)
        
    else:
        # write your own code for other environments,
        # like shared hosting
        pass
    
    
def remove_apache_conf():
    """
    Removes apache conf. Vagrant-only version for now
    """
    print(_yellow('>>> starting %s()' % _fn()))
    require('settings', provided_by=[vagrant])
    if env.settings != 'vagrant':
        return
    
    sudo('a2dissite %(project_name)s' % env)


def maintenance_on():
    """
    Turn maintenance mode on.
    """
    print(_yellow('>>> starting %s()' % _fn()))
    require('settings', provided_by=[vagrant])
    run('touch %(repo_path)s/.upgrading' % env)

    
def maintenance_off():
    """
    Turn maintenance mode off.
    """
    print(_yellow('>>> starting %s()' % _fn()))
    require('settings', provided_by=[vagrant])
    run('rm -f %(repo_path)s/.upgrading' % env)

    
def mkdirs():
    """
    Create all directories required for project
    """
    print(_yellow('>>> starting %s()' % _fn()))
    require('settings', provided_by=[vagrant])
    
    run('mkdir -p %(path)s' % env)


def rmdirs():
    """
    Removes all directories. Vagrant-only version for now
    """
    print(_yellow('>>> starting %s()' % _fn()))
    require('settings', provided_by=[vagrant])
    if env.settings != 'vagrant':
        return
    
    run('rm -rf %(path)s' % env)
    
# -----------------------------------------------------------------------------
# Functions not to be run directly
# -----------------------------------------------------------------------------
def _fn():
    """
    Returns current function name
    """
    return inspect.stack()[1][3]

def _get_vagrant_config():
    """
    Parses vagrant configuration and returns it as dict of ssh parameters
    and their values
    """
    result = local('vagrant ssh_config', capture=True)
    conf = {}
    for line in iter(result.splitlines()):
        parts = line.split()
        conf[parts[0]] = ' '.join(parts[1:])

    return conf
