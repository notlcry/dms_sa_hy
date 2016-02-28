class DmsVmomi::Service < Base
	attr_reader :name
	def initialize(svcname,connnect)
		super connect
		name = svcname
	end
end