class DmsVmomi::VIM::Base
	attr_reader :conn
	def initialize(connect)
		conn = connect
	end
end

