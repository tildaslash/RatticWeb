# -*- mode: ruby -*-
# vi: set ft=ruby :

Vagrant.configure("2") do |config|
  # All Vagrant configuration is done here. The most common configuration
  # options are documented and commented below. For a complete reference,
  # please see the online documentation at vagrantup.com.

  # Every Vagrant virtual environment requires a box to build off of.
  config.vm.box = "centos_6.3_extra_vg_space"

  # The url from where the 'config.vm.box' box will be fetched if it
  # doesn't already exist on the user's system.
  config.vm.box_url = "http://rattic.org/vagrant/centos_6.3_extra_vg_space.box"

  config.vm.define "rattic" do |web|
    config.vm.network :forwarded_port, host: 8080, guest: 80
    config.vm.network :forwarded_port, host: 8443, guest: 443
    config.vm.provision :ansible do |ansible|
      ansible.playbook = "docs/ansible/rattic.play"
      ansible.extra_vars = { release: "vagrant" }
      ansible.sudo = true
      ansible.host_key_checking = false
    end
  end

end
