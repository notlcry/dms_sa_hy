require_relative  'types_loader'
require_relative  'zk_client'
module DmsVmomi
class Connection
	attr_reader :client
	def initialize opts
		schema = opts[:type]  or  fail "no connect type specified" 
		if schema == "zookeeper"
			client = ZookeeperConnection.new opts
	    else
	     	fail "the type: %s is unavailable"
	    end
	end
    def self.extension_dirs
      @extension_dirs ||= []
    end

	def self.add_extension_dir dir 
		extension_dirs <<  dir 
		@loader.reload_extensions_dir dir if @loader
	end

	def self.reload_extension
		@loader.reload_extension
	end

	def self.loader;@loader;end

	def self.load_vmodl fn
		@loader = DmsVmomi::TypeLoader.new fn,extension_dirs,self
		nil
	end
end
end