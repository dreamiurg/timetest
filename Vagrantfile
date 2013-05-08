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
  
  # forward ports
  config.vm.forward_port 80, 8080
  config.vm.forward_port 3306, 8806
end
