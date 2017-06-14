from invoke import task
from paramiko import SSHClient, AutoAddPolicy
from scp import SCPClient
import os

@task
def init(ctx):
    if not os.path.isfile('./cruise-config.xml'):
        ctx.run("curl -s -o cruise-config.xml http://$SWARM_HOST:8153/go/admin/restful/configuration/file/GET/xml", pty=True)
    else:
        print('cruise-config.xml already exists')

@task
def update(ctx):
    config_dir = '/mnt/data/go/godata/config'
    plugin_dir = '/mnt/data/go/godata/plugins/external'
    ssh = SSHClient()
    ssh.set_missing_host_key_policy(AutoAddPolicy())
    ssh.connect(os.environ['SWARM_HOST'], username='ubuntu', key_filename='./bootstrap.pem')

    # deploy plugins and config
    with SCPClient(ssh.get_transport()) as scp:
         scp.put('cruise-config.xml', config_dir + '/cruise-config.xml')
         scp.put('password.properties', config_dir + '/password.properties')
         if not set(ssh.open_sftp().listdir('/mnt/data/go/godata/plugins/external'))==set(os.listdir('plugins')):
            ssh.exec_command("sudo rm -r {}/*".format(plugin_dir))
            for item in os.listdir('plugins'):
                scp.put(os.path.join('plugins', item), os.path.join(plugin_dir + '/', item))

            cmd="sudo docker kill $(sudo docker ps | grep \'{}\' | awk \'{{print $1}}\')".format(os.environ['GOCDSERVER_IMAGE'])
            # print(cmd)
            ssh.exec_command(cmd)
            ssh.exec_command("sudo docker kill $GOID")
