class DmsVmomi::VIM::Account < Base
  attr_reader :id
  attr_accessor :name
  def initialize(accountid,accountname,connect)
  	super connect
  	id = accountid
  	name = accountname
  end
end