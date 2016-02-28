require_relative 'base'

module DmsVmomi::VIM
class Folder < Base
	attr_reader :arc
	attr_accessor :parent
	attr_accessor :children
	def initialize name,conn
		super conn
		arc = name
	end
end

class AccountFolder < Folder
	def initialize(conn)
		super "accounts",conn
	end
end

class ServiceFolder < Folder
	def initialize(conn)
		super "service",conn
	end
end

class RootFolder < Folder
	def initialize(conn)
		super "dso",conn
	end
end

end