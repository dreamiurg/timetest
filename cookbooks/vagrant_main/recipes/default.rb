include_recipe "apt"
include_recipe "apache2::mod_wsgi"
include_recipe "python"
include_recipe "mysql::server"
include_recipe "git"

execute "disable-default-site" do
  command "sudo a2dissite default"
  notifies :restart, resources(:service => "apache2")
end
