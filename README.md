### Installation

Installer les dépendances

    sudo apt-get update
    sudo apt-get install -y htop wget curl python-setuptools python-pip avahi-daemon i2c-tools python-smbus vim nginx

Puis les modules python nécessaires :

    sudo pip install bottle wifi smbus
    easy_install twython

Changer le nom d'hôte et étendre le file system avec :

    sudo raspi-config

> Nous utilisons le nom d'hôte `totem1` par la suite

### Configuration

Dans le fichier suivant :

    sudo nano /etc/modprobe.d/raspi-blacklist.conf

Commenter le module i2c :

    # blacklist spi and i2c by default (many users don't need them)
    blacklist spi-bcm2708
    #blacklist i2c-bcm2708

Et dans le fichier de modules :

    sudo nano /etc/modules

Ajouter le module i2c :

    snd-bcm2835
    i2c-dev

Puis :

    sudo adduser pi i2c

Ajouter une configuration de proxy à nginx :


    sudo vi /etc/nginx/available/totem.conf

Avec :

    server {
      server_name totem1.local totem1;
      rewrite ^/(.*)$ http://totem1:8080/$1 permanent;
    }

puis :

    cd /etc/nginx/enabled && ln -s ../available/totem.conf .
    sudo service nginx restart

Pour lancer `avahi` au démarrage :

    sudo update-rc.d avahi-daemon defaults

Puis :

    sudo insserv avahi-daemon

Éditer le fichier de service :

    sudo pico /etc/avahi/services/multiple.service

Avec ce contenu :

```xml
<?xml version="1.0" standalone='no'?>
<!DOCTYPE service-group SYSTEM "avahi-service.dtd">
<service-group>
        <name replace-wildcards="yes">%h</name>
        <service>
                <type>_device-info._tcp</type>
                <port>0</port>
                <txt-record>model=TOTEM</txt-record>
        </service>
        <service>
                <type>_ssh._tcp</type>
                <port>22</port>
        </service>
</service-group>
```

Et enfin :

    sudo /etc/init.d/avahi-daemon restart

Et finalement, redémarrez (`sudo reboot`)

### Créer un script de démarrage

Avec :

    sudo vi /etc/init.d/totem


```bash
#! /bin/sh

case "$1" in
  start)
    echo "Starting totem .."
    cd /home/pi/firmware/ && sudo python totem.py
    ;;
  stop)
    echo "Stopping totem .."
    sudo pkill -f "totem"
    ;;
  *)
    echo "Usage: /etc/init.d/totem {start|stop}"
    exit 1
    ;;
esac

exit 0
```

Puis 

    sudo update-rc.d totem defaults


### Accès à l'interface

Sur le même réseau wifi, aller sur http://totem1.local ou http://totem1


