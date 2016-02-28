class DmsVmomi::VIM::VM < Base
	attr_reader :id
	attr_accessor :manage_ip
	attr_accessor :public_ip
	attr_accessor :service_ip
	def initialize(stackid,conn)
		super :conn
		id = stackid
	end