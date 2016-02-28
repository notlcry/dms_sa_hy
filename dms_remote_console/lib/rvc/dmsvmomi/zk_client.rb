module DmsVmomi

require 'zookeeper'
class  ZookeeperConnection
	attr_reader :zk
	def initialize opts
		@host = opts[:host] or fail "no host url specified"
		@port = opts[:port] or fail "no port specified"
		zk = Zookeeper.new("#{@host}:#{@port}")
	end

	
end

end