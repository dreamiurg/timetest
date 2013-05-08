Vagrant::Config.run do |config|
  config.vm.box = "lucid32"

  # Enable and configure the chef solo provisioner
  config.vm.provision :chef_solo do |chef|
    chef.json.merge!({
      :mysql => {
        :server_root_password => "root",
        :server_debian_password => "root",
        :server_repl_password => "root"
      }
    })
    
    chef.add_recipe("vagrant_main")
  end
  
  # forward 80 so we can connect to apache from host os
  config.vm.forward_port 80, 8080
  # forwardgin mysql is not required, but convenient for mysql admin tools on host os
  config.vm.forward_port 3306, 8806
end
